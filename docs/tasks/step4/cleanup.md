# Task step4.cleanup: 删除 quant-assistant-py（Phase A→Step 4 完工）

**Phase**: Step 4
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 前置条件

Phase C.1–C.6 全部 PASS（已满足）：Rust quant-assistant 已实现 Rhai DSL、SMA/EMA 指标、
Walk-Forward CV、ONNX 推理、网格搜索优化、绩效报告，全量替代 quant-assistant-py 的核心能力。

### 做什么

- **删除** `apps/quant-assistant-py/` 整目录
- **删除** `scripts/dev-quant-py.sh`
- **删除** `.github/workflows/quant-assistant-py.yml`
- **更新** `pyproject.toml`：移除 `apps/quant-assistant-py/backend` workspace member
- **重新生成** `uv.lock`（`uv lock` 后自动）
- **更新** `CLAUDE.md`：
  - 移除 quant-assistant-py 相关说明
  - 更新常用命令（去掉 quant-py pytest）
  - 更新不变式说明
- **更新** `scripts/infra.sh`：移除 quant-py .env 加载路径
- **更新** `common/python/README.md`：移除"quant-assistant-py 也用此包"字样
- **更新** `common/python/quantpilot_common/__init__.py`：移除 quant-py 提及
- **更新** `apps/stock-assistant/backend/tests/test_frontend_contracts.py`：
  移除已过时的 quant-assistant-py 注释
- **更新** `apps/stock-assistant/backend/src/quantpilot_stock/api/portfolio.py`：
  移除 Phase A quant-py 注释

### 不做什么

- 不删除 `common/data-store/` 数据文件（这是共享数据，不属于 quant-py）
- 不改变 Rust quant-assistant 的任何功能（Step 4 是纯清理）
- 不删除 `apps/stock-assistant/` 中对 quant-py 能力的 try/except 包装（留着也无害）

---

## 验收标准

- [ ] **AC-1**: `apps/quant-assistant-py/` 目录不存在
- [ ] **AC-2**: `scripts/dev-quant-py.sh` 不存在
- [ ] **AC-3**: `.github/workflows/quant-assistant-py.yml` 不存在
- [ ] **AC-4**: `pyproject.toml` 不含 `quant-assistant-py` workspace member
- [ ] **AC-5**: `apps/stock-assistant/` 中无 `from quantpilot_quant` 直接 import（允许 try/except 内的 lazy import）
- [ ] **AC-6**: `common/` 中无 `from quantpilot_quant` import
- [ ] **AC-7**: `apps/stock-assistant/backend && uv run pytest tests/ -q` 全过（165 passed）
- [ ] **AC-8**: `common/python && uv run --group dev pytest tests/ -q` 全过（59 passed）
- [ ] **AC-9**: Rust `cargo test` 全过（57 tests）

---

## 测试集合

```bash
# AC-1
test ! -d apps/quant-assistant-py

# AC-2
test ! -f scripts/dev-quant-py.sh

# AC-3
test ! -f .github/workflows/quant-assistant-py.yml

# AC-4
grep -qv "quant-assistant-py" pyproject.toml

# AC-5（strict: no direct import outside try/except）
! grep -r "^from quantpilot_quant\|^import quantpilot_quant" apps/stock-assistant/

# AC-6
! grep -r "from quantpilot_quant\|import quantpilot_quant" common/

# AC-7
(cd apps/stock-assistant/backend && uv run pytest tests/ -q 2>&1 | tail -2 | grep -q "165 passed")

# AC-8
(cd common/python && uv run --group dev pytest tests/ -q 2>&1 | tail -2 | grep -q "59 passed")

# AC-9
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result" | grep -v "FAILED")
```

---

## 文件影响范围（白名单）

```
删除：
- apps/quant-assistant-py/  （整目录）
- scripts/dev-quant-py.sh
- .github/workflows/quant-assistant-py.yml

修改：
- pyproject.toml
- uv.lock（自动重生成）
- CLAUDE.md
- scripts/infra.sh
- common/python/README.md
- common/python/quantpilot_common/__init__.py
- apps/stock-assistant/backend/tests/test_frontend_contracts.py
- apps/stock-assistant/backend/src/quantpilot_stock/api/portfolio.py
- docs/tasks/step4/cleanup.md  （本文件）
```

---

## 引用

- **计划**：plan §4 "Step 4：删除 quant-assistant-py"，plan §8 "Step 4 验证"
- **前置**：phaseC.1–C.6 全部 PASS
