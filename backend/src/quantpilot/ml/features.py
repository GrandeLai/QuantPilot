"""特征工程 — 从 OHLCV 数据提取 TA 特征."""
from __future__ import annotations

import pandas as pd

from quantpilot.data.models import OHLCVBar


class FeatureEngineer:
    """从 OHLCV K 线列表计算机器学习特征."""

    def compute(self, bars: list[OHLCVBar]) -> pd.DataFrame:
        """计算特征 DataFrame.

        Args:
            bars: OHLCV K 线列表（按时间升序）

        Returns:
            包含特征列的 DataFrame（已删除 NaN 行）
        """
        if len(bars) < 5:
            return pd.DataFrame()

        df = pd.DataFrame([
            {
                "timestamp": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ]).set_index("timestamp")

        # 价格特征
        df["returns"] = df["close"].pct_change()
        df["log_returns"] = df["returns"]  # simplified approximation

        # 动量特征
        df["momentum"] = df["close"].pct_change(periods=5)
        df["momentum_10"] = df["close"].pct_change(periods=10)

        # 波动率特征
        df["volatility"] = df["returns"].rolling(window=10).std()
        df["volatility_20"] = df["returns"].rolling(window=20).std()

        # 移动平均
        df["ma5"] = df["close"].rolling(window=5).mean()
        df["ma10"] = df["close"].rolling(window=10).mean()
        df["ma20"] = df["close"].rolling(window=20).mean()
        df["ma5_ratio"] = df["close"] / df["ma5"]
        df["ma20_ratio"] = df["close"] / df["ma20"]

        # 成交量特征
        df["volume_ma10"] = df["volume"].rolling(window=10).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma10"]

        # 价格区间
        df["hl_ratio"] = (df["high"] - df["low"]) / df["close"]
        df["oc_ratio"] = (df["close"] - df["open"]) / df["open"]

        # 目标变量：未来1期收益方向 (1=涨, -1=跌, 0=持平)
        future_ret = df["returns"].shift(-1)
        df["target"] = future_ret.apply(
            lambda r: 1 if r > 0.001 else (-1 if r < -0.001 else 0)
        )

        df.dropna(inplace=True)
        return df
