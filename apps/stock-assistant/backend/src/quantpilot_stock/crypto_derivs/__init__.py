"""Crypto derivatives — Binance/OKX collectors + basis/funding analytics."""
from quantpilot_stock.crypto_derivs.analytics import (
    compute_basis,
    funding_extreme_signal,
    funding_percentile_stats,
    oi_momentum,
)
from quantpilot_stock.crypto_derivs.collector import (
    fetch_aggregated_derivs,
    fetch_binance_funding,
    fetch_binance_funding_history,
    fetch_binance_open_interest,
    fetch_okx_funding,
    fetch_okx_funding_history,
    fetch_okx_open_interest,
)
from quantpilot_stock.crypto_derivs.models import FundingRate, OpenInterest

__all__ = [
    "FundingRate",
    "OpenInterest",
    "compute_basis",
    "fetch_aggregated_derivs",
    "fetch_binance_funding",
    "fetch_binance_funding_history",
    "fetch_binance_open_interest",
    "fetch_okx_funding",
    "fetch_okx_funding_history",
    "fetch_okx_open_interest",
    "funding_extreme_signal",
    "funding_percentile_stats",
    "oi_momentum",
]
