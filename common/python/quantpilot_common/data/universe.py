"""Shared market universe for QuantPilot products.

This module is the product-neutral contract for which instruments each app can
offer as first-class choices. Stock-assistant owns data fetching and storage;
quant-assistant consumes the same symbols for research computations.
"""

from typing import Literal

from pydantic import BaseModel, Field

from quantpilot_common.data.models import AssetType, Exchange

ProductId = Literal["quant-assistant", "stock-assistant"]
DataSource = Literal["auto", "yfinance", "akshare"]


class SupportedInstrument(BaseModel):
    """Instrument metadata shared by both product frontends and APIs."""

    symbol: str = Field(..., description="Canonical symbol used by QuantPilot APIs.")
    name: str = Field(..., description="Human-readable instrument name.")
    exchange: Exchange = Field(..., description="Primary listing or trading venue.")
    asset_type: AssetType = Field(..., description="Instrument asset type.")
    currency: str = Field(..., description="Quote currency.")
    default_source: DataSource = Field(..., description="Preferred data source.")
    products: list[ProductId] = Field(..., description="Products that should show this instrument.")
    aliases: list[str] = Field(default_factory=list, description="Common user input aliases.")
    description: str = Field(default="", description="Short product-facing explanation.")


_BOTH_PRODUCTS: list[ProductId] = ["quant-assistant", "stock-assistant"]

DEFAULT_MARKET_UNIVERSE: tuple[SupportedInstrument, ...] = (
    SupportedInstrument(
        symbol="AAPL",
        name="Apple Inc.",
        exchange=Exchange.NASDAQ,
        asset_type=AssetType.STOCK,
        currency="USD",
        default_source="yfinance",
        products=_BOTH_PRODUCTS,
        aliases=["APPLE"],
        description="US mega-cap equity for stock decisions and strategy research.",
    ),
    SupportedInstrument(
        symbol="MSFT",
        name="Microsoft Corporation",
        exchange=Exchange.NASDAQ,
        asset_type=AssetType.STOCK,
        currency="USD",
        default_source="yfinance",
        products=_BOTH_PRODUCTS,
        aliases=["MICROSOFT"],
        description="US mega-cap equity.",
    ),
    SupportedInstrument(
        symbol="NVDA",
        name="NVIDIA Corporation",
        exchange=Exchange.NASDAQ,
        asset_type=AssetType.STOCK,
        currency="USD",
        default_source="yfinance",
        products=_BOTH_PRODUCTS,
        aliases=["NVIDIA"],
        description="US semiconductor equity.",
    ),
    SupportedInstrument(
        symbol="SPY",
        name="SPDR S&P 500 ETF Trust",
        exchange=Exchange.NYSE,
        asset_type=AssetType.ETF,
        currency="USD",
        default_source="yfinance",
        products=_BOTH_PRODUCTS,
        aliases=["S&P500", "SP500"],
        description="US broad-market ETF benchmark.",
    ),
    SupportedInstrument(
        symbol="BTC-USDT",
        name="Bitcoin / USDT Spot",
        exchange=Exchange.OKX,
        asset_type=AssetType.CRYPTO,
        currency="USDT",
        default_source="auto",
        products=_BOTH_PRODUCTS,
        aliases=["BTCUSDT", "BTC/USDT", "BTC-USD"],
        description="Crypto spot market pair.",
    ),
    SupportedInstrument(
        symbol="ETH-USDT",
        name="Ethereum / USDT Spot",
        exchange=Exchange.OKX,
        asset_type=AssetType.CRYPTO,
        currency="USDT",
        default_source="auto",
        products=_BOTH_PRODUCTS,
        aliases=["ETHUSDT", "ETH/USDT", "ETH-USD"],
        description="Crypto spot market pair.",
    ),
    SupportedInstrument(
        symbol="SOL-USDT",
        name="Solana / USDT Spot",
        exchange=Exchange.OKX,
        asset_type=AssetType.CRYPTO,
        currency="USDT",
        default_source="auto",
        products=_BOTH_PRODUCTS,
        aliases=["SOLUSDT", "SOL/USDT"],
        description="Crypto spot market pair.",
    ),
    SupportedInstrument(
        symbol="0700.HK",
        name="Tencent Holdings",
        exchange=Exchange.HKEX,
        asset_type=AssetType.STOCK,
        currency="HKD",
        default_source="yfinance",
        products=_BOTH_PRODUCTS,
        aliases=["TENCENT", "700.HK"],
        description="Hong Kong equity example.",
    ),
    SupportedInstrument(
        symbol="600519",
        name="Kweichow Moutai",
        exchange=Exchange.SSE,
        asset_type=AssetType.STOCK,
        currency="CNY",
        default_source="akshare",
        products=_BOTH_PRODUCTS,
        aliases=["贵州茅台"],
        description="A-share equity example.",
    ),
)


def list_supported_instruments(product: ProductId | None = None) -> list[SupportedInstrument]:
    """Return supported instruments, optionally filtered by product."""
    if product is None:
        return list(DEFAULT_MARKET_UNIVERSE)
    return [
        instrument
        for instrument in DEFAULT_MARKET_UNIVERSE
        if product in instrument.products
    ]


def find_supported_instrument(symbol: str) -> SupportedInstrument | None:
    """Find an instrument by canonical symbol or alias."""
    normalized = symbol.strip().upper()
    for instrument in DEFAULT_MARKET_UNIVERSE:
        candidates = {instrument.symbol.upper(), *(alias.upper() for alias in instrument.aliases)}
        if normalized in candidates:
            return instrument
    return None
