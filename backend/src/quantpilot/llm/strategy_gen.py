"""LLM 驱动策略代码生成器 — T-3.1."""
from __future__ import annotations

import re

from loguru import logger
from pydantic import BaseModel

STRATEGY_TEMPLATE = '''
你是一位量化策略专家，请根据用户描述生成完整的 QuantPilot 策略 Python 代码。

## 策略基类接口

```python
from quantpilot.strategy.base import BaseStrategy, StrategyContext
from quantpilot_common.data.models import OHLCVBar

class MyStrategy(BaseStrategy):
    name = "my_strategy"           # 唯一标识
    description = "策略说明"

    def on_init(self, context: StrategyContext) -> None:
        """初始化，设置参数."""
        pass

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        """每根K线触发. 通过 context.buy/sell 下单."""
        # 买入示例: context.buy(bar.symbol, quantity=100, price=bar.close)
        # 卖出示例: context.sell(bar.symbol, quantity=100, price=bar.close)
        pass
```

## 要求
1. 生成完整可运行的策略类（继承 BaseStrategy）
2. 代码包含在 ```python ... ``` 代码块中
3. 之后一行写：EXPLANATION: <一句话解释策略逻辑>
4. 最后一行写：NAME: <策略英文名>

## 用户需求
{description}
'''


class StrategyGenResult(BaseModel):
    """LLM 策略生成结果."""

    code: str
    explanation: str
    name: str


class StrategyGenerator:
    """基于 LLM 将自然语言描述转换为可执行 Python 策略代码."""

    def __init__(self, model: str = "gpt-4o", api_key: str = "") -> None:
        # model/api_key kept for API backwards compatibility; generate() delegates to
        # get_default_agent() which manages model selection via llm_agents.toml config.
        self._model = model
        self._api_key = api_key

    async def generate(self, description: str) -> StrategyGenResult:
        """根据自然语言描述生成策略代码，委托给 QuantAgent.

        Args:
            description: 策略自然语言描述

        Returns:
            包含代码、解释和名称的生成结果

        Raises:
            ValueError: 当描述为空时
        """
        if not description.strip():
            raise ValueError("描述不能为空")

        prompt = STRATEGY_TEMPLATE.format(description=description.strip())

        from quantpilot.agent import ChatMessage, get_default_agent
        agent = get_default_agent()
        try:
            raw = await agent.chat([ChatMessage(role="user", content=prompt)])
            logger.info(f"[StrategyGen] generated {len(raw)} chars for: {description[:50]}")
            return self._parse_response(raw, description)
        except Exception as e:
            logger.error(f"[StrategyGen] error: {e}")
            raise

    def _parse_response(self, raw: str, description: str) -> StrategyGenResult:
        """从 LLM 响应中提取代码、解释和名称.

        Args:
            raw: LLM 原始响应文本
            description: 原始策略描述（用于 fallback）

        Returns:
            解析后的策略生成结果
        """
        # Extract code block
        code_match = re.search(r"```python\s*(.*?)```", raw, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
        else:
            # Fallback: take everything before EXPLANATION
            code = raw.split("EXPLANATION:")[0].strip()

        # Extract explanation
        expl_match = re.search(r"EXPLANATION:\s*(.+?)(?:\n|$)", raw)
        explanation = expl_match.group(1).strip() if expl_match else description[:80]

        # Extract name
        name_match = re.search(r"NAME:\s*(.+?)(?:\n|$)", raw)
        name = name_match.group(1).strip() if name_match else "GeneratedStrategy"

        return StrategyGenResult(code=code, explanation=explanation, name=name)
