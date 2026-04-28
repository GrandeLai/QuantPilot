# QuantPilot 文档索引

> **最后更新**：2026-04-29
> **当前阶段**：Phase A–E 完工 + Phase F 启动（详见 [DESIGN.md §9 路线图](DESIGN.md)）

QuantPilot 是双 app + 共享基础的本地优先量化交易平台：
`apps/stock-assistant/`（Python 人决策交易）与 `apps/quant-assistant/`（Rust 量化研究）互不耦合，通过 `common/` 共享 schema、行情数据与前端组件。

---

## 入门必读

| 文档 | 内容 | 适合谁读 |
|---|---|---|
| [`/README.md`](../README.md) | 仓库总览 + 快速启动 | 第一次拉代码 |
| [`/CLAUDE.md`](../CLAUDE.md) | Claude Code 指令 + 强制不变式 | 用 Claude Code 工作的开发者 |
| [`DESIGN.md`](DESIGN.md) | 架构设计（双 app 结构、技术栈、路线图） | 全员 |
| [`MIGRATION.md`](MIGRATION.md) | 拆分 + 演进时间线（PhaseA→F） | 想理解项目演进史 |

---

## 架构与功能

| 文档 | 内容 |
|---|---|
| [`architecture/features.md`](architecture/features.md) | **功能总结** — 两 app 的能力清单（broker、策略、回测、LLM 等） |
| [`architecture/tech-stack.md`](architecture/tech-stack.md) | **技术实现** — 各层选型与关键代码位置 |
| [`architecture/quant-assistant-api.md`](architecture/quant-assistant-api.md) | **Rust HTTP API 参考**（quant-assistant，端口 8002） |
| [`architecture/stock-assistant-api.md`](architecture/stock-assistant-api.md) | **Python HTTP API 参考**（stock-assistant，端口 8001） |
| [`architecture/frontend-routing.md`](architecture/frontend-routing.md) | Vite dev proxy 路由表 + 三前端端口分配 |

---

## 工程规范

| 文档 | 内容 |
|---|---|
| [`conventions/acceptance-process.md`](conventions/acceptance-process.md) | task spec + acceptance-agent 验收工作流 |
| [`conventions/cross-language-types.md`](conventions/cross-language-types.md) | JSON Schema 单源 → Py / Rust / TS codegen 流水线 |
| [`protocols/duckdb-write-discipline.md`](protocols/duckdb-write-discipline.md) | DuckDB 写权限协议（stock 单写、quant 只读） |

---

## 任务与验收记录

| 目录 | 内容 |
|---|---|
| [`tasks/`](tasks/) | 各 Phase 的任务规格（task spec），动手前必有 |
| [`acceptance/`](acceptance/) | 各任务对应的 acceptance-agent 验收报告 |
| [`acceptance/INDEX.md`](acceptance/INDEX.md) | 验收记录时间倒序索引 |
| [`tasks/_template.md`](tasks/_template.md) | task spec 模板 |

> 协议：**没有任务规格 → 不动手**；**没有 PASS 报告 → 不合 PR**。详见 [`conventions/acceptance-process.md`](conventions/acceptance-process.md)。

---

## 学习资源

| 目录 | 内容 |
|---|---|
| [`quant_tutorial/`](quant_tutorial/) | 面向后端工程师的量化交易完整教程（金融市场基础 → 因子 → 回测 → 风控 → 执行 → 合规） |

---

## 历史 / 归档

| 目录 | 内容 |
|---|---|
| [`archive/`](archive/) | 与当前实现已不一致的历史文档（Pre-split / Phase 0–4） |
| [`superpowers/plans/`](superpowers/) | superpowers skill 产出的历史实施计划 |
| [`superpowers/specs/`](superpowers/) | superpowers skill 产出的历史设计规范 |

---

## 速查

```bash
# 启动开发环境
./scripts/dev-stock.sh    # → 8001 / 5173 / 5174
./scripts/dev-quant.sh    # → 8002 / 5175

# 跑测试
(cd common/python && uv run --group dev pytest)
(cd apps/stock-assistant/backend && uv run pytest)
(cd apps/quant-assistant/backend && cargo test)

# Schema codegen（改 schema 后必跑）
bash common/schemas/codegen.sh
```

详见 [CLAUDE.md](../CLAUDE.md)。
