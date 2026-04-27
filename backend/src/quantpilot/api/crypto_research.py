"""OKX 多时间维度加密研究 API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from quantpilot_common.data import get_storage
from quantpilot_common.data.storage import MarketDataStorage
from quantpilot.research.models import (
    CryptoResearchDatasetSummary,
    CryptoResearchOptimizationSummary,
    CryptoResearchTrainSummary,
)
from quantpilot.research.service import CryptoResearchRequest, CryptoResearchService
from quantpilot.research.validation import TimeSeriesValidationConfig

router = APIRouter(prefix="/crypto/research", tags=["加密研究"])


class ValidationRequest(BaseModel):
    """训练验证窗口配置."""

    train_size: int = Field(ge=20)
    test_size: int = Field(ge=5)
    step_size: int = Field(ge=1)
    embargo_size: int = Field(default=0, ge=0)


class CryptoResearchDatasetRequest(BaseModel):
    """研究数据集请求."""

    symbol: str
    base_timeframe: str = "15m"
    higher_timeframes: list[str] = ["1h", "4h", "1d", "1w"]
    limit: int = Field(default=240, ge=60, le=5000)


class CryptoResearchTrainRequest(CryptoResearchDatasetRequest):
    """研究训练请求."""

    validation: ValidationRequest


class CryptoResearchOptimizeRequest(CryptoResearchDatasetRequest):
    """研究优化请求."""

    param_grid: dict[str, list[int | float]]


StorageDep = Annotated[MarketDataStorage, Depends(get_storage)]


@router.post("/dataset", response_model=CryptoResearchDatasetSummary)
def build_dataset_summary(
    req: CryptoResearchDatasetRequest,
    storage: StorageDep,
) -> CryptoResearchDatasetSummary:
    """返回多周期研究数据集摘要."""
    service = CryptoResearchService(storage)
    return service.build_dataset_summary(
        symbol=req.symbol,
        base_timeframe=req.base_timeframe,
        higher_timeframes=req.higher_timeframes,
        limit=req.limit,
    )


@router.post("/train", response_model=CryptoResearchTrainSummary)
def run_training(
    req: CryptoResearchTrainRequest,
    storage: StorageDep,
) -> CryptoResearchTrainSummary:
    """返回多周期训练与 walk-forward 验证摘要."""
    service = CryptoResearchService(storage)
    try:
        return service.train_and_validate(
            CryptoResearchRequest(
                symbol=req.symbol,
                base_timeframe=req.base_timeframe,
                higher_timeframes=req.higher_timeframes,
                limit=req.limit,
                validation=TimeSeriesValidationConfig(
                    train_size=req.validation.train_size,
                    test_size=req.validation.test_size,
                    step_size=req.validation.step_size,
                    embargo_size=req.validation.embargo_size,
                ),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/latest", response_model=CryptoResearchTrainSummary)
def get_latest_training_result(
    symbol: str,
    storage: StorageDep,
    base_timeframe: str = "15m",
) -> CryptoResearchTrainSummary:
    """读取最近一次缓存的训练摘要."""
    service = CryptoResearchService(storage)
    latest = service.get_latest(symbol=symbol, base_timeframe=base_timeframe)
    if latest is None:
        raise HTTPException(status_code=404, detail="暂无缓存研究结果")
    return latest


@router.post("/optimize", response_model=CryptoResearchOptimizationSummary)
def optimize_strategy(
    req: CryptoResearchOptimizeRequest,
    storage: StorageDep,
) -> CryptoResearchOptimizationSummary:
    """运行 VWAP_EMA_Trend 策略参数搜索."""
    service = CryptoResearchService(storage)
    try:
        return service.optimize_strategy(
            symbol=req.symbol,
            base_timeframe=req.base_timeframe,
            higher_timeframes=req.higher_timeframes,
            limit=req.limit,
            param_grid=req.param_grid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/optimize/latest", response_model=CryptoResearchOptimizationSummary)
def get_latest_optimization_result(
    symbol: str,
    strategy_id: str,
    storage: StorageDep,
    base_timeframe: str = "15m",
) -> CryptoResearchOptimizationSummary:
    """读取最近一次缓存的优化摘要."""
    service = CryptoResearchService(storage)
    latest = service.get_latest_optimization(
        symbol=symbol,
        base_timeframe=base_timeframe,
        strategy_id=strategy_id,
    )
    if latest is None:
        raise HTTPException(status_code=404, detail="暂无缓存优化结果")
    return latest
