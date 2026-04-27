# Task phaseA.pr-4-stock-assistant: 股票助手抽出

**Phase**: A
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 创建 `apps/stock-assistant/backend/`，含：
  - `pyproject.toml`：`[project.name = "quantpilot-stock"]`，依赖 `quantpilot-common`、FastAPI、broker SDK 等
  - `src/quantpilot_stock/__init__.py`、`main.py`（FastAPI app 入口；从原 `backend/src/quantpilot/main.py` 拆出股票相关路由部分）
- 移动"人决策"模块（详见 plan §1 归属表）：
  - `backend/src/quantpilot/api/{trading,paper,portfolio,advisor,insights,sentiment,screener,options,crypto,crypto_research,alerts,llm,security,ws,platform,plugins,data}.py` → `apps/stock-assistant/backend/src/quantpilot_stock/api/`（注：`platform`、`plugins` 的 API 路由层留在这里，对应业务模块已在 PR 3 进 common）
  - `backend/src/quantpilot/{broker,trading,portfolio,sentiment,screener,options,insights,llm,agent,alerts,security}/` → `apps/stock-assistant/backend/src/quantpilot_stock/`
- 替换 import：`from quantpilot.xxx` → `from quantpilot_stock.xxx`（业务模块）或 `from quantpilot_common.xxx`（基础设施）
- 移动对应 tests 到 `apps/stock-assistant/backend/tests/`
- 在根 `pyproject.toml` uv workspace members 加入 `apps/stock-assistant/backend`

### 不做什么
- 不动 quant 模块（backtest/factors/ml 等，PR 5）
- 不重构业务模块内部逻辑——只搬+改 import
- 不动前端
- 不写新启动脚本（PR 7）

---

## 验收标准

- [ ] **AC-1**: `apps/stock-assistant/backend/pyproject.toml` 存在，`name = "quantpilot-stock"`
- [ ] **AC-2**: `apps/stock-assistant/backend/src/quantpilot_stock/main.py` 存在并导出 FastAPI app
- [ ] **AC-3**: 以下模块都已在 `apps/stock-assistant/backend/src/quantpilot_stock/` 下：`broker/`、`trading/`、`portfolio/`、`sentiment/`、`screener/`、`options/`、`insights/`、`llm/`、`agent/`、`alerts/`、`security/`、`api/`（API 路由模块）
- [ ] **AC-4**: 这些模块在 `backend/src/quantpilot/` 下已不存在
- [ ] **AC-5**: `cd apps/stock-assistant/backend && uv run pytest tests/ -x` 全过
- [ ] **AC-6**: `apps/stock-assistant/` 不 import `apps/quant-assistant/` 任何东西：`! grep -rE "from quantpilot_quant|import quantpilot_quant" apps/stock-assistant/`
- [ ] **AC-7**: 现有 `backend/` 仍能跑 `uv run pytest`（这一步 backend/ 还没空，留下了 quant 模块；保证 quant 部分仍能跑）

---

## 测试集合

```bash
# AC-1
test -f apps/stock-assistant/backend/pyproject.toml
grep -q 'name = "quantpilot-stock"' apps/stock-assistant/backend/pyproject.toml

# AC-2
test -f apps/stock-assistant/backend/src/quantpilot_stock/main.py
python3 -c "import sys; sys.path.insert(0, 'apps/stock-assistant/backend/src'); from quantpilot_stock.main import app"

# AC-3
for m in broker trading portfolio sentiment screener options insights llm agent alerts security api; do
  test -d "apps/stock-assistant/backend/src/quantpilot_stock/$m" || (echo "MISSING: $m" && exit 1)
done

# AC-4
for m in broker trading portfolio sentiment screener options insights llm agent alerts security; do
  test -e "backend/src/quantpilot/$m" && echo "STILL THERE: $m" && exit 1
done
echo "OK: removed from backend/"

# AC-5
cd apps/stock-assistant/backend && uv run pytest tests/ -x
cd ../../..

# AC-6
! grep -rE "from quantpilot_quant|import quantpilot_quant" apps/stock-assistant/

# AC-7
cd backend && uv run pytest tests/ -x
cd ..
```

---

## 文件影响范围（白名单）

```
- apps/stock-assistant/backend/**
- backend/src/quantpilot/{broker,trading,portfolio,sentiment,screener,options,insights,llm,agent,alerts,security,api}/** (移动到 apps/stock-assistant)
- backend/src/quantpilot/main.py (拆分；股票部分迁出)
- backend/tests/test_{trading,paper,portfolio,advisor,insights,sentiment,screener,options,crypto,crypto_research,alerts,llm,agent,security,broker}*.py (移动)
- pyproject.toml (顶层；添加 workspace member)
```

---

## 引用

- **设计来源**：plan §1 模块归属表、§4 PR 4
- **上游依赖**：phaseA.pr-3-common-py
- **下游依赖**：phaseA.pr-5-quant-assistant-py
