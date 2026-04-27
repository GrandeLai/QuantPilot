"""因子 provider 注册表."""

from __future__ import annotations

import pandas as pd

from quantpilot_quant.factors.providers.base import BaseFactorProvider


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

    def provider_names(self) -> list[str]:
        """返回已注册 provider 名称."""
        return [provider.name for provider in self._providers]

    def available_provider_names(self) -> list[str]:
        """返回当前可用 provider 名称."""
        names: list[str] = []
        for provider in self._providers:
            available = getattr(provider, "available", True)
            if available:
                names.append(provider.name)
        return names
