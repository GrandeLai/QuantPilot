"""飞书文档推送 — 将 Markdown 报告推送至飞书云文档."""
from __future__ import annotations

import httpx
from loguru import logger
from pydantic import BaseModel

FEISHU_API = "https://open.feishu.cn/open-apis"


class FeishuDocResult(BaseModel):
    """飞书文档创建结果."""

    document_id: str
    url: str
    title: str


class FeishuDocPusher:
    """使用飞书 Open API 创建并写入文档."""

    def __init__(self, app_id: str, app_secret: str) -> None:
        self._app_id = app_id
        self._app_secret = app_secret

    async def _get_access_token(self) -> str:
        """获取飞书租户 access token."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{FEISHU_API}/auth/v3/tenant_access_token/internal",
                json={"app_id": self._app_id, "app_secret": self._app_secret},
            )
        data = resp.json()
        if data.get("code", 0) != 0:
            raise RuntimeError(f"获取飞书 token 失败: {data.get('msg', 'unknown')}")
        return str(data["tenant_access_token"])

    async def _create_document(self, token: str, title: str) -> str:
        """创建空飞书文档，返回 document_id."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{FEISHU_API}/docx/v1/documents",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"title": title, "folder_token": ""},
            )
        data = resp.json()
        if data.get("code", 0) != 0:
            raise RuntimeError(f"创建飞书文档失败: {data.get('msg', 'unknown')}")
        return str(data["data"]["document"]["document_id"])

    async def _append_content(self, token: str, document_id: str, content: str) -> None:
        """将 Markdown 内容作为代码块追加到文档."""
        block = {
            "block_type": 4,  # code block
            "code": {
                "style": {"language": 1},  # 1 = Plain Text
                "elements": [{"text_run": {"content": content[:50000]}}],
            },
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{FEISHU_API}/docx/v1/documents/{document_id}/blocks/{document_id}/children",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"children": [block], "index": 0},
            )
        data = resp.json()
        if data.get("code", 0) != 0:
            logger.warning(f"[FeishuDoc] 追加内容失败: {data.get('msg')}")

    async def push_markdown(self, markdown: str, title: str) -> FeishuDocResult:
        """创建飞书文档并推送 Markdown 内容."""
        token = await self._get_access_token()
        document_id = await self._create_document(token, title)
        await self._append_content(token, document_id, markdown)
        url = f"https://feishu.cn/docx/{document_id}"
        logger.info(f"[FeishuDoc] 文档已创建: {url}")
        return FeishuDocResult(document_id=document_id, url=url, title=title)
