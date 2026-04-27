"""LLM 网关测试 — T-2.7/T-2.8 验收."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quantpilot_stock.llm.gateway import ChatMessage, LLMGateway
from quantpilot_stock.llm.tools import get_tool_definitions


class TestChatMessage:
    def test_user_message(self) -> None:
        msg = ChatMessage(role="user", content="分析 AAPL 的走势")
        assert msg.role == "user"
        assert msg.content == "分析 AAPL 的走势"

    def test_assistant_message(self) -> None:
        msg = ChatMessage(role="assistant", content="好的，让我查一下...")
        assert msg.role == "assistant"


class TestToolDefinitions:
    def test_tools_are_list(self) -> None:
        tools = get_tool_definitions()
        assert isinstance(tools, list)
        assert len(tools) >= 3

    def test_tools_have_required_fields(self) -> None:
        tools = get_tool_definitions()
        for tool in tools:
            assert "type" in tool
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]

    def test_fetch_bars_tool_present(self) -> None:
        tools = get_tool_definitions()
        names = [t["function"]["name"] for t in tools]
        assert "fetch_bars" in names

    def test_list_strategies_tool_present(self) -> None:
        tools = get_tool_definitions()
        names = [t["function"]["name"] for t in tools]
        assert "list_strategies" in names


@pytest.mark.asyncio
class TestLLMGateway:
    async def test_chat_returns_string(self) -> None:
        gw = LLMGateway(model="gpt-4o", api_key="test-key")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AAPL 近期走势强劲..."
        mock_response.choices[0].message.tool_calls = None

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            result = await gw.chat([ChatMessage(role="user", content="分析 AAPL")])
            assert isinstance(result, str)
            assert len(result) > 0

    async def test_chat_uses_system_prompt(self) -> None:
        gw = LLMGateway(model="gpt-4o", api_key="test-key")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        mock_response.choices[0].message.tool_calls = None

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            await gw.chat([ChatMessage(role="user", content="hello")])
            call_args = mock_llm.call_args
            messages = call_args.kwargs.get("messages") or (call_args.args[0] if call_args.args else [])
            has_system = any(m.get("role") == "system" for m in messages)
            assert has_system

    async def test_empty_history_raises(self) -> None:
        gw = LLMGateway(model="gpt-4o", api_key="test-key")
        with pytest.raises(ValueError, match="消息列表"):
            await gw.chat([])
