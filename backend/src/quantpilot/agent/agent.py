"""QuantAgent — unified LLM interface with middleware, system prompt, and singleton factory."""
from __future__ import annotations

import threading
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

from loguru import logger

from quantpilot.agent._types import AgentConfig, ChatMessage
from quantpilot.agent.middleware import LoggingMiddleware, Middleware
from quantpilot.agent.router import ModelRouter

SYSTEM_PROMPT = """你是 QuantPilot 的 AI 量化分析助手，具备以下能力：
- 分析股票/加密货币技术面（K线形态、技术指标）
- 解读基本面数据和财务指标
- 提供策略建议和风险分析
- 调用工具查询实时数据

请用简洁专业的中文回答。数据分析时先调用工具获取实际数据，再给出分析。"""

_DEFAULT_AGENT: QuantAgent | None = None
_DEFAULT_AGENT_LOCK = threading.Lock()


class QuantAgent:
    """Primary LLM interface for QuantPilot.

    Wraps ModelRouter with:
    - System prompt injection
    - Middleware chain (before_request / after_response / on_error)
    - Extension stubs: rag_retriever, tool_executor, memory_store (Protocol-ready)
    """

    def __init__(
        self,
        router: ModelRouter,
        middlewares: list[Middleware] | None = None,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self._router = router
        self._middlewares: list[Middleware] = (
            middlewares if middlewares is not None else [LoggingMiddleware()]
        )
        self._system_prompt = system_prompt

    def _build_messages(self, history: list[ChatMessage]) -> list[dict[str, Any]]:
        msgs: list[dict[str, Any]] = [{"role": "system", "content": self._system_prompt}]
        msgs.extend({"role": m.role, "content": m.content} for m in history)
        return msgs

    async def chat(self, history: list[ChatMessage]) -> str:
        """Non-streaming chat with fallback and middleware hooks."""
        if not history:
            raise ValueError("消息列表不能为空")

        messages = self._build_messages(history)
        context: dict[str, Any] = {}

        for mw in self._middlewares:
            await mw.before_request(messages, context)

        try:
            result = await self._router.chat(messages)
        except Exception as exc:
            for mw in self._middlewares:
                await mw.on_error(exc, context)
            raise

        for mw in self._middlewares:
            result = await mw.after_response(result, context)

        return result

    async def stream(self, history: list[ChatMessage]) -> AsyncIterator[str]:
        """Streaming chat with fallback and error middleware hook.

        Note: `after_response` middleware is NOT called for streams since the full
        response is never assembled as a single string. Use `before_request` or
        `on_error` for streaming-compatible hooks.
        """
        if not history:
            raise ValueError("消息列表不能为空")

        messages = self._build_messages(history)
        context: dict[str, Any] = {}

        for mw in self._middlewares:
            await mw.before_request(messages, context)

        try:
            async for token in self._router.stream(messages):
                yield token
        except Exception as exc:
            for mw in self._middlewares:
                await mw.on_error(exc, context)
            yield f"[错误] {exc}"


def _find_config_path() -> Path:
    """Locate llm_agents.toml relative to cwd or package root."""
    candidates = [
        Path("config/llm_agents.toml"),
        Path(__file__).parent.parent.parent.parent / "config" / "llm_agents.toml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return Path("config/llm_agents.toml")


def _make_key_loader() -> Callable[[str], str | None]:
    """Return a function that loads API keys from keystore."""
    def load_key(provider: str) -> str | None:
        try:
            from quantpilot.security.keystore import load_api_key
            return load_api_key(provider)
        except Exception:
            return None
    return load_key


def get_default_agent() -> QuantAgent:
    """Return the process-level QuantAgent singleton, creating it if needed."""
    global _DEFAULT_AGENT
    if _DEFAULT_AGENT is None:
        with _DEFAULT_AGENT_LOCK:
            if _DEFAULT_AGENT is None:  # double-checked locking
                config = AgentConfig.from_toml(_find_config_path())
                router = ModelRouter(config.models, key_loader=_make_key_loader())
                _DEFAULT_AGENT = QuantAgent(router=router)
                logger.info(
                    f"[Agent] initialized with {len(config.models)} models: "
                    + ", ".join(m.id for m in config.models)
                )
    return _DEFAULT_AGENT
