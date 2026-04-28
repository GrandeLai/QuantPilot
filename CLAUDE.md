# CLAUDE.md — Claude Code 项目指令文件

## 项目简介

QuantPilot — 本地优先的个人量化交易平台。**Phase A+C 已完成**，现在是两 app + 共享包的 monorepo：

```
apps/
├── stock-assistant/       # Python: 股票/期权/加密的人决策交易（端口 8001）
└── quant-assistant/       # Rust: 自动化研究 + 规则化执行（端口 8002）
common/                    # 共享：schemas / 数据 / 共享 Python 设施 / 共享前端组件
tools/                     # ml-trainer (Phase B+) / golden-generator
```

## 核心参考文档

- **拆分计划**：`/Users/bytedance/.claude/plans/python-rust-common-wiggly-river.md`（已批准）
- **迁移记录**：`docs/MIGRATION.md`（Phase A 完工状态）
- **协议**：`docs/protocols/duckdb-write-discipline.md`、`docs/conventions/cross-language-types.md`
- **历史设计**：`docs/DESIGN.md`（旧版，反映拆分前结构；待 Phase B 时整体重写）

## 验收流程（**强制**）

每个 PR/任务在动手前必须先有 task spec + 走验收流程：

1. **Task spec**：`docs/tasks/<phase>/<task-id>.md`，含验收标准（AC）、测试集合、文件白名单
2. **实现**：commit message 末尾加 `Refs: docs/tasks/<phase>/<task-id>.md`
3. **验收**：调用 `acceptance-agent`（`.claude/agents/acceptance-agent.md`），跑 AC 测试，写 `docs/acceptance/<phase>/<task-id>.md` 报告
4. **合 PR 条件**：报告 verdict = ✅ PASS

详见 `docs/conventions/acceptance-process.md`。

## 不变式（**强制**）

- `apps/stock-assistant/` 与 `apps/quant-assistant/` **互不 import 对方源码**
- `common/` 不反向 import `apps/*`
- 跨语言类型只能在 `common/schemas/*.schema.json` 定义；其他位置的类型由 `common/schemas/codegen.sh` 生成
- `common/data-store/market.duckdb` 仅 stock-assistant 可写；其他 read-only

## 常用命令

### 启动开发环境

```bash
# 股票助手全栈（推荐主开发模式）
./scripts/dev-stock.sh
# → http://localhost:8001 (API)
# → http://localhost:5173 (workbench)
# → http://localhost:5174 (assistant)

# 量化助手 Rust
./scripts/dev-quant.sh
# → http://localhost:8002 (API)
# → http://localhost:5175 (research frontend)
```

### 测试

```bash
# Python 测试套件
(cd common/python && uv run --group dev pytest tests/)
(cd apps/stock-assistant/backend && uv run pytest tests/)

# Rust 测试（含 golden 集）
(cd apps/quant-assistant/backend && cargo test)
```

### 前端 build

```bash
npm install   # 仅根目录跑一次（npm workspace 装所有前端依赖）
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
(cd common/frontend-components && npm run build)
```

### Schema codegen

```bash
bash common/schemas/codegen.sh   # 改 schema 后必跑
```

### Quant-Assistant API 端点（Rust, port 8002）

```
GET  /healthz
POST /api/backtest/run      # MA crossover 回测（bars + fast/slow period）
POST /api/walk-forward      # Walk-forward 验证窗口切分
POST /api/optimize          # 网格搜索最优参数（top-N by Sharpe）
POST /api/indicators        # SMA / EMA 指标计算
POST /api/ml/predict        # ONNX 模型推理（model_id + features）
```

详细 request/response schema 见 `docs/architecture/quant-assistant-api.md`。

### Lint / 类型检查

```bash
(cd apps/stock-assistant/backend && uv run ruff check src/ tests/)
(cd apps/stock-assistant/backend && uv run mypy src/)
(cd apps/stock-assistant/backend && uv run ruff format src/ tests/)

# common 同形
(cd common/python && uv run ruff check quantpilot_common/ tests/)
```

## 编码规范

- Python: type hints、ruff、loguru、async-first、Pydantic v2
- Rust: clippy、doc comments、PyO3（如还需要 binding）
- TypeScript: strict mode、函数组件、Zustand
- Git: Conventional Commits 格式（`feat:`、`fix:`、`refactor:`、`chore:`、`docs:` 等）

## 关键约束

- **不要** 跳过测试编写
- **不要** 忽略验收标准
- **不要** 跨 app import 源码（违反者，acceptance-agent 给 FAIL）
- **不要** 手改 codegen 生成产物（在 common/python/.../schemas/、apps/quant-assistant/.../schemas/、common/frontend-components/src/types/ 之下的内容）
- **不要** 让 Rust quant 写 `common/data-store/market.duckdb`
- 如果某个任务的验收标准不清晰，先问用户再动手

## Plan 文件

`/Users/bytedance/.claude/plans/python-rust-common-wiggly-river.md` 是 Phase A-D 的总体路线图。改动 Phase 范围或决策时同步更新此文件。
