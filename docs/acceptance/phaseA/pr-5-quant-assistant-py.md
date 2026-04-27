# Acceptance Report: phaseA.pr-5-quant-assistant-py

**Run at**: 2026-04-27T17:00:00Z
**Implementation PRs/commits**:
- `429f764` — refactor(quant-py): extract quant modules to apps/quant-assistant-py/ + delete backend/ (main PR 5)
- `1cfed48` — chore: untrack catboost training artifacts (gitignore followup)
**Diff range**: `8f7b639..1cfed48`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS**

---

## 文件影响范围检查

PR 5 改动 121 + 5 = 126 文件：

**主 commit `429f764`**：
- 新增：`apps/quant-assistant-py/backend/{pyproject.toml, README.md, src/quantpilot_quant/, tests/conftest.py}`
- 移动（git rename）：11 quant 模块、11 quant API 路由、3 platform 文件、24+ 测试文件
- 删除：整个 `backend/` 目录（pyproject、cli、main、__init__、所有 stub 文件）
- 删除：`backend/tests/test_rust_core.py`（POC 代码，模块已重命名）
- 修改：根 `pyproject.toml`（workspace member 加入 quant-py）

**Followup commit `1cfed48`**：
- `.gitignore`：`**/catboost_info/` 全局忽略
- 取消跟踪 4 个误入的 catboost training 文件

无超出白名单改动。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `apps/quant-assistant-py/backend/pyproject.toml` 存在，name = quantpilot-quant | ✅ PASS | grep 命中 |
| AC-2: `quant_assistant/main.py` 存在并导出 FastAPI app | ✅ PASS | uv import 成功；app 注册 11 quant 路由 |
| AC-3: 11 个 quant 模块都在 quant-py 下 | ✅ PASS | backtest, factors, ml, signals, strategy, optimize, risk, indicators, research, reports, pipeline 全部 ls 通过；含 platform/ |
| AC-4: 顶层 `backend/` 目录已**完全删除** | ✅ PASS | `! test -e backend` 通过 |
| AC-5: quant-assistant-py pytest 全过 | ✅ PASS | **276 passed in 21.50s** |
| AC-6: quant-py 不 import quantpilot_stock | ✅ PASS | grep 0 命中 |
| AC-7: stock-assistant 仍跑通 | ✅ PASS | **163 passed, 2 skipped**（不变）|
| AC-8: 根 pyproject.toml 不再含 backend/ | ✅ PASS | grep 0 命中；workspace members 现为 [common/python, apps/stock-assistant/backend, apps/quant-assistant-py/backend] |

---

## 测试执行日志摘要

```
=== common ===                          59 passed in 8.41s
=== stock-assistant ===                163 passed, 2 skipped in 16.61s
=== quant-assistant-py ===             276 passed, 3 warnings in 21.50s

=== isolation grep ===
  ✓ stock not importing quant
  ✓ quant not importing stock
  ✓ common not importing apps

Total active: 498 passed + 2 skipped = 500
Original 505 - 5 (deleted test_rust_core POC) = 500 ✓
```

---

## 代码 Review 备注

非阻塞性观察：

1. **PR 5 实际是 2 个 commit**：`429f764`（主迁移）+ `1cfed48`（catboost gitignore followup）。catboost training 产物在新位置 `apps/quant-assistant-py/backend/catboost_info/` 误入 commit，由 `**/catboost_info/` 通配修复。

2. **删除的测试文件**：
   - `test_rust_core.py`（5 个测试）：测的是已重命名的 PyO3 模块 `quantpilot_core`（现 `quantpilot_quant`），且当前 Phase A 不构建 maturin extension。Phase B Rust 量化助手起步时会有自己的测试。

3. **advisor + crypto_research 路由迁到 quant-py**（域名不匹配但务实）：
   - 这两个路由从用户视角是"投顾建议"，应属 stock-assistant 域
   - 但实现重度依赖 `CryptoResearchService` + `research/` 模块（quant-py 内）
   - 按用户在 PR 4 中确认的"A: 共享契约下沉到 common"原则，且这两个 service 是有行为且依赖更深的模块，下沉到 common 不合适
   - 妥协：advisor + agent_models + advisor_service 全部进 quant-py 域；后续 Phase B/C Rust quant 上线时通过 HTTP API 把 advisor 迁回 stock 域（前端总能调）
   - `agent_models.py` 的 contracts 部分（AdviceCard、AdviceEvidence）已在 PR 4 时下沉到 `common.contracts.agent_advice`；quant-py 这里只是行为类（advisor_service.py）的归属

4. **stock-assistant 的 2 个 skip 测试未恢复**：
   - `test_api_aliases_are_available`、`test_available_strategies_include_user_strategies`
   - 它们测的 `/api/signals/feed`、`load_strategy_class` 在 quant-py 后端，stock TestClient 测不到
   - 真正恢复需要：(a) 端到端集成测试启两个进程；或 (b) PR 7 时拆出共享契约测试到独立场地
   - 留 skip 标注，PR 6 / PR 7 时再决定

5. **uv.lock + 依赖重型化**：quant-py 依赖闭包含 sklearn、xgboost、lightgbm、catboost、cvxpy、optuna、statsmodels — 这些都是 ML 训练/优化需要的，stock-assistant 不必装。`uv sync` 总规模上升，但每个 app 的 .venv 隔离没问题。

6. **conftest.py**：stock 与 quant-py 各自维护独立 conftest；前者 reset stock-side broker/trading singletons，后者只 reset common.data 单例。

---

## 后续动作

- ✅ 本 PR 可视为已合并
- 更新 `docs/acceptance/INDEX.md`
- 下一步 PR 6（前端三拆 + common/frontend-components 抽出）
- 之后 PR 7（启动脚本 + CI + 文档）
- Phase A 完工后即可进入 Phase B（Rust quant MVP）

## Phase A 完工接近

PR -1 → PR 5 已完成 6 个 PR，剩 PR 6 + PR 7。Phase A "目标终态目录结构" 的后端部分**已经实现**：

```
QuantPilot/
├── apps/
│   ├── stock-assistant/backend/      ✅ Python，14 路由，163 测试
│   └── quant-assistant-py/backend/   ✅ Python 临时态，11 路由，276 测试
│   └── quant-assistant/backend/      ✅ Rust seed (PR 1 移入)
├── common/
│   ├── schemas/                       ✅ JSON Schema + codegen
│   ├── python/                        ✅ 共享设施 + 契约 + schemas + risk + strategy_persistence
│   ├── data-store/                    ✅ 目录预留
│   └── frontend-components/           ⏳ PR 6
├── tools/                             ⏳ 目录预留，PR 7 起骨架
└── archive/                           ⏳ 预留
```

剩下的是前端 + 工具脚本 + 文档收尾。
