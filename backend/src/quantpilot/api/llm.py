"""LLM 聊天 API — 支持 SSE 流式输出.

端点:
  POST /llm/chat       非流式聊天
  POST /llm/stream     SSE 流式聊天
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from quantpilot.llm.gateway import ChatMessage, LLMGateway

router = APIRouter(prefix="/llm", tags=["AI 助手"])


def _get_gateway(model: str) -> LLMGateway:
    """创建 LLM 网关，尝试从 keyring 加载 API key."""
    try:
        from quantpilot.security.keystore import load_api_key

        provider = "openai" if "gpt" in model else "anthropic" if "claude" in model else "openai"
        api_key = load_api_key(provider) or ""
    except Exception:
        api_key = ""
    return LLMGateway(model=model, api_key=api_key)


_CANDIDATE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
    {"id": "claude-opus-4-6", "name": "Claude Opus 4.6", "provider": "anthropic"},
    {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic"},
    {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "provider": "openai"},
]


@router.get("/models")
def list_models() -> dict[str, Any]:
    """返回已配置 API Key 的可用模型列表.

    对每个提供商尝试加载 API Key，有 Key 则标记为 available。
    """
    available: list[dict[str, Any]] = []
    try:
        from quantpilot.security.keystore import load_api_key
        configured: dict[str, bool] = {}
        for provider in ("openai", "anthropic"):
            key = load_api_key(provider)
            configured[provider] = bool(key)
    except Exception:
        configured = {}

    for m in _CANDIDATE_MODELS:
        available.append({**m, "available": configured.get(m["provider"], False)})

    return {"models": available}


class ChatRequest(BaseModel):
    """聊天请求模型."""

    messages: list[ChatMessage]
    model: str = "gpt-4o"


@router.post("/chat")
async def chat(req: ChatRequest) -> dict[str, Any]:
    """非流式 LLM 聊天."""
    gw = _get_gateway(req.model)
    reply = await gw.chat(req.messages)
    return {"reply": reply, "model": req.model}


@router.post("/stream")
async def stream_chat(req: ChatRequest) -> StreamingResponse:
    """SSE 流式 LLM 聊天."""
    gw = _get_gateway(req.model)

    async def event_stream() -> AsyncIterator[str]:
        async for token in gw.stream(req.messages):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


class GenerateStrategyRequest(BaseModel):
    """策略生成请求模型."""

    description: str
    model: str = "gpt-4o"


@router.post("/generate-strategy")
async def generate_strategy(req: GenerateStrategyRequest) -> dict[str, str]:
    """根据自然语言描述生成量化策略代码."""
    from quantpilot.llm.strategy_gen import StrategyGenerator

    gw = _get_gateway(req.model)
    gen = StrategyGenerator(model=req.model, api_key=gw.api_key)
    result = await gen.generate(req.description)
    return {
        "code": result.code,
        "explanation": result.explanation,
        "name": result.name,
    }
