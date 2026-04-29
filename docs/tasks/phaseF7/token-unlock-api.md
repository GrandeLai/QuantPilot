# Task phaseF7.token-unlock-api: Token 解锁 API 端点

**Phase**: Phase F.7
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/token_unlock.py`，注册到 `main.py`。

### 端点设计

```
GET /api/token-unlocks/upcoming?days=30
    → TokenUnlockCalendar

GET /api/token-unlocks/by-symbol?symbol=ARB
    → list[TokenUnlockEvent]  (过滤特定代币)

GET /api/token-unlocks/high-risk
    → list[TokenUnlockEvent]  (sell_pressure_score >= 0.6)
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/token_unlock.py`
  - `grep -q "token_unlock_router\|from.*token_unlock.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/token_unlock.py` 输出 ≥ 3

- [ ] **AC-3**: 测试通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_token_unlock_api.py -v)` 退出码 0
  - 至少 8 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/token_unlock.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/token_unlock.py`
- `apps/stock-assistant/backend/tests/test_token_unlock_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

> **批次开发说明**：F.7.1–F.7.3 在同一工作树批量开发并统一提交。
