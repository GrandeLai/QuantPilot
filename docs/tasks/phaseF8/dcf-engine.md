# Task phaseF8.dcf-engine: DCF + Monte Carlo 估值引擎

**Phase**: Phase F.8
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/dcf/` 模块。

### 数据模型

```python
@dataclass
class WACCComponents:
    cost_of_equity: float     # CAPM: Rf + β × ERP
    cost_of_debt: float       # interest_expense / total_debt
    tax_rate: float
    debt_weight: float        # D / (D + E)
    equity_weight: float      # E / (D + E)
    wacc: float               # WACC = equity_weight × Ke + debt_weight × Kd × (1-T)
    beta: float
    risk_free_rate: float

@dataclass
class DCFResult:
    ticker: str
    current_price: float
    fair_value_p5: float      # 5th percentile Monte Carlo
    fair_value_p50: float     # median (base case)
    fair_value_p95: float     # 95th percentile
    wacc_components: WACCComponents
    base_fcf: float           # last 3yr avg free cash flow
    npv_fcf: float            # NPV of 5yr FCF projection
    terminal_value_pv: float  # PV of terminal value
    margin_of_safety: float   # (p50 - current) / p50
    valuation: Literal["deep_value", "undervalued", "fair", "overvalued", "overheated"]
    projected_fcfs: list[float]  # 5-year FCF projections (base case)
    as_of_date: date
```

### 关键函数

```python
def compute_wacc(ticker: str, *, risk_free_rate: float = 0.045, market_premium: float = 0.055) -> WACCComponents | None:
    """计算加权平均资本成本（CAPM + 资本结构）."""

def compute_dcf(
    ticker: str,
    *,
    risk_free_rate: float = 0.045,
    market_premium: float = 0.055,
    terminal_growth: float = 0.025,
    projection_years: int = 5,
    mc_simulations: int = 1000,
) -> DCFResult | None:
    """运行 DCF 估值 + 蒙特卡洛敏感度分析."""
```

### 蒙特卡洛参数分布

```
WACC        ~ N(wacc_base, σ=0.015)    # ±1.5% WACC uncertainty
FCF growth  ~ N(growth_base, σ=0.03)  # ±3% annual growth uncertainty
Terminal g  ~ N(0.025, σ=0.005)        # long-term growth uncertainty
```

### 估值分类

```
deep_value:  margin_of_safety > 0.30   (公允价值 vs 现价 > 30% 上行)
undervalued: 0.10 < m.o.s ≤ 0.30
fair:       -0.10 ≤ m.o.s ≤ 0.10
overvalued: -0.30 ≤ m.o.s < -0.10
overheated:  m.o.s < -0.30
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/dcf/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/dcf/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "DCFResult\|WACCComponents\|compute_dcf\|compute_wacc" apps/stock-assistant/backend/src/quantpilot_stock/dcf/engine.py`

- [ ] **AC-3**: 单元测试通过 (≥14)
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_dcf_engine.py -v)` 退出码 0

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/dcf/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/dcf/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/dcf/engine.py`
- `apps/stock-assistant/backend/tests/test_dcf_engine.py`

> **批次开发说明**：F.8.1–F.8.3 在同一工作树批量开发并统一提交。
