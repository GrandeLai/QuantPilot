"""OKX 加密货币多周期特征流水线."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantpilot.factors.providers.advanced_crypto import AdvancedCryptoFactorProvider
from quantpilot.factors.providers.core_crypto import CoreCryptoFactorProvider
from quantpilot.factors.providers.pandas_ta_crypto import PandasTaCryptoFactorProvider
from quantpilot.factors.providers.registry import FactorProviderRegistry


class CryptoFeaturePipeline:
    """基于多周期 OHLCV 对齐结果构建研究特征与标签."""

    def __init__(self, provider_registry: FactorProviderRegistry | None = None) -> None:
        self._provider_registry = provider_registry or FactorProviderRegistry(
            providers=[
                CoreCryptoFactorProvider(),
                AdvancedCryptoFactorProvider(),
                PandasTaCryptoFactorProvider(),
            ]
        )

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        """从多周期研究数据集生成特征矩阵."""
        if frame.empty:
            return pd.DataFrame()

        df = frame.copy().sort_index()
        close = df["close_15m"]
        df = pd.concat([df, self._provider_registry.compute(df)], axis=1)

        for timeframe in ("1h", "4h", "1d", "1w"):
            if f"close_{timeframe}" in df.columns:
                df[f"close_{timeframe}_ratio"] = close / df[f"close_{timeframe}"] - 1
                df[f"return_{timeframe}"] = df[f"close_{timeframe}"].pct_change()
                df[f"close_{timeframe}_ratio"] = df[f"close_{timeframe}_ratio"].ffill().fillna(0.0)
                df[f"return_{timeframe}"] = df[f"return_{timeframe}"].ffill().fillna(0.0)

        if "funding_rate" not in df.columns:
            df["funding_rate"] = 0.0
        if "open_interest" not in df.columns:
            df["open_interest"] = 0.0
        df["open_interest_delta"] = df["open_interest"].diff().fillna(0.0)
        if "basis_proxy" not in df.columns:
            df["basis_proxy"] = 0.0

        if "btc_market_price_usd" not in df.columns:
            df["btc_market_price_usd"] = close
        df["btc_market_price_usd"] = df["btc_market_price_usd"].ffill().fillna(close)

        future_1d = df["close_1d"].shift(-1) / df["close_1d"] - 1 if "close_1d" in df.columns else close.shift(-96) / close - 1
        df["forward_return_1d"] = future_1d
        df["target_class"] = future_1d.apply(lambda r: 1 if r > 0.01 else (-1 if r < -0.01 else 0))
        df["target_reversal"] = self._reversal_target(close_1d=df["close_1d"] if "close_1d" in df.columns else close)

        df = df.replace([np.inf, -np.inf], np.nan)
        required_columns = [
            "returns",
            "log_returns",
            "volume_ratio",
            "atr_14",
            "adx_14",
            "plus_di_14",
            "minus_di_14",
            "ema_20",
            "macd_hist",
            "forward_return_1d",
            "target_class",
            "target_reversal",
        ]
        df = df.dropna(subset=required_columns)
        return df

    def _reversal_target(self, *, close_1d: pd.Series) -> pd.Series:
        daily_ret = close_1d.pct_change()
        downward_regime = (daily_ret.shift(2) < 0) & (daily_ret.shift(1) < 0)
        reversal_window = (daily_ret.shift(-1) > 0.01) | (daily_ret.shift(-2) > 0.015)
        return (downward_regime & reversal_window).astype(int)
