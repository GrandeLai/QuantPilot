# QuantPilot Migration: Single Backend → Stock-Assistant + Quant-Assistant + Common

记录从单一 `backend/` + `frontend/` + `assistant_frontend/` + `rust_core/` 单体架构，迁到 `apps/{stock-assistant, quant-assistant-py, quant-assistant}/` + `common/` + `tools/` 的过程。

## 时间线

- **2026-04-27**：Phase A 完工。8 个 PR（PR -1 ~ PR 7）落地。

## Phase A：仓库目录重构（完成）

### 完成的 PR

| PR | 内容 | 提交 |
|---|---|---|
| PR -1 | 验收基础设施（acceptance-agent + task specs） | `ba2c7df` |
| PR 0  | 清理预备（gitignore、未提交工作 checkpoint、死组件） | `60fb932` + `1710e2c` + `4b6b498` + `dfa3bf2` |
| PR 1  | 仓库 layout 骨架 + workspace 配置 | `28a02e3` + `c42b4be` |
| PR 2  | common/schemas/ + 三语言 codegen 流水线 | `801dbfa` + `965abdb` |
| PR 3  | common/python/ 抽出基础设施（config/redis/data/plugins/platform.{models,services}） | `eb06d9a` + `3d36072` |
| PR 4  | stock-assistant 抽出 + 契约下沉 (Stage A + B) | `c0e6ff1` + `d8d6001` + `8f7b639` |
| PR 5  | quant-assistant-py 抽出 + 删除 backend/ | `429f764` + `1cfed48` + `c294b3e` |
| PR 6  | 前端三拆 + common/frontend-components 抽出 | `38984e3` + `0afefa7` |
| PR 7  | 启动脚本 + CI workflows + 文档 | （本 PR） |

### 模块归属变更

| 旧位置 | 新位置 |
|---|---|
| `backend/src/quantpilot/config.py` | `common/python/quantpilot_common/config.py` |
| `backend/src/quantpilot/redis/` | `common/python/quantpilot_common/redis/` |
| `backend/src/quantpilot/plugins/` | `common/python/quantpilot_common/plugins/` |
| `backend/src/quantpilot/data/` | `common/python/quantpilot_common/data/` |
| `backend/src/quantpilot/platform/{models,services}.py` | `common/python/quantpilot_common/platform/` |
| `backend/src/quantpilot/strategy/base.py` 数据契约 | `common/python/quantpilot_common/contracts/{order,position,strategy}.py` |
| `backend/src/quantpilot/risk/manager.py` | `common/python/quantpilot_common/risk/manager.py` + `contracts/risk.py` |
| `backend/src/quantpilot/strategy/{storage,git_manager,loader}.py` | `common/python/quantpilot_common/strategy_persistence/` |
| `backend/src/quantpilot/backtest/metrics.py` TradeRecord | `common/python/quantpilot_common/contracts/trade.py` |
| `backend/src/quantpilot/research/{models,validation}.py` 数据契约 | `common/python/quantpilot_common/contracts/{research,validation}.py` |
| `backend/src/quantpilot/{broker,trading,paper,portfolio,sentiment,screener,options,insights,llm,agent,alerts,security}/` | `apps/stock-assistant/backend/src/quantpilot_stock/` |
| `backend/src/quantpilot/api/{trading,paper,portfolio,sentiment,screener,options,crypto,alerts,security,ws,platform,plugins,data,insights,llm}.py` | `apps/stock-assistant/backend/src/quantpilot_stock/api/` |
| `backend/src/quantpilot/{backtest,factors,ml,signals,strategy,optimize,risk,indicators,research,reports,pipeline}/` | `apps/quant-assistant-py/backend/src/quantpilot_quant/` |
| `backend/src/quantpilot/api/{backtest,factors,ml,signals,strategy,optimize,reports,pipeline,indicators,advisor,crypto_research}.py` | `apps/quant-assistant-py/backend/src/quantpilot_quant/api/` |
| `backend/src/quantpilot/platform/{advisor_service,agent_models}.py` | `apps/quant-assistant-py/backend/src/quantpilot_quant/platform/`（agent_models data → `common.contracts.agent_advice`） |
| `frontend/` | `apps/stock-assistant/frontends/workbench/` |
| `assistant_frontend/` | `apps/stock-assistant/frontends/assistant/` |
| 新建 | `apps/quant-assistant/frontend/` (skeleton) |
| `frontend/src/components/chart/` | `common/frontend-components/src/chart/`（copy；Phase B+ 真正抽出） |
| `rust_core/` | `apps/quant-assistant/backend/`（Phase B 起点种子） |

### 删除项

- 整个 `backend/` 目录（PR 5 删除，由 stock-assistant + quant-assistant-py + common 接管）
- 旧脚本 `scripts/{dev.sh, start_backend.sh, start_frontend.sh, setup.sh}`（PR 7）
- `backend/tests/test_rust_core.py`（PyO3 POC 测试，Phase B 重写）
- 5 个前端死组件 (PR 0)：AIPanel, AlertsPanel, LLMChat, PluginPanel, SystemPanel

## 端口分配（Phase A 结束后）

| 服务 | 端口 |
|---|---|
| stock-assistant 后端 | 8001 |
| stock-assistant workbench | 5173 |
| stock-assistant assistant | 5174 |
| quant-assistant-py 后端 | 8002 |
| quant-assistant frontend | 5175 |
| Redis | 6379 |

## 当前测试规模

- common: 59 passed
- stock-assistant: 163 passed, 2 skipped
- quant-assistant-py: 276 passed
- **总计**: 498 passed + 2 skipped + Rust cargo check（绿）

## 已知遗留 / 后续清理

1. `backend/src/quantpilot/strategy/base.py` 等 re-export shim 已在 PR 5 后无引用；可清理（已删除随 backend/ 一起）
2. `apps/quant-assistant/frontend/` 是 skeleton；Phase B+ 时实际 wire-up 研究面板
3. `common/frontend-components/src/chart/` 是 workbench chart 的 copy；Phase B+ 真抽
4. stock 侧 2 个 skip 测试（test_frontend_contracts 中的 `test_api_aliases_are_available` + `test_available_strategies_include_user_strategies`）：依赖 quant-py 后端，需要端到端集成测试场地恢复

## Phase B 起步

- `apps/quant-assistant/backend/`：Phase A 已含 Rust seed (MA crossover PyO3 binding)
- Phase B MVP：转 axum + Polars + duckdb-rs，实现 `/healthz` + `/backtest` 端点
- 验证：与 `quant-assistant-py` 同 OHLCV 输入回测，结果偏差 < 1e-9（goldens dataset）
- Phase C：增量替换 quant-py 各模块（Rhai DSL + 因子库 + walk-forward + ONNX 推理 + ...）
- Step 4：删除 `apps/quant-assistant-py/`
