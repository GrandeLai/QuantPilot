"""因子 provider 注册表."""

from __future__ import annotations

import pandas as pd

from quantpilot.factors.providers.base import BaseFactorProvider


class FactorProviderRegistry:
    """顺序执行多个 provider，并合并其输出."""

    def __init__(self, providers: list[BaseFactorProvider]) -> None:
        self._providers = providers

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        outputs = []
        for provider in self._providers:
            result = provider.compute(frame)
            if not result.empty:
                outputs.append(result)
        if not outputs:
            return pd.DataFrame(index=frame.index)
        return pd.concat(outputs, axis=1)
