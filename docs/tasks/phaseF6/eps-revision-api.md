# Task phaseF6.eps-revision-api: EPS 修正动量 API 端点

**Phase**: Phase F.6
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/eps_revision.py`，注册到 `main.py`。

### 端点设计

```
GET /api/eps-revision/summary?ticker=AAPL
    → EpsRevisionMomentum (periods + targets + overall_direction)

GET /api/eps-revision/targets?ticker=AAPL
    → AnalystTargets
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/eps_revision.py`
  - `grep -q "eps_revision_router\|from.*eps_revision.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/eps_revision.py` 输出 ≥ 2

- [ ] **AC-3**: 测试通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_eps_revision_api.py -v)` 退出码 0
  - 至少 8 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/eps_revision.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/eps_revision.py`
- `apps/stock-assistant/backend/tests/test_eps_revision_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

> **批次开发说明**：F.6.1–F.6.3 在同一工作树批量开发并统一提交。
