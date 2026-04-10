"""AKShare 数据抓取器.

支持 A 股、港股、期货、基金等国内市场数据获取。
"""

from datetime import UTC, date, datetime

import akshare as ak
import pandas as pd
from loguru import logger

from quantpilot.data.fetchers.base import BaseDataFetcher
from quantpilot.data.models import AssetType, Exchange, OHLCVBar, SymbolInfo

# AKShare 周期映射（stock_zh_a_hist 接口）
_TF_MAP_A_STOCK: dict[str, str] = {
    "1d": "daily",
    "1w": "weekly",
    "1M": "monthly",
}

# AKShare 分钟周期（stock_zh_a_hist_min_em 接口）
_TF_MAP_A_STOCK_MIN: dict[str, str] = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
}


class AKShareFetcher(BaseDataFetcher):
    """AKShare 数据源适配器，主要用于 A 股、港股市场."""

    @property
    def source_name(self) -> str:
        return "akshare"

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: date,
        end: date | None = None,
    ) -> list[OHLCVBar]:
        """从 AKShare 抓取 K 线数据.

        Args:
            symbol: A 股代码（如 '000001' 平安银行，'600519' 茅台）
            timeframe: K 线周期
            start: 开始日期
            end: 结束日期
        """
        end_date = end or date.today()

        logger.info(
            f"[AKShare] 抓取 {symbol} {timeframe} "
            f"{start.isoformat()} ~ {end_date.isoformat()}"
        )

        try:
            if timeframe in _TF_MAP_A_STOCK_MIN:
                return self._fetch_minute_bars(symbol, timeframe, start, end_date)
            elif timeframe in _TF_MAP_A_STOCK:
                return self._fetch_daily_bars(symbol, timeframe, start, end_date)
            else:
                msg = f"AKShare 不支持 timeframe: {timeframe}"
                raise ValueError(msg)
        except Exception as e:
            logger.error(f"[AKShare] 抓取失败 {symbol}: {e}")
            raise

    def _fetch_daily_bars(
        self, symbol: str, timeframe: str, start: date, end: date
    ) -> list[OHLCVBar]:
        """抓取日线/周线/月线数据."""
        period = _TF_MAP_A_STOCK[timeframe]
        df: pd.DataFrame = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="qfq",  # 前复权
        )

        if df.empty:
            return []

        bars: list[OHLCVBar] = []
        for _, row in df.iterrows():
            dt = datetime.strptime(str(row["日期"]), "%Y-%m-%d").replace(
                tzinfo=UTC
            )
            bars.append(
                OHLCVBar(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=dt,
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"]),
                    turnover=float(row.get("成交额", 0) or 0),
                )
            )

        logger.info(f"[AKShare] {symbol} 日线抓取完成，共 {len(bars)} 条")
        return bars

    def _fetch_minute_bars(
        self, symbol: str, timeframe: str, start: date, end: date
    ) -> list[OHLCVBar]:
        """抓取分钟线数据."""
        period = _TF_MAP_A_STOCK_MIN[timeframe]
        df: pd.DataFrame = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            start_date=start.strftime("%Y-%m-%d %H:%M:%S"),
            end_date=end.strftime("%Y-%m-%d 15:00:00"),
            period=period,
            adjust="qfq",
        )

        if df.empty:
            return []

        bars: list[OHLCVBar] = []
        for _, row in df.iterrows():
            dt = datetime.strptime(str(row["时间"]), "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=UTC
            )
            bars.append(
                OHLCVBar(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=dt,
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"]),
                    turnover=float(row.get("成交额", 0) or 0),
                )
            )

        logger.info(f"[AKShare] {symbol} 分钟线抓取完成，共 {len(bars)} 条")
        return bars

    def search_symbols(self, query: str) -> list[SymbolInfo]:
        """搜索 A 股标的."""
        try:
            df: pd.DataFrame = ak.stock_zh_a_spot_em()
            mask = df["代码"].str.contains(query, na=False) | df["名称"].str.contains(
                query, na=False
            )
            filtered = df[mask].head(20)

            return [
                SymbolInfo(
                    symbol=str(row["代码"]),
                    name=str(row["名称"]),
                    exchange=Exchange.SSE if str(row["代码"]).startswith("6") else Exchange.SZSE,
                    asset_type=AssetType.STOCK,
                    currency="CNY",
                )
                for _, row in filtered.iterrows()
            ]
        except Exception as e:
            logger.error(f"[AKShare] 搜索失败: {e}")
            return []
