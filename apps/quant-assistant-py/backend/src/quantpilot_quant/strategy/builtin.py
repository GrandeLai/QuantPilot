"""内置策略注册表."""
from __future__ import annotations

from quantpilot_quant.strategy.templates import TEMPLATE_STRATEGIES

# 内置策略字典: {name: class}，直接复用模板策略注册表
BUILTIN_STRATEGIES = dict(TEMPLATE_STRATEGIES)
