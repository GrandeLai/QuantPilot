"""LLM 网关 — 保持 API 兼容，plain chat/stream 委托给 QuantAgent."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import litellm
from loguru import logger
from pydantic import BaseModel

from quantpilot.llm.tools import execute_tool, get_tool_definitions

litellm.drop_params = True

SYSTEM_PROMPT = """你是 QuantPilot 的 AI 量化分析助手，具备以下能力：
- 分析股票/加密货币技术面（K线形态、技术指标）
- 解读基本面数据和财务指标
- 提供策略建议和风险分析
- 调用工具查询实时数据

请用简洁专业的中文回答。数据分析时先调用工具获取实际数据，再给出分析。"""


class ChatMessage(BaseModel):
    """聊天消息模型（向后兼容 re-export）."""

    role: str
    content: str


class LLMGateway:
    """LLM 网关 — tool calling 使用固定模型；plain chat/stream 委托给 QuantAgent."""

    def __init__(self, model: str = "gpt-4o", api_key: str = "") -> None:
        self._model = model
        self._api_key = api_key

    @property
    def api_key(self) -> str:
        """公开访问 API key."""
        return self._api_key

    def _build_messages(self, history: list[ChatMessage]) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        msgs.extend({"role": m.role, "content": m.content} for m in history)
        return msgs

    async def chat(self, history: list[ChatMessage], use_tools: bool = True) -> str:
        """非流式聊天.

        use_tools=True: 保留原有 Function Calling 逻辑（固定模型，支持 tool_call_id）.
        use_tools=False: 委托给 QuantAgent，享有多模型 fallback.
        """
        if not history:
            raise ValueError("消息列表不能为空")

        if not use_tools:
            from quantpilot.agent import ChatMessage as AgentMsg
            from quantpilot.agent import get_default_agent
            agent = get_default_agent()
            return await agent.chat([AgentMsg(role=m.role, content=m.content) for m in history])

        return await self._chat_with_tools(history)

    async def _chat_with_tools(self, history: list[ChatMessage]) -> str:
        """原有 Function Calling 逻辑 — 固定模型，支持多轮 tool_call_id."""
        messages = self._build_messages(history)
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "api_key": self._api_key or None,
            "tools": get_tool_definitions(),
            "tool_choice": "auto",
        }

        try:
            response = await litellm.acompletion(**kwargs)
            msg = response.choices[0].message

            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_results = []
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    result = await execute_tool(fn_name, args)
                    tool_results.append(result)
                    logger.info(f"[LLM] tool call: {fn_name}({args}) → {result[:100]}")

                messages.append({"role": "assistant", "content": msg.content or ""})
                for i, tc in enumerate(msg.tool_calls):
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": tool_results[i]}
                    )
                follow_up = await litellm.acompletion(
                    model=self._model, messages=messages, api_key=self._api_key or None
                )
                return follow_up.choices[0].message.content or ""

            return msg.content or ""
        except Exception as e:
            logger.error(f"[LLM] chat error: {e}")
            raise

    async def stream(self, history: list[ChatMessage]) -> AsyncIterator[str]:
        """流式聊天 — 委托给 QuantAgent，享有多模型 fallback."""
        if not history:
            raise ValueError("消息列表不能为空")
        from quantpilot.agent import ChatMessage as AgentMsg
        from quantpilot.agent import get_default_agent
        agent = get_default_agent()
        async for token in agent.stream(
            [AgentMsg(role=m.role, content=m.content) for m in history]
        ):
            yield token
