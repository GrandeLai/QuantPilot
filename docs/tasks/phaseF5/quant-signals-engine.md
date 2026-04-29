# Task phaseF5.quant-signals-engine: Beneish M-Score + Russell 调仓预览引擎

**Phase**: Phase F.5
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/` 模块：

### 数据模型

```python
@dataclass
class BeneishMScore:
    ticker: str
    m_score: float           # < -2.22 安全；-2.22 ~ -1.78 灰色区；> -1.78 高风险
    risk_level: Literal["safe", "grey", "manipulator"]
    ratios: dict[str, float]  # 8 个财务比率明细
    interpretation: str
    as_of_date: date

@dataclass
class RussellMembership:
    ticker: str
    market_cap_usd: float
    estimated_rank: int | None    # 在所有美股中的市值排名估算
    current_index: Literal["Russell 1000", "Russell 2000", "Outside Russell 3000", "Unknown"]
    proximity_score: float        # 0-1，距离 1000/2000 边界的远近（越高越接近边界）
    rebalance_signal: Literal["likely_add_1000", "likely_drop_1000",
                               "likely_add_2000", "likely_drop_2000", "stable", "unknown"]
```

### 关键函数

```python
def compute_beneish_mscore(ticker: str) -> BeneishMScore | None:
    """计算 Beneish M-Score（8 维盈利操纵检测指标）."""

def estimate_russell_membership(
    ticker: str,
    *,
    universe_tickers: list[str] | None = None,  # None → 使用内置 SP500 + Russell 常见成分
) -> RussellMembership | None:
    """估算 ticker 的 Russell 指数归属和边界接近度."""
```

### Beneish M-Score 8 个比率

1. **DSRI** = (AR/Sales)_t / (AR/Sales)_{t-1}    应收账款天数增加 → 收入虚增
2. **GMI** = Gross Margin_{t-1} / Gross Margin_t  毛利率恶化 → 财务压力
3. **AQI** = (1 - (CA+PPE)/TA)_t / (1 - (CA+PPE)/TA)_{t-1}  资产质量下降
4. **SGI** = Sales_t / Sales_{t-1}                收入高增长（操纵动机）
5. **DEPI** = (Dep/(Dep+PPE))_{t-1} / (Dep/(Dep+PPE))_t  折旧率下降
6. **SGAI** = (SGA/Sales)_t / (SGA/Sales)_{t-1}  销售费用增加
7. **LVGI** = (LTD+CL)/TA_t / (LTD+CL)/TA_{t-1} 杠杆增加
8. **TATA** = (NI - CFO) / TA_t                   总应计项目（越高越危险）

M = -4.840 + 0.920×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "BeneishMScore\|RussellMembership\|compute_beneish_mscore\|estimate_russell_membership" apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/engine.py`

- [ ] **AC-3**: M-Score 公式存在
  - `grep -q "DSRI\|GMI\|TATA\|-4.840\|m_score" apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/engine.py`

- [ ] **AC-4**: 单元测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_quant_signals_engine.py -v)` 退出码 0
  - 至少 12 个测试

- [ ] **AC-5**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/quant_signals/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/engine.py`
- `apps/stock-assistant/backend/tests/test_quant_signals_engine.py`

> **批次开发说明**：F.5.1–F.5.3 在同一工作树批量开发并统一提交。
