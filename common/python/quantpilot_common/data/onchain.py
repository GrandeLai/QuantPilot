"""链上数据提供者 — BTC/ETH 链上指标（blockchain.info 公共 API）."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel

BLOCKCHAIN_INFO_URL = "https://api.blockchain.info/stats"

METRIC_LABELS: dict[str, str] = {
    "market_price_usd": "BTC 市价 (USD)",
    "hash_rate": "算力 (GH/s)",
    "total_fees_btc": "24h 交易费 (BTC)",
    "n_tx": "24h 交易笔数",
    "estimated_transaction_volume_usd": "24h 链上交易量 (USD)",
    "miners_revenue_usd": "矿工收入 (USD)",
    "difficulty": "挖矿难度",
}


class OnChainMetric(BaseModel):
    """链上指标数据点."""

    metric: str
    label: str = ""
    value: float
    source: str = "blockchain.info"
    asset: str = "BTC"
    fetched_at: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.label:
            self.label = METRIC_LABELS.get(self.metric, self.metric)
        if not self.fetched_at:
            self.fetched_at = datetime.now(UTC).isoformat()


class OnChainProvider:
    """从 blockchain.info 获取 BTC 链上指标."""

    async def _fetch_raw(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(BLOCKCHAIN_INFO_URL)
            resp.raise_for_status()
            return dict(resp.json())

    async def fetch_btc_stats(self) -> list[OnChainMetric]:
        """获取所有已知 BTC 链上指标."""
        try:
            raw = await self._fetch_raw()
            metrics = []
            for key in METRIC_LABELS:
                if key in raw:
                    val = raw[key]
                    if isinstance(val, (int, float)):
                        metrics.append(OnChainMetric(metric=key, value=float(val)))
            logger.info(f"[OnChain] fetched {len(metrics)} BTC metrics")
            return metrics
        except Exception as e:
            logger.error(f"[OnChain] fetch failed: {e}")
            return []

    async def fetch_metric(self, metric_name: str) -> OnChainMetric | None:
        """获取单个链上指标."""
        try:
            raw = await self._fetch_raw()
            if metric_name not in raw:
                return None
            val = raw[metric_name]
            if not isinstance(val, (int, float)):
                return None
            return OnChainMetric(metric=metric_name, value=float(val))
        except Exception as e:
            logger.error(f"[OnChain] fetch_metric({metric_name}) failed: {e}")
            return None
