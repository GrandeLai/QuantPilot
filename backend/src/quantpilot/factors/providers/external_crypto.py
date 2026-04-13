"""外部加密因子库适配 provider."""

from __future__ import annotations

import importlib

import pandas as pd

from quantpilot.factors.providers.base import BaseFactorProvider


class ExternalCryptoFactorProvider(BaseFactorProvider):
    """可选第三方因子库适配器，缺依赖时自动降级为空输出."""

    def __init__(self, module_name: str = "crypto_factor_lib", entrypoint: str = "build_features") -> None:
        self._module_name = module_name
        self._entrypoint = entrypoint

    @property
    def name(self) -> str:
        return "external_crypto"

    @property
    def available(self) -> bool:
        try:
            importlib.import_module(self._module_name)
        except ModuleNotFoundError:
            return False
        return True

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(index=frame.index)
        if not self.available:
            return pd.DataFrame(index=frame.index)

        module = importlib.import_module(self._module_name)
        builder = getattr(module, self._entrypoint)
        result = builder(frame.copy())
        if not isinstance(result, pd.DataFrame):
            raise TypeError(f"{self._module_name}.{self._entrypoint} must return a pandas DataFrame")
        return result
