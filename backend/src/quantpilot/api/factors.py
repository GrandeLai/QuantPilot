"""因子研究 API — 因子目录 + IC/IR 分析.

端点:
  GET  /factors/catalog          返回全量因子目录（元数据）
  POST /factors/ic-analysis      计算单因子 IC/IR 及分层收益
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.factors.calculator import FactorCalculator

router = APIRouter(prefix="/factors", tags=["因子研究"])
_calc = FactorCalculator()


# ── 因子目录 ──────────────────────────────────────────────────────────────────


class FactorInfo(BaseModel):
    """单个因子的元数据."""

    name: str
    category: str   # 动量 | 反转 | 波动率 | 量价 | 形态 | 跨周期 | 振荡器
    source: str     # core_crypto | advanced_crypto | pandas_ta_crypto
    window: int | None
    description: str
    range_hint: str | None  # "[0, 100]" | "无界" | "[-1, 1]"


_CATALOG: list[FactorInfo] = [
    # ── CoreCryptoFactorProvider ──────────────────────────────────────────────
    FactorInfo(name="returns",           category="动量",   source="core_crypto",      window=1,    description="1 期简单收益率 (close/prev_close - 1)",                             range_hint="无界"),
    FactorInfo(name="log_returns",       category="动量",   source="core_crypto",      window=1,    description="对数收益率 ln(close/prev_close)，统计特性更好",                     range_hint="无界"),
    FactorInfo(name="momentum_5",        category="动量",   source="core_crypto",      window=5,    description="5 期价格变化率",                                                   range_hint="无界"),
    FactorInfo(name="momentum_20",       category="动量",   source="core_crypto",      window=20,   description="20 期价格变化率",                                                  range_hint="无界"),
    FactorInfo(name="volume_ratio",      category="量价",   source="core_crypto",      window=20,   description="当期成交量 / 20 期均量，衡量成交活跃度",                            range_hint="无界"),
    FactorInfo(name="ema_10",            category="趋势",   source="core_crypto",      window=10,   description="10 期指数移动平均",                                                range_hint="无界"),
    FactorInfo(name="ema_20",            category="趋势",   source="core_crypto",      window=20,   description="20 期指数移动平均",                                                range_hint="无界"),
    FactorInfo(name="ema_50",            category="趋势",   source="core_crypto",      window=50,   description="50 期指数移动平均",                                                range_hint="无界"),
    FactorInfo(name="ema_spread_10_20",  category="趋势",   source="core_crypto",      window=20,   description="ema_10/ema_20 - 1，快慢线偏离度",                                  range_hint="无界"),
    FactorInfo(name="ema_spread_20_50",  category="趋势",   source="core_crypto",      window=50,   description="ema_20/ema_50 - 1，中长期偏离度",                                  range_hint="无界"),
    FactorInfo(name="macd_line",         category="趋势",   source="core_crypto",      window=26,   description="MACD 主线 (EMA12 - EMA26)",                                       range_hint="无界"),
    FactorInfo(name="macd_signal",       category="趋势",   source="core_crypto",      window=35,   description="MACD 信号线（主线 9 期 EMA）",                                     range_hint="无界"),
    FactorInfo(name="macd_hist",         category="趋势",   source="core_crypto",      window=35,   description="MACD 柱状图（主线 - 信号线），正值=多头动能",                       range_hint="无界"),
    FactorInfo(name="atr_14",            category="波动率", source="core_crypto",      window=14,   description="14 期平均真实波幅，衡量市场波动强度",                               range_hint="无界"),
    FactorInfo(name="adx_14",            category="趋势",   source="core_crypto",      window=14,   description="平均趋向指数，> 25 为趋势行情",                                    range_hint="[0, 100]"),
    FactorInfo(name="plus_di_14",        category="趋势",   source="core_crypto",      window=14,   description="+DI 多方向力量，与 -DI 交叉判断趋势方向",                           range_hint="[0, 100]"),
    FactorInfo(name="minus_di_14",       category="趋势",   source="core_crypto",      window=14,   description="-DI 空方向力量",                                                   range_hint="[0, 100]"),
    FactorInfo(name="rsi_14",            category="反转",   source="core_crypto",      window=14,   description="14 期相对强弱指数，> 70 超买，< 30 超卖",                          range_hint="[0, 100]"),
    FactorInfo(name="bb_width_20",       category="波动率", source="core_crypto",      window=20,   description="布林带宽度 = (上轨-下轨)/中轨，量化波动率区间",                     range_hint="无界"),
    FactorInfo(name="donchian_20",       category="趋势",   source="core_crypto",      window=20,   description="20 期唐奇安通道宽度（最高 - 最低）",                               range_hint="无界"),
    # ── AdvancedCryptoFactorProvider ─────────────────────────────────────────
    FactorInfo(name="vwap_dev_20",       category="量价",   source="advanced_crypto",  window=20,   description="20 期滚动 VWAP 乖离率（%），正值=价格高于均量均价",                 range_hint="无界"),
    FactorInfo(name="vwap_dev_60",       category="量价",   source="advanced_crypto",  window=60,   description="60 期滚动 VWAP 乖离率",                                            range_hint="无界"),
    FactorInfo(name="skewness_20",       category="波动率", source="advanced_crypto",  window=20,   description="20 期对数收益率偏度，捕捉分布不对称性",                             range_hint="无界"),
    FactorInfo(name="skewness_60",       category="波动率", source="advanced_crypto",  window=60,   description="60 期对数收益率偏度",                                              range_hint="无界"),
    FactorInfo(name="kurtosis_20",       category="波动率", source="advanced_crypto",  window=20,   description="20 期超额峰度，> 0 肥尾，高波动预警",                              range_hint="无界"),
    FactorInfo(name="kurtosis_60",       category="波动率", source="advanced_crypto",  window=60,   description="60 期超额峰度",                                                    range_hint="无界"),
    FactorInfo(name="upper_shadow_ratio",category="形态",   source="advanced_crypto",  window=None, description="上影线/实体比率，值越大=上方卖压越强（射击之星）",                   range_hint="无界"),
    FactorInfo(name="lower_shadow_ratio",category="形态",   source="advanced_crypto",  window=None, description="下影线/实体比率，值越大=下方买盘越强（锤子线）",                   range_hint="无界"),
    FactorInfo(name="pin_score",         category="形态",   source="advanced_crypto",  window=None, description="插针方向得分，+1=锤子线（看涨），-1=射击之星（看跌）",              range_hint="[-1, 1]"),
    FactorInfo(name="mtf_resonance",     category="跨周期", source="advanced_crypto",  window=None, description="多时间框架动量方向一致性，+1=全周期向上共振",                       range_hint="[-1, 1]"),
    # ── PandasTaCryptoFactorProvider ─────────────────────────────────────────
    FactorInfo(name="cci_20",            category="反转",   source="pandas_ta_crypto", window=20,   description="Commodity Channel Index，偏离统计均价的标准化程度，±100 为超买超卖阈值", range_hint="无界"),
    FactorInfo(name="willr_14",          category="反转",   source="pandas_ta_crypto", window=14,   description="Williams %R，< -80 超卖，> -20 超买",                             range_hint="[-100, 0]"),
    FactorInfo(name="mfi_14",            category="量价",   source="pandas_ta_crypto", window=14,   description="Money Flow Index（量价加权 RSI），> 80 超买，< 20 超卖",            range_hint="[0, 100]"),
    FactorInfo(name="stoch_k",           category="振荡器", source="pandas_ta_crypto", window=14,   description="随机振荡器 %K 快线，当前价在 N 期区间的相对位置",                   range_hint="[0, 100]"),
    FactorInfo(name="stoch_d",           category="振荡器", source="pandas_ta_crypto", window=14,   description="随机振荡器 %D 慢线（%K 的 3 期均值）",                             range_hint="[0, 100]"),
    FactorInfo(name="roc_10",            category="动量",   source="pandas_ta_crypto", window=10,   description="Rate of Change（10 期价格变化率），正=上涨动能",                    range_hint="无界"),
    FactorInfo(name="dpo_20",            category="振荡器", source="pandas_ta_crypto", window=20,   description="Detrended Price Oscillator，剔除长期趋势，放大短周期波动",           range_hint="无界"),
]


@router.get("/catalog", response_model=list[FactorInfo])
def factor_catalog() -> list[FactorInfo]:
    """返回当前系统全量因子目录（40 个因子的元数据）."""
    return _CATALOG


# ── 单因子 IC/IR 分析 ─────────────────────────────────────────────────────────


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
