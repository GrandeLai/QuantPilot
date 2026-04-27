"""链上数据测试 — T-3.7 验收."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from quantpilot_common.data.onchain import OnChainMetric, OnChainProvider


class TestOnChainMetric:
    def test_has_fields(self) -> None:
        m = OnChainMetric(
            metric="market_price_usd",
            value=65000.0,
            source="blockchain.info",
            asset="BTC",
        )
        assert m.metric == "market_price_usd"
        assert m.value == 65000.0


class TestOnChainProvider:
    async def test_fetch_btc_stats(self) -> None:
        provider = OnChainProvider()
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(
            return_value={
                "market_price_usd": 65000.12,
                "hash_rate": 600_000_000.0,
                "total_fees_btc": 10.5,
                "n_tx": 350000,
                "estimated_transaction_volume_usd": 5_000_000_000.0,
            }
        )
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            metrics = await provider.fetch_btc_stats()
            assert isinstance(metrics, list)
            assert len(metrics) >= 3
            names = [m.metric for m in metrics]
            assert "market_price_usd" in names
            assert "hash_rate" in names

    async def test_fetch_specific_metric(self) -> None:
        provider = OnChainProvider()
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(
            return_value={
                "market_price_usd": 65000.0,
                "hash_rate": 500_000_000.0,
                "n_tx": 300_000,
            }
        )
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            metric = await provider.fetch_metric("market_price_usd")
            assert metric is not None
            assert metric.metric == "market_price_usd"
            assert metric.value == 65000.0

    async def test_unknown_metric_returns_none(self) -> None:
        provider = OnChainProvider()
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(return_value={"market_price_usd": 65000.0})
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            result = await provider.fetch_metric("nonexistent_metric")
            assert result is None
