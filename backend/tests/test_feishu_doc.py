"""飞书文档推送测试 — T-3.4 验收."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quantpilot.reports.feishu_doc import FeishuDocPusher, FeishuDocResult


class TestFeishuDocResult:
    def test_has_fields(self) -> None:
        r = FeishuDocResult(document_id="abc123", url="https://feishu.cn/docx/abc123", title="Test")
        assert r.document_id == "abc123"
        assert "abc123" in r.url


class TestFeishuDocPusher:
    async def test_create_document_calls_api(self) -> None:
        pusher = FeishuDocPusher(app_id="app1", app_secret="secret1")
        mock_token_resp = MagicMock()
        mock_token_resp.json = MagicMock(return_value={"tenant_access_token": "t-token", "code": 0})
        mock_doc_resp = MagicMock()
        mock_doc_resp.json = MagicMock(return_value={
            "code": 0,
            "data": {"document": {"document_id": "doc123", "title": "Test Report"}},
        })
        mock_append_resp = MagicMock()
        mock_append_resp.json = MagicMock(return_value={"code": 0})

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [mock_token_resp, mock_doc_resp, mock_append_resp]
            result = await pusher.push_markdown("# Test Report\n\nContent here.", "Test Report")
            assert mock_post.called
            assert isinstance(result, FeishuDocResult)

    async def test_get_token_raises_on_failure(self) -> None:
        pusher = FeishuDocPusher(app_id="bad", app_secret="bad")
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(return_value={"code": 99991661, "msg": "invalid app"})
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            with pytest.raises(RuntimeError, match="获取飞书 token 失败"):
                await pusher._get_access_token()

    async def test_push_markdown_returns_url(self) -> None:
        pusher = FeishuDocPusher(app_id="a", app_secret="s")
        with patch.object(pusher, "_get_access_token", return_value="tok"), \
             patch.object(pusher, "_create_document", return_value="docXYZ"), \
             patch.object(pusher, "_append_content", return_value=None):
            result = await pusher.push_markdown("# Hello", "Hello Doc")
            assert result.document_id == "docXYZ"
            assert "docXYZ" in result.url
