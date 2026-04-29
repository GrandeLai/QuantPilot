# Task phaseF9.short-interest-engine: 空头兴趣 + 轧空风险引擎

**Phase**: Phase F.9
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/short_interest/` 模块。

### 数据模型

```python
@dataclass
class ShortInterestData:
    ticker: str
    short_pct_float: float | None      # % of float sold short
    short_ratio: float | None          # days to cover (= short_shares / avg_daily_vol)
    shares_short: int | None
    shares_short_prior_month: int | None
    short_change_pct: float | None     # MoM change in short interest
    float_shares: int | None
    avg_daily_volume: int | None
    price_vs_52w_high: float | None    # current / 52w_high (momentum proxy)
    squeeze_risk_score: float          # 0-1
    signal: Literal["squeeze_setup", "high_short", "moderate", "low_short"]
    as_of_date: date
```

### 关键函数

```python
def compute_short_interest(ticker: str) -> ShortInterestData | None:
    """从 yfinance info 计算空头兴趣 + 轧空风险评分."""
```

### 轧空风险评分公式

```
# 成分 1：空头强度（short_pct_float）
short_intensity = min(1.0, short_pct_float / 0.30)   # 30% 以上满分

# 成分 2：日覆盖难度（days to cover）
dtc_score = min(1.0, short_ratio / 10.0)              # 10天+ 满分

# 成分 3：正向动量（价格 vs 52周高点）
momentum = max(0.0, price_vs_52w_high - 0.70)         # 距高点 < 30% 则有动量
momentum_score = min(1.0, momentum / 0.30)

# 综合得分
squeeze_risk_score = short_intensity * 0.4 + dtc_score * 0.4 + momentum_score * 0.2
```

### 信号分类

```
squeeze_setup: squeeze_risk_score >= 0.6 AND price_vs_52w_high >= 0.8
high_short:    short_pct_float >= 0.15
moderate:      0.05 <= short_pct_float < 0.15
low_short:     short_pct_float < 0.05
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/short_interest/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/short_interest/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "ShortInterestData\|compute_short_interest\|squeeze_risk_score" apps/stock-assistant/backend/src/quantpilot_stock/short_interest/engine.py`

- [ ] **AC-3**: 单元测试通过 (≥12)
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_short_interest_engine.py -v)` 退出码 0

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/short_interest/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/short_interest/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/short_interest/engine.py`
- `apps/stock-assistant/backend/tests/test_short_interest_engine.py`

> **批次开发说明**：F.9.1–F.9.3 在同一工作树批量开发并统一提交。
