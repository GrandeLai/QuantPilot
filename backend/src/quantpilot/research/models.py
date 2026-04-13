"""加密研究服务输出模型."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CryptoResearchDatasetSummary(BaseModel):
    """多周期研究数据集摘要."""

    symbol: str
    base_timeframe: str
    higher_timeframes: list[str]
    rows: int = Field(ge=0)
    dataset_version: str
    dataset_columns: list[str]


class WalkForwardWindowMetric(BaseModel):
    """单个 walk-forward 窗口指标."""

    train_start: int
    train_end: int
    test_start: int
    test_end: int
    accuracy: float
    strategy_return: float


class CryptoResearchTrainSummary(BaseModel):
    """训练与验证摘要."""

    symbol: str
    base_timeframe: str
    higher_timeframes: list[str]
    rows: int = Field(ge=0)
    dataset_version: str
    feature_count: int = Field(ge=0)
    feature_columns: list[str]
    validation_windows: int = Field(ge=0)
    window_metrics: list[WalkForwardWindowMetric]
    mean_accuracy: float
    mean_strategy_return: float
    latest_class_signal: int
    latest_class_probabilities: dict[str, float]
    feature_importance: dict[str, float]
    reversal_probability: float
    reversal_signal: str
    reversal_evidence: list[str]
