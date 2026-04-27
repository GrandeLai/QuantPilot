"""QuantPilot 钩子接口定义."""
from __future__ import annotations

import pluggy

hookspec = pluggy.HookspecMarker("quantpilot")
hookimpl = pluggy.HookimplMarker("quantpilot")


class QuantPilotSpec:
    """QuantPilot 插件钩子规范."""

    hookimpl = staticmethod(hookimpl)

    @hookspec
    def on_bar(self, symbol: str, close: float) -> str:
        """每根 K 线到达时调用."""

    @hookspec
    def on_signal(self, symbol: str, signal: str) -> str:
        """交易信号产生时调用."""

    @hookspec
    def on_alert(self, message: str) -> str:
        """告警触发时调用."""
