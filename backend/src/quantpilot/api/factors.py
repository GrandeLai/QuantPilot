"""因子研究 API — IC/IR 分析.

端点:
  POST /factors/ic-analysis   计算因子 IC/IR 及分层收益
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.factors.calculator import FactorCalculator

router = APIRouter(prefix="/factors", tags=["因子研究"])
_calc = FactorCalculator()


class FactorDataPoint(BaseModel):
    factor_value: float
    forward_return: float


class ICAnalysisRequest(BaseModel):
    data: list[FactorDataPoint]
    window: int = 20
    n_quantiles: int = 5


@router.post("/ic-analysis")
def ic_analysis(req: ICAnalysisRequest) -> dict[str, Any]:
    """计算因子 IC/IR 及分层回测结果."""
    if len(req.data) < req.window:
        raise HTTPException(status_code=400, detail=f"数据量不足，至少需要 {req.window} 条")
    df = pd.DataFrame([{"factor": d.factor_value, "forward_return": d.forward_return} for d in req.data])
    ic_series = _calc.compute_ic_series(df, window=req.window)
    ir_result = _calc.compute_ir(ic_series)
    layers = _calc.layered_returns(df["factor"], df["forward_return"], n_quantiles=req.n_quantiles)
    return {
        "ic": ir_result.ic,
        "ir": ir_result.ir,
        "ic_mean": ir_result.ic_mean,
        "ic_std": ir_result.ic_std,
        "n_periods": ir_result.n_periods,
        "ic_series": ic_series,
        "layered_returns": layers,
    }
