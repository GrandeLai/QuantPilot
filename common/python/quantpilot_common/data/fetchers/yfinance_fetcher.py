"""Yahoo Finance 数据抓取器.

支持全球股票、ETF、指数、外汇、加密货币的历史 K 线数据获取。
"""

from datetime import UTC, date, datetime

import pandas as pd
import yfinance as yf
from loguru import logger

from quantpilot_common.data.fetchers.base import BaseDataFetcher
from quantpilot_common.data.models import AssetType, Exchange, OHLCVBar, SymbolInfo

# Yahoo Finance 周期映射
_TF_MAP: dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1wk",
    "1M": "1mo",
}


class YFinanceFetcher(BaseDataFetcher):
    """Yahoo Finance 数据源适配器."""

    @property
    def source_name(self) -> str:
        return "yfinance"

    def _timeframe_to_source(self, timeframe: str) -> str:
        if timeframe not in _TF_MAP:
            msg = f"Yahoo Finance 不支持 timeframe: {timeframe}"
            raise ValueError(msg)
        return _TF_MAP[timeframe]

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: date,
        end: date | None = None,
    ) -> list[OHLCVBar]:
        """从 Yahoo Finance 抓取 K 线数据.

        Args:
            symbol: Yahoo Finance 代码（如 AAPL、BTC-USD、^GSPC）
            timeframe: K 线周期
            start: 开始日期
            end: 结束日期（None 表示今天）

        Returns:
            OHLCVBar 列表，按时间升序排列
        """
        yf_interval = self._timeframe_to_source(timeframe)
        end_date = end or date.today()

        logger.info(
            f"[YFinance] 抓取 {symbol} {timeframe} "
            f"{start.isoformat()} ~ {end_date.isoformat()}"
        )

        try:
            ticker = yf.Ticker(symbol)
            df: pd.DataFrame = ticker.history(
                start=start.isoformat(),
                end=end_date.isoformat(),
                interval=yf_interval,
                auto_adjust=True,
                actions=False,
            )
        except Exception as e:
            logger.error(f"[YFinance] 抓取失败 {symbol}: {e}")
            raise

        if df.empty:
            logger.warning(f"[YFinance] {symbol} 无数据返回")
            return []

        bars: list[OHLCVBar] = []
        for ts, row in df.iterrows():
            # 统一转为 UTC datetime
            if isinstance(ts, pd.Timestamp):
                if ts.tzinfo is None:
                    ts = ts.tz_localize("UTC")
                dt = ts.to_pydatetime()
            else:
                dt = datetime.fromtimestamp(float(str(ts)), tz=UTC)

            bars.append(
                OHLCVBar(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=dt,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0)),
                )
            )

        logger.info(f"[YFinance] {symbol} 抓取完成，共 {len(bars)} 条")
        return bars

    def search_symbols(self, query: str) -> list[SymbolInfo]:
        """搜索标的（Yahoo Finance 不直接提供搜索 API，返回空列表）."""
        logger.warning("[YFinance] search_symbols 暂不支持，请直接指定代码")
        return []

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """获取标的基础信息."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info:
                return None

            return SymbolInfo(
                symbol=symbol,
                name=info.get("longName") or info.get("shortName") or symbol,
                exchange=Exchange.UNKNOWN,
                asset_type=self._guess_asset_type(info),
                currency=info.get("currency", "USD"),
            )
        except Exception as e:
            logger.error(f"[YFinance] 获取 {symbol} 信息失败: {e}")
            return None

    @staticmethod
    def _guess_asset_type(info: dict[str, object]) -> AssetType:
        """根据 yfinance info 猜测资产类型."""
        quote_type = str(info.get("quoteType", "")).upper()
        mapping = {
            "EQUITY": AssetType.STOCK,
            "ETF": AssetType.ETF,
            "FUTURE": AssetType.FUTURE,
            "OPTION": AssetType.OPTION,
            "CRYPTOCURRENCY": AssetType.CRYPTO,
            "CURRENCY": AssetType.FOREX,
            "BOND": AssetType.BOND,
        }
        return mapping.get(quote_type, AssetType.STOCK)
