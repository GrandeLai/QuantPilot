"""ML 策略 API.

端点:
  POST /ml/train      训练 LightGBM 策略
  POST /ml/predict    对新数据进行预测
  GET  /ml/models     列出已保存模型
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.data.models import OHLCVBar
from quantpilot.ml.features import FeatureEngineer
from quantpilot.ml.registry import MLModelRegistry
from quantpilot.ml.strategy import LGBMStrategy

router = APIRouter(prefix="/ml", tags=["ML策略"])

_registry = MLModelRegistry()
_feature_engineer = FeatureEngineer()


class BarInput(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TrainRequest(BaseModel):
    model_name: str
    bars: list[BarInput]


class PredictRequest(BaseModel):
    model_name: str
    bars: list[BarInput]


def _to_bars(bar_inputs: list[BarInput]) -> list[OHLCVBar]:
    return [
        OHLCVBar(
            symbol=b.symbol,
            timeframe=b.timeframe,
            timestamp=datetime.fromisoformat(b.timestamp).replace(tzinfo=UTC),
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=b.volume,
        )
        for b in bar_inputs
    ]


@router.post("/train")
def train_model(req: TrainRequest) -> dict[str, Any]:
    """训练 LightGBM 策略并保存到注册表."""
    bars = _to_bars(req.bars)
    if len(bars) < 30:
        raise HTTPException(status_code=400, detail="训练数据至少需要 30 根 K 线")
    df = _feature_engineer.compute(bars)
    if len(df) < 10:
        raise HTTPException(status_code=400, detail="特征计算后数据不足")
    strat = LGBMStrategy()
    strat.fit(df)
    _registry.save(req.model_name, strat)
    return {"message": f"模型 '{req.model_name}' 训练完成", "samples": len(df)}


@router.post("/predict")
def predict(req: PredictRequest) -> dict[str, Any]:
    """用已保存的模型预测新数据信号."""
    model = _registry.load(req.model_name)
    if model is None:
        raise HTTPException(status_code=404, detail=f"模型 '{req.model_name}' 不存在")
    bars = _to_bars(req.bars)
    df = _feature_engineer.compute(bars)
    if len(df) == 0:
        raise HTTPException(status_code=400, detail="特征计算后数据为空")
    preds = model.predict(df)  # type: ignore[union-attr]
    return {"predictions": preds, "count": len(preds)}


@router.get("/models")
def list_models() -> dict[str, Any]:
    """列出所有已保存模型."""
    return {"models": _registry.list_models()}
