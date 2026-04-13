"""自建核心加密因子 provider."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantpilot.factors.providers.base import BaseFactorProvider


class CoreCryptoFactorProvider(BaseFactorProvider):
    """基于现有依赖自建的核心 OKX 加密因子集合."""

    @property
    def name(self) -> str:
        return "core_crypto"

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(index=frame.index)

        close = frame["close_15m"]
        high = frame["high_15m"]
        low = frame["low_15m"]
        volume = frame["volume_15m"]

        features = pd.DataFrame(index=frame.index)
        returns = close.pct_change()
        features["returns"] = returns
        features["log_returns"] = np.log(close / close.shift(1))
        features["momentum_5"] = close.pct_change(periods=5)
        features["momentum_20"] = close.pct_change(periods=20)
        features["volume_ratio"] = volume / volume.rolling(20, min_periods=20).mean()

        for span in (10, 20, 50):
            features[f"ema_{span}"] = close.ewm(span=span, adjust=False).mean()
        features["ema_spread_10_20"] = features["ema_10"] / features["ema_20"] - 1
        features["ema_spread_20_50"] = features["ema_20"] / features["ema_50"] - 1

        macd = self._macd(close)
        features["macd_line"] = macd["macd_line"]
        features["macd_signal"] = macd["macd_signal"]
        features["macd_hist"] = macd["macd_hist"]

        features["atr_14"] = self._atr(high=high, low=low, close=close, window=14)
        adx_frame = self._adx(high=high, low=low, close=close, window=14)
        features["adx_14"] = adx_frame["adx_14"]
        features["plus_di_14"] = adx_frame["plus_di_14"]
        features["minus_di_14"] = adx_frame["minus_di_14"]
        features["rsi_14"] = self._rsi(close, window=14)

        rolling_mean = close.rolling(20, min_periods=20).mean()
        rolling_std = close.rolling(20, min_periods=20).std()
        features["bb_width_20"] = ((rolling_mean + 2 * rolling_std) - (rolling_mean - 2 * rolling_std)) / rolling_mean
        features["donchian_20"] = high.rolling(20, min_periods=20).max() - low.rolling(20, min_periods=20).min()

        return features

    def _macd(self, close: pd.Series) -> pd.DataFrame:
        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal = macd_line.ewm(span=9, adjust=False).mean()
        return pd.DataFrame(
            {
                "macd_line": macd_line,
                "macd_signal": signal,
                "macd_hist": macd_line - signal,
            },
            index=close.index,
        )

    def _atr(self, *, high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.Series:
        prev_close = close.shift(1)
        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return tr.ewm(alpha=1 / window, adjust=False).mean()

    def _adx(self, *, high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.DataFrame:
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        atr = self._atr(high=high, low=low, close=close, window=window)
        plus_di = 100 * (plus_dm.ewm(alpha=1 / window, adjust=False).mean() / atr.replace(0, np.nan))
        minus_di = 100 * (minus_dm.ewm(alpha=1 / window, adjust=False).mean() / atr.replace(0, np.nan))
        dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
        adx = dx.ewm(alpha=1 / window, adjust=False).mean()
        return pd.DataFrame(
            {
                "adx_14": adx,
                "plus_di_14": plus_di,
                "minus_di_14": minus_di,
            },
            index=close.index,
        )

    def _rsi(self, close: pd.Series, *, window: int) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))
