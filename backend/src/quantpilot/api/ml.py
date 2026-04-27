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

from quantpilot_common.data.models import OHLCVBar
from quantpilot.ml.feature_selector import FeatureSelector
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
    corr_threshold: float = 0.85  # 特征相关性去冗余阈值


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

    # ── 动态特征筛选：去除高相关冗余，保留互信息更高的特征 ────────────────
    candidate_cols = [c for c in LGBMStrategy.FEATURE_COLS if c in df.columns]
    selected_cols = candidate_cols  # 默认：保留所有候选特征
    if len(candidate_cols) >= 2 and len(df) >= 10:
        try:
            selector = FeatureSelector(corr_threshold=req.corr_threshold)
            selected_cols, selection_report = selector.fit_transform(
                X=df[candidate_cols],
                y=df["target"],
                target_type="classification",
            )
        except ValueError:
            selected_cols = candidate_cols  # 筛选失败则回退到全量特征
    # ─────────────────────────────────────────────────────────────────────────

    strat = LGBMStrategy()
    strat.fit(df, feature_columns=selected_cols)
    _registry.save(req.model_name, strat)
    return {
        "message": f"模型 '{req.model_name}' 训练完成",
        "samples": len(df),
        "features_before_selection": len(candidate_cols),
        "features_after_selection": len(selected_cols),
        "selected_features": selected_cols,
    }


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
