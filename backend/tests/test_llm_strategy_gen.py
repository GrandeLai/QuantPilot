"""LLM 策略代码生成测试 — T-3.1 验收."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from quantpilot.llm.strategy_gen import StrategyGenerator, StrategyGenResult


class TestStrategyGenResult:
    def test_has_required_fields(self) -> None:
        r = StrategyGenResult(code="# test", explanation="买入后持有", name="TestStrat")
        assert r.code == "# test"
        assert r.explanation == "买入后持有"
        assert r.name == "TestStrat"


class TestStrategyGenerator:
    async def test_generate_returns_result(self) -> None:
        gen = StrategyGenerator(model="gpt-4o", api_key="test")
        mock_raw = '''```python
# strategy code
class MyStrategy:
    name = "my_strategy"
```
EXPLANATION: 这是一个简单策略
NAME: MyStrategy'''

        with patch(
            "quantpilot.agent.agent.QuantAgent.chat",
            new=AsyncMock(return_value=mock_raw),
        ):
            result = await gen.generate("当RSI低于30时买入，高于70时卖出")
            assert isinstance(result, StrategyGenResult)
            assert len(result.code) > 0

    async def test_generate_raises_on_empty_description(self) -> None:
        gen = StrategyGenerator(model="gpt-4o", api_key="test")
        with pytest.raises(ValueError, match="描述"):
            await gen.generate("")

    async def test_extract_code_block(self) -> None:
        gen = StrategyGenerator(model="gpt-4o", api_key="test")
        raw = '```python\nclass Strat:\n    name = "s"\n```\nEXPLANATION: OK\nNAME: Strat'
        result = gen._parse_response(raw, "test")
        assert "class Strat" in result.code
        assert result.explanation == "OK"
        assert result.name == "Strat"

    async def test_fallback_when_no_code_block(self) -> None:
        gen = StrategyGenerator(model="gpt-4o", api_key="test")
        raw = "class Strat:\n    name = 'fallback'\nEXPLANATION: fallback\nNAME: Fallback"
        result = gen._parse_response(raw, "fallback prompt")
        assert len(result.code) > 0
