"""QuantPilot unified LLM agent layer.

Usage:
    from quantpilot_stock.agent import get_default_agent, ChatMessage

    agent = get_default_agent()
    reply = await agent.chat([ChatMessage(role="user", content="hi")])
"""
from quantpilot_stock.agent._types import ChatMessage
from quantpilot_stock.agent.agent import QuantAgent, get_default_agent

__all__ = ["QuantAgent", "get_default_agent", "ChatMessage"]
