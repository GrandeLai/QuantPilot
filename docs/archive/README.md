# Archive — 历史文档归档

本目录存放与当前实现已不一致、但仍保留以备追溯的文档。

> **不要在新工作中引用这里的内容**。所有 active 文档见 [`../README.md`](../README.md)。

---

## archive/legacy/ — Pre-split / Phase 0–4 时期文档

这一时期 QuantPilot 还是单体架构（`backend/` + `frontend/` + `assistant_frontend/` + `rust_core/`）。Phase A（2026-04-27）完成 monorepo 拆分后，下列文档引用的模块路径全部失效，但其中一部分（如 LLM agent 的设计思路、因子分类的概念框架）仍有参考价值。

| 文件 | 归档原因 | 替代 / 后续位置 |
|---|---|---|
| `Claude_Code_Usage_Guide.md` | Pre-split Phase 0 引导文，引用已不存在的 `T-0.1`~`T-0.4` 任务编号；当前项目通过 task spec + acceptance-agent 工作流（`docs/conventions/acceptance-process.md`）替代 | `CLAUDE.md`、`docs/conventions/acceptance-process.md` |
| `factor_guide.md` | Phase 4 时期的因子体系指南，依赖 `quantpilot.factors` / `quantpilot.ml.crypto_features` 模块——这些模块已随 `apps/quant-assistant-py/` 整体删除（Step 4，2026-04-27） | （Rust 量化端 Phase B+ 重新设计因子层时再写新版） |
| `llm-agent-layer-design.md` | Pre-split LLM agent 架构设计，路径 `quantpilot.agent` 已迁至 `quantpilot_stock.agent`；circuit breaker / fallback 思路仍有效但目录结构需重新映射 | `apps/stock-assistant/backend/src/quantpilot_stock/agent/` 源码 + 后续重写为 `docs/architecture/llm-agent.md` |
| `tab-pages-guide.md` | Pre-split 主工作台 Tab 说明，引用 `backend/src/quantpilot/`、`frontend/src/components/` 旧路径；按"研究中心 / 策略库 / 验证中心 / 运行中心 / 风险与复盘"五块切分的组织方式仍是当前 workbench 的设计依据 | `apps/stock-assistant/frontends/workbench/src/` 源码 + 后续重写为 `docs/architecture/workbench-tabs.md` |

---

## 何时清理

`docs/archive/` 的内容**不会自动清理**。如果某份文档完全失去参考价值（包括"思路价值"），可以在新 PR 中物理删除——但需要在 commit message 里说明删除理由。

`docs/superpowers/plans/` 与 `docs/superpowers/specs/` 中的历史 Phase 0–4 / pre-split 文档也属于历史文档，但由 superpowers skill 自动管理，**不要移动到这里**。
