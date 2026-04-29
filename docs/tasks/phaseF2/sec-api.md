# Task phaseF2.sec-api: SEC 事件流 API 端点

**Phase**: Phase F.2
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py`，注册到 `main.py`。

### 端点设计

```
GET /api/sec/8k/recent?ticker=AAPL&max_count=3
    → 最近 3 份 8-K 及其 item-level 解析

GET /api/sec/8k/diff?ticker=AAPL
    → 最新两份 8-K 的差分结果（EightKDiff）

GET /api/sec/form4/signals?ticker=AAPL&days=90
    → 过去 N 天的 Form 4 集群信号列表

GET /api/sec/summary?ticker=AAPL
    → 三类数据的摘要合并（供前端一次拿全）
```

### 错误处理

- 网络超时（EDGAR 请求 > 15s）→ 503
- ticker 不存在 → 404
- EDGAR 限速 → 429，携带 Retry-After: 11

### 响应结构（summary 端点）

```json
{
  "ticker": "AAPL",
  "generated_at": "2026-04-29T12:00:00Z",
  "latest_8k": {
    "filed_date": "...",
    "accession_number": "...",
    "items": [{"item_number": "5.02", "item_title": "...", "text_snippet": "..."}]
  },
  "8k_diff": {
    "has_material_change": true,
    "overall_change_score": 0.65,
    "changed_items": ["5.02"]
  },
  "insider_clusters": [
    {
      "window_start": "...", "window_end": "...",
      "insider_count": 3, "total_value": 2500000,
      "signal_strength": 0.72, "key_roles": ["CEO", "CFO"]
    }
  ]
}
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py`
  - `grep -q "sec_router\|sec\.router\|from.*sec.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 四个端点存在
  - `grep -c "@router.get" apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py` 输出 ≥ 4

- [ ] **AC-3**: 错误处理（503/404/429）
  - `grep -q "503\|HTTPException\|404" apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py`

- [ ] **AC-4**: 单元测试通过（mock edgar client）
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_sec_api.py -v)` 退出码 0
  - 至少 10 个测试（四端点 happy path + 404 + 503 + api alias）

- [ ] **AC-5**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/sec.py)` 退出码 0

---

## 文件影响范围

新建（本任务核心文件）：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py`
- `apps/stock-assistant/backend/tests/test_sec_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`（注册 sec_router）

依赖（由 F.2.1–F.2.3 提供，批次共同提交）：
- `edgar/__init__.py`、`edgar/models.py`、`edgar/client.py`（F.2.1）
- `edgar/diff_engine.py`（F.2.2）
- `edgar/form4_engine.py`（F.2.3）
- `pyproject.toml`（rapidfuzz 依赖在 F.2.1 中添加）
