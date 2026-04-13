"""因子 provider 抽象接口."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseFactorProvider(ABC):
    """统一的因子 provider 接口."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称."""

    @abstractmethod
    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        """对输入数据集计算因子特征."""
