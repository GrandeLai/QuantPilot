# Task phaseF7.token-unlock-engine: 加密 Token 解锁引擎

**Phase**: Phase F.7
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/token_unlock/` 模块。

### 数据模型

```python
@dataclass
class TokenUnlockEvent:
    protocol: str
    symbol: str
    unlock_date: date
    days_until_unlock: int          # 负值 = 已过去
    unlock_tokens: float
    unlock_usd: float | None        # 可能无法估算
    unlock_pct_circulating: float   # 占流通量百分比
    category: Literal["team", "investors", "ecosystem", "public_sale", "other"]
    sell_pressure_score: float      # 0-1（越高抛压越大）
    signal: Literal["high_risk", "moderate_risk", "low_risk", "post_unlock_rebound"]

@dataclass
class TokenUnlockCalendar:
    as_of_date: date
    events: list[TokenUnlockEvent]  # 按 unlock_date 升序
    total_events: int
    high_risk_count: int
```

### 关键函数

```python
def fetch_upcoming_unlocks(days_ahead: int = 30) -> TokenUnlockCalendar:
    """从 DefiLlama Emissions API 获取未来解锁事件."""

def compute_sell_pressure_score(
    unlock_pct_circulating: float,
    days_until_unlock: int,
    category: str,
) -> float:
    """计算抛压评分 0-1.
    
    考虑因素：
    - 解锁规模（占流通量）
    - 距解锁天数（越近越危险）
    - 解锁类别（team/investors 压力最大）
    """
```

### 抛压评分公式

```
base_score = min(1.0, unlock_pct_circulating / 10.0)  # 10% 解锁 → 满分
time_multiplier = max(0.3, 1.0 - days_until_unlock / 60)  # 越近越高
category_weight = {team: 1.0, investors: 0.9, ecosystem: 0.5, public_sale: 0.3, other: 0.4}
score = base_score * time_multiplier * category_weight[category]
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/token_unlock/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/token_unlock/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "TokenUnlockEvent\|TokenUnlockCalendar\|compute_sell_pressure_score\|fetch_upcoming_unlocks" apps/stock-assistant/backend/src/quantpilot_stock/token_unlock/engine.py`

- [ ] **AC-3**: 单元测试通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_token_unlock_engine.py -v)` 退出码 0
  - 至少 12 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/token_unlock/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/token_unlock/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/token_unlock/engine.py`
- `apps/stock-assistant/backend/tests/test_token_unlock_engine.py`

> **批次开发说明**：F.7.1–F.7.3 在同一工作树批量开发并统一提交。
