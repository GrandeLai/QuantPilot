# QuantPilot

> 本地优先、LLM 原生的个人量化交易平台

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Rust](https://img.shields.io/badge/Rust-1.82-orange)](https://rust-lang.org)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)

## 项目简介

QuantPilot 是两个独立产品 + 共享基础的 monorepo。

| App | 语言 | 职责 | 端口 |
|---|---|---|---|
| apps/stock-assistant/ | Python | 股票/期权/加密的人决策交易、portfolio、screener、LLM 投顾 | 8001 (API), 5173 (workbench), 5174 (assistant) |
| apps/quant-assistant/ | Rust | 自动化量化研究：回测、参数优化、walk-forward、技术指标 | 8002 (API), 5175 (frontend) |

两个 app 互不 import 对方源码，通过 common/data-store/market.duckdb 共享行情数据。

## 仓库结构

```
apps/
├── stock-assistant/        # Python FastAPI + 双前端
│   ├── backend/
│   └── frontends/
│       ├── workbench/      # 股票工作台（5173）
│       └── assistant/      # 决策辅助 UI（5174）
│
└── quant-assistant/        # Rust axum + 研究前端
    ├── backend/
    └── frontend/           # 量化研究台（5175）

common/
├── schemas/                JSON Schema 单源 → Py/Rust/TS codegen
├── data-store/             共享 DuckDB 行情库（stock 单写）+ golden 基准
├── python/                 共享 Python 设施（config/redis/data/contracts）
└── frontend-components/    跨前端共享 TS 组件

tools/
├── ml-trainer/             ML 训练 → ONNX（Phase B+）
└── golden-generator/       跨语言行为等价基准生成
```

## 快速开始

### 环境要求

| 工具 | 版本 | 安装 |
|---|---|---|
| Python | ≥ 3.12 | 由 uv 自动管理 |
| uv | ≥ 0.11 | `brew install uv` |
| Rust | ≥ 1.75 | `brew install rust` |
| Node.js | ≥ 20 | `brew install node` |
| Redis | 任意 | `brew install redis` |

### 安装依赖

```bash
uv sync       # 所有 Python workspace members
npm install   # 所有前端 workspace（根目录运行）
```

### 启动各 App

```bash
# 股票助手（后端 + 两个前端）
./scripts/dev-stock.sh
# → http://localhost:8001 (API)
# → http://localhost:5173 (workbench)
# → http://localhost:5174 (assistant)

# 量化助手（Rust 后端 + 研究前端）
./scripts/dev-quant.sh
# → http://localhost:8002 (API)
# → http://localhost:5175 (frontend)
```

## 开发命令

### 测试

```bash
(cd common/python && uv run --group dev pytest tests/)
(cd apps/stock-assistant/backend && uv run pytest tests/)
(cd apps/quant-assistant/backend && cargo test)
```

### 前端 Build

```bash
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
(cd common/frontend-components && npm run build)
```

### Schema Codegen

```bash
bash common/schemas/codegen.sh   # 改 schema 后必跑
```

### Lint

```bash
(cd apps/stock-assistant/backend && uv run ruff check src/ tests/)
(cd apps/stock-assistant/backend && uv run mypy src/)
```

## 关键文档

| 文档 | 内容 |
|---|---|
| docs/DESIGN.md | 架构设计（两 app 结构、技术栈、路线图） |
| docs/MIGRATION.md | Phase A–E 迁移历史 + 模块归属变更 |
| docs/architecture/quant-assistant-api.md | Rust HTTP API 完整参考（5 个端点） |
| docs/architecture/frontend-routing.md | Vite proxy 路由表 |
| CLAUDE.md | Claude Code 工作指令（命令、规范、不变式） |

## 许可证

MIT License
