"""策略类加载器."""
from __future__ import annotations


def load_strategy_class(name: str) -> type | None:
    """按策略名称加载策略类.

    目前支持从代码库内置策略中查找。
    """
    from quantpilot.strategy.builtin import BUILTIN_STRATEGIES

    return BUILTIN_STRATEGIES.get(name)
