# CLAUDE.md — Claude Code 项目指令文件

## 项目简介

QuantPilot — 本地优先的个人量化交易平台。**Phase A 已完成仓库拆分**，现在是三 app + 共享包的 monorepo：

```
apps/
├── stock-assistant/       # Python: 股票/期权/加密的人决策交易（端口 8001）
├── quant-assistant-py/    # Python 临时态: 自动化研究 + 规则化执行（端口 8002，Step 4 删除）
└── quant-assistant/       # Rust: Phase B+ 替代 quant-assistant-py
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

- `apps/stock-assistant/` 与 `apps/quant-assistant*/` **互不 import 对方源码**
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

# 量化助手 Python 临时态
./scripts/dev-quant-py.sh
# → http://localhost:8002 (API)
# → http://localhost:5175 (research frontend)

# 量化助手 Rust（Phase B+ 起真正可用，Phase A 占位）
./scripts/dev-quant.sh
```

### 测试

```bash
# 三个独立测试套件
(cd common/python && uv run --group dev pytest tests/)
(cd apps/stock-assistant/backend && uv run pytest tests/)
(cd apps/quant-assistant-py/backend && uv run pytest tests/)

# Rust check
(cd apps/quant-assistant/backend && cargo check)
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

### Lint / 类型检查

```bash
(cd apps/stock-assistant/backend && uv run ruff check src/ tests/)
(cd apps/stock-assistant/backend && uv run mypy src/)
(cd apps/stock-assistant/backend && uv run ruff format src/ tests/)

# quant-py / common 同形
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
