"""Sector Momentum module — SPDR sector ETF rotation heatmap."""

from quantpilot_stock.sector_momentum.engine import (
    SECTOR_ETFS,
    SectorMomentumData,
    SectorReturn,
    compute_sector_momentum,
)

__all__ = [
    "SECTOR_ETFS",
    "SectorMomentumData",
    "SectorReturn",
    "compute_sector_momentum",
]
