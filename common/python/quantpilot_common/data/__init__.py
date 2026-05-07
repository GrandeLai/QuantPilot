"""数据层模块 — 行情数据存储、抓取、调度."""

from quantpilot_common.data.models import (
    AssetType,
    DataFetchRequest,
    DataQueryRequest,
    Exchange,
    OHLCVBar,
    OHLCVResponse,
    SymbolInfo,
)
from quantpilot_common.data.storage import MarketDataStorage
from quantpilot_common.data.universe import (
    DEFAULT_MARKET_UNIVERSE,
    SupportedInstrument,
    find_supported_instrument,
    list_supported_instruments,
)

__all__ = [
    "AssetType",
    "Exchange",
    "OHLCVBar",
    "SymbolInfo",
    "DataFetchRequest",
    "DataQueryRequest",
    "OHLCVResponse",
    "MarketDataStorage",
    "SupportedInstrument",
    "DEFAULT_MARKET_UNIVERSE",
    "find_supported_instrument",
    "get_storage",
    "list_supported_instruments",
]


_storage: MarketDataStorage | None = None


def get_storage() -> MarketDataStorage:
    """依赖注入：获取共享 MarketDataStorage 单例（基于 settings.duckdb_path）."""
    global _storage
    if _storage is None:
        from quantpilot_common.config import get_settings
        settings = get_settings()
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        _storage = MarketDataStorage(settings.duckdb_path)
    return _storage
