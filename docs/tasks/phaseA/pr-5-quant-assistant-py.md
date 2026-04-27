# Task phaseA.pr-5-quant-assistant-py: 量化助手 Python 临时态抽出

**Phase**: A
**Status**: passed
**Implementation PR**: commits `429f764` + `1cfed48`
**Acceptance**: [docs/acceptance/phaseA/pr-5-quant-assistant-py.md](../../acceptance/phaseA/pr-5-quant-assistant-py.md) — ✅ PASS (2026-04-27)
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 创建 `apps/quant-assistant-py/backend/`，含：
  - `pyproject.toml`：`[project.name = "quantpilot-quant"]`，依赖 `quantpilot-common`、FastAPI、scikit-learn、pandas-ta 等
  - `src/quantpilot_quant/__init__.py`、`main.py`（FastAPI app 入口；从原 `backend/src/quantpilot/main.py` 拆出量化部分）
- 移动量化模块（详见 plan §1 归属表）：
  - `backend/src/quantpilot/api/{backtest,factors,ml,signals,strategy,optimize,reports,pipeline,indicators}.py` → `apps/quant-assistant-py/backend/src/quantpilot_quant/api/`
  - `backend/src/quantpilot/{backtest,factors,ml,signals,strategy,optimize,risk,indicators,research}/` → `apps/quant-assistant-py/backend/src/quantpilot_quant/`
- 替换 import
- 移动对应 tests 到 `apps/quant-assistant-py/backend/tests/`
- **删除已为空的 `backend/`** 顶层目录（应只剩根 `__init__.py`）
- 在根 `pyproject.toml` uv workspace members 加入 `apps/quant-assistant-py/backend`，**移除** 已不存在的 `backend/` 旧 member（如有）

### 不做什么
- 不动前端
- 不写新启动脚本
- 不动 stock-assistant
- 不重构内部逻辑——只搬+改 import

---

## 验收标准

- [ ] **AC-1**: `apps/quant-assistant-py/backend/pyproject.toml` 存在，`name = "quantpilot-quant"`
- [ ] **AC-2**: `apps/quant-assistant-py/backend/src/quantpilot_quant/main.py` 存在并导出 FastAPI app
- [ ] **AC-3**: 以下模块都已在 `apps/quant-assistant-py/backend/src/quantpilot_quant/`：`backtest/`、`factors/`、`ml/`、`signals/`、`strategy/`、`optimize/`、`risk/`、`indicators/`、`research/`、`api/`
- [ ] **AC-4**: 顶层 `backend/` 目录已**完全删除**（不只是 src/quantpilot 为空，整个 backend/ 移除）
- [ ] **AC-5**: `cd apps/quant-assistant-py/backend && uv run pytest tests/ -x` 全过
- [ ] **AC-6**: `apps/quant-assistant-py/` 不 import `apps/stock-assistant/` 任何东西：`! grep -rE "from quantpilot_stock|import quantpilot_stock" apps/quant-assistant-py/`
- [ ] **AC-7**: `apps/stock-assistant/` 仍跑通：`cd apps/stock-assistant/backend && uv run pytest tests/ -x`
- [ ] **AC-8**: 根 `pyproject.toml` 不再含已删除的 backend/ 作为 workspace member

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant-py/backend/pyproject.toml
grep -q 'name = "quantpilot-quant"' apps/quant-assistant-py/backend/pyproject.toml

# AC-2
test -f apps/quant-assistant-py/backend/src/quantpilot_quant/main.py
python3 -c "import sys; sys.path.insert(0, 'apps/quant-assistant-py/backend/src'); from quantpilot_quant.main import app"

# AC-3
for m in backtest factors ml signals strategy optimize risk indicators research api; do
  test -d "apps/quant-assistant-py/backend/src/quantpilot_quant/$m" || (echo "MISSING: $m" && exit 1)
done

# AC-4
! test -e backend
echo "OK: backend/ removed"

# AC-5
cd apps/quant-assistant-py/backend && uv run pytest tests/ -x
cd ../../..

# AC-6
! grep -rE "from quantpilot_stock|import quantpilot_stock" apps/quant-assistant-py/

# AC-7
cd apps/stock-assistant/backend && uv run pytest tests/ -x
cd ../../..

# AC-8
! grep -E '"backend"|backend/backend' pyproject.toml
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant-py/backend/**
- backend/** (整体删除；本 PR 完成后顶层无此目录)
- pyproject.toml (顶层；workspace members 调整)
```

---

## 引用

- **设计来源**：plan §1 模块归属表、§4 PR 5
- **上游依赖**：phaseA.pr-4-stock-assistant
- **下游依赖**：phaseA.pr-6-frontend-split
