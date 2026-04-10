"""数据抓取器包."""

from quantpilot.data.fetchers.akshare_fetcher import AKShareFetcher
from quantpilot.data.fetchers.base import BaseDataFetcher
from quantpilot.data.fetchers.yfinance_fetcher import YFinanceFetcher

__all__ = ["BaseDataFetcher", "YFinanceFetcher", "AKShareFetcher"]
