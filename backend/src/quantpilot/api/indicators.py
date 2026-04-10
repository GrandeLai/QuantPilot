"""技术指标 API 路由.

端点：
  GET  /indicators/list              列出所有支持的指标
  POST /indicators/calculate         计算单个指标
  POST /indicators/batch             批量计算多个指标
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.data.models import OHLCVBar
from quantpilot.indicators.calculator import INDICATOR_REGISTRY, IndicatorCalculator

router = APIRouter(prefix="/indicators", tags=["技术指标"])
_calc = IndicatorCalculator()


class IndicatorRequest(BaseModel):
    """单指标计算请求."""

    bars: list[OHLCVBar]
    indicator: str
    params: dict[str, Any] | None = None


class BatchIndicatorRequest(BaseModel):
    """批量指标计算请求."""

    bars: list[OHLCVBar]
    indicators: list[str]


@router.get("/list")
def list_indicators() -> dict[str, Any]:
    """列出所有支持的技术指标及默认参数."""
    return {
        "count": len(INDICATOR_REGISTRY),
        "indicators": {
            name: {
                "group": info["group"],
                "default_params": info["params"],
            }
            for name, info in INDICATOR_REGISTRY.items()
        },
    }


@router.post("/calculate")
def calculate_indicator(req: IndicatorRequest) -> dict[str, Any]:
    """计算单个技术指标."""
    if req.indicator not in INDICATOR_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的指标: {req.indicator}，可用: {list(INDICATOR_REGISTRY.keys())}",
        )
    if len(req.bars) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 根 K 线")

    try:
        result = _calc.calculate(req.bars, req.indicator, req.params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "indicator": req.indicator,
        "count": len(req.bars),
        "data": result,
    }


@router.post("/batch")
def calculate_batch(req: BatchIndicatorRequest) -> dict[str, Any]:
    """批量计算多个技术指标."""
    if len(req.bars) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 根 K 线")
    if not req.indicators:
        raise HTTPException(status_code=400, detail="indicators 列表不能为空")

    results = _calc.calculate_batch(req.bars, req.indicators)
    return {
        "count": len(req.bars),
        "indicators": results,
    }
