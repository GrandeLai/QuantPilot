# Task phaseF6.eps-revision-engine: EPS 修正动量引擎

**Phase**: Phase F.6
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/eps_revision/` 模块。

### 数据模型

```python
@dataclass
class EpsRevisionPeriod:
    period: str         # "0q" | "+1q" | "0y" | "+1y"
    period_label: str   # "本季度" | "下季度" | "本年度" | "明年度"
    up_7d: int
    down_7d: int
    up_30d: int
    down_30d: int
    revision_score_7d: float   # (up - down) / max(1, up + down)  ∈ [-1, 1]
    revision_score_30d: float
    direction: Literal["strong_upgrade", "upgrade", "neutral", "downgrade", "strong_downgrade"]

@dataclass
class AnalystTargets:
    current_price: float | None
    target_mean: float | None
    target_median: float | None
    target_high: float | None
    target_low: float | None
    upside_pct: float | None  # (mean - current) / current

@dataclass
class EpsRevisionMomentum:
    ticker: str
    periods: list[EpsRevisionPeriod]
    targets: AnalystTargets | None
    overall_direction: Literal["strong_upgrade", "upgrade", "neutral", "downgrade", "strong_downgrade"]
    as_of_date: date
```

### 关键函数

```python
def compute_eps_revision_momentum(ticker: str) -> EpsRevisionMomentum | None:
    """从 yfinance eps_revisions 计算 EPS 修正动量."""

def _revision_direction(score: float) -> Literal[...]:
    # score > 0.5  → strong_upgrade
    # score > 0.1  → upgrade
    # score > -0.1 → neutral
    # score > -0.5 → downgrade
    # else         → strong_downgrade
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/eps_revision/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/eps_revision/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "EpsRevisionPeriod\|EpsRevisionMomentum\|compute_eps_revision_momentum" apps/stock-assistant/backend/src/quantpilot_stock/eps_revision/engine.py`

- [ ] **AC-3**: 单元测试通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_eps_revision_engine.py -v)` 退出码 0
  - 至少 12 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/eps_revision/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/eps_revision/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/eps_revision/engine.py`
- `apps/stock-assistant/backend/tests/test_eps_revision_engine.py`

> **批次开发说明**：F.6.1–F.6.3 在同一工作树批量开发并统一提交。
