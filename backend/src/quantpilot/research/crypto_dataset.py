"""OKX 多时间维度加密研究数据集构建器."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quantpilot.data.storage import MarketDataStorage


@dataclass(slots=True)
class MultiTimeframeDataset:
    """统一后的多周期研究数据集."""

    symbol: str
    base_timeframe: str
    higher_timeframes: list[str]
    frame: pd.DataFrame
    rows: int
    data_version: str


class MultiTimeframeDatasetBuilder:
    """从本地行情仓库构建多周期对齐数据集."""

    def __init__(self, storage: MarketDataStorage) -> None:
        self._storage = storage

    def build(
        self,
        *,
        symbol: str,
        base_timeframe: str,
        higher_timeframes: list[str],
        limit: int = 500,
    ) -> MultiTimeframeDataset:
        """构建以 base_timeframe 为主时间轴的多周期研究数据集."""
        base_df = self._query_frame(symbol=symbol, timeframe=base_timeframe, limit=limit)
        if base_df.empty:
            return MultiTimeframeDataset(
                symbol=symbol,
                base_timeframe=base_timeframe,
                higher_timeframes=higher_timeframes,
                frame=pd.DataFrame(),
                rows=0,
                data_version=f"{symbol}:{base_timeframe}:empty",
            )

        base_frame = self._rename_frame(base_df, suffix=base_timeframe, keep_main_timestamp=True)
        merged = base_frame.copy()

        for timeframe in higher_timeframes:
            higher_df = self._query_frame(symbol=symbol, timeframe=timeframe, limit=limit)
            if higher_df.empty:
                continue
            higher_frame = self._rename_frame(higher_df, suffix=timeframe, keep_main_timestamp=False)
            merged = pd.merge_asof(
                merged.sort_values("timestamp"),
                higher_frame.sort_values(f"timestamp_{timeframe}"),
                left_on="timestamp",
                right_on=f"timestamp_{timeframe}",
                direction="backward",
            )

        merged = merged.set_index("timestamp").sort_index()
        merged = merged.ffill()
        data_version = f"{symbol}:{base_timeframe}:{merged.index.min().isoformat()}:{merged.index.max().isoformat()}"
        return MultiTimeframeDataset(
            symbol=symbol,
            base_timeframe=base_timeframe,
            higher_timeframes=higher_timeframes,
            frame=merged,
            rows=len(merged),
            data_version=data_version,
        )

    def _query_frame(self, *, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        frame = self._storage.query_bars(symbol=symbol, timeframe=timeframe, limit=limit).to_pandas()
        if frame.empty:
            return frame
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        return frame.sort_values("timestamp").reset_index(drop=True)

    def _rename_frame(
        self,
        frame: pd.DataFrame,
        *,
        suffix: str,
        keep_main_timestamp: bool,
    ) -> pd.DataFrame:
        renamed = frame.rename(
            columns={
                "open": f"open_{suffix}",
                "high": f"high_{suffix}",
                "low": f"low_{suffix}",
                "close": f"close_{suffix}",
                "volume": f"volume_{suffix}",
                "turnover": f"turnover_{suffix}",
            }
        )
        if keep_main_timestamp:
            return renamed
        return renamed.rename(columns={"timestamp": f"timestamp_{suffix}"})
