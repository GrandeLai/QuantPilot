# QuantPilot — 设计文档

> **文档版本**：v0.4.2
> **最后更新**：2026-05-08（移除本地模拟盘，回测收敛为实盘前验证）
> **作者**：赖俊金
> **状态**：Active

> **相关文档**：
> - `docs/MIGRATION.md` — Phase A 8 PR 完工状态与模块归属
> - `docs/architecture/quant-assistant-api.md` — Rust API 详细规范
> - `docs/architecture/frontend-routing.md` — 前端路由设计
> - `docs/protocols/duckdb-write-discipline.md` — DuckDB 写权限协议
> - `docs/conventions/cross-language-types.md` — 跨语言类型规范
> - `docs/conventions/acceptance-process.md` — 验收流程规范

---

## 更新日志（Changelog）

| 版本 | 日期 | 更新内容 |
|---|---|---|
| v0.1.0 | 2026-04-07 | 初始版本 |
| v0.2.0 | 2026-04-27 | Phase A 拆分完成；双产品 + 共享包结构 |
| v0.3.0 | 2026-04-28 | Phase A–E 完工；Rust 量化后端全 API + 前端接线；删除 Python 量化临时后端 |
| v0.4.0 | 2026-04-28 | A1–A3 + B1：equity curve 图表、Walk-Forward 面板、/api/ml/predict 端点、ApiError DRY |
| v0.4.1 | 2026-05-07 | G1：双产品共享市场宇宙；量化投资与股票投资助手均支持美股、ETF、港股、A 股与 OKX 加密标的 |
| v0.4.2 | 2026-05-08 | 移除 stock-assistant 本地模拟盘 `/api/paper` 与自定义撮合引擎；回测统一定位为 stock-assistant 与 quant-assistant 共用的实盘前验证测试 |

---

## 1. 项目概述

**Vision**：本地优先、证据驱动的个人量化交易平台。

**当前状态**：Phase A–E + G1 + G2 完工 — stock-assistant（Python，生产就绪）+ quant-assistant（Rust，核心 API 全通）+ 双产品共享市场宇宙 + 通用实盘前回测验证。

---

## 2. 架构总览

```
QuantPilot Monorepo
├── apps/
│   ├── stock-assistant/   (Python, 8001 / 5173 / 5174)
│   └── quant-assistant/   (Rust, 8002 / 5175)
├── common/
│   ├── schemas/            → three-language codegen
│   ├── data-store/         → DuckDB + golden
│   ├── python/quantpilot_common/
│   └── frontend-components/
└── tools/
    ├── ml-trainer/          (Phase B+)
    └── golden-generator/
```

### 端口分配

| 端口 | 服务 | 说明 |
|---|---|---|
| 8001 | stock-assistant backend | Python FastAPI |
| 5173 | stock-assistant workbench | Vite dev / build |
| 5174 | stock-assistant assistant | Vite dev / build |
| 8002 | quant-assistant backend | Rust axum |
| 5175 | quant-assistant frontend | Vite dev / build |
| 6379 | Redis | 实时行情缓存 |

---

## 3. 两应用职责划分

### stock-assistant（股票投资助手，Python）

- **定位**：人参与决策的交易工作流
- **功能**：Longbridge / FuTu / OKX broker 接入，交易执行，broker 账户持仓管理，选股，情绪分析，结构化投顾，实盘前回测验证入口
- **支持资产**：美股 / ETF / 港股 / A 股 / 期权 / OKX 加密现货与衍生品
- **市场数据写入方**：yfinance / akshare / OKX → `common/data-store/market.duckdb`
- **不做**：自动化量化研究，ML 训练，无人值守执行
- **已移除**：本地模拟盘产品功能（`quantpilot_stock.paper`、`/api/paper`、自定义撮合 engine、模拟策略槽位）。Broker sandbox/testnet 仅作为交易通道安全模式保留，不作为独立产品入口。

### quant-assistant（量化投资，Rust）

- **定位**：自动化量化研究 + 规则化计算
- **HTTP 端点**（5 个）：
  - `GET  /healthz`
  - `POST /api/backtest/run`
  - `POST /api/walk-forward`
  - `POST /api/optimize`
  - `POST /api/indicators`
- **支持资产**：美股 / ETF / 港股 / A 股 / OKX 加密现货与衍生品（从 stock-assistant 数据层获取 K 线后计算）
- **市场数据只读方**：读 `market.duckdb` 或通过 stock-assistant 的 `/api/data/*` 获取
- **不做**：broker 接入，LLM 调用，人决策界面

### 通用实盘前回测验证

- **定位**：回测不是独立玩具功能，而是任何策略或信号进入交易执行前的验证测试。
- **计算归属**：`quant-assistant` 的 Rust `POST /api/backtest/run` 是唯一回测计算 owner。
- **使用方式**：`stock-assistant` 前端通过 HTTP/proxy 调用回测 API；不得 import `apps/quant-assistant/` 源码。
- **共享契约**：`common/schemas/backtest_config.schema.json` 与 `common/schemas/backtest_result.schema.json` 作为跨产品结果契约。
- **覆盖资产**：美股 / ETF / 港股 / A 股 / OKX 加密均可进入相同验证链路。

### 共享市场宇宙

- **Task**：`docs/tasks/phaseG/dual-product-market-universe.md` — [x] completed
- **后端契约**：`common/python/quantpilot_common/data/universe.py`
- **前端契约**：`common/frontend-components/src/markets.ts`
- **API**：`GET /data/universe` 与 `GET /api/data/universe`
- **默认数据源**：美股 / ETF / 港股走 `yfinance`，A 股走 `akshare`，OKX 加密走 `auto` 并由 stock-assistant 归一化到 OKX 格式。

---

## 4. 关键不变式（强制）

1. `apps/stock-assistant/` **不得** import `apps/quant-assistant/` 源码。CI 通过 grep 检查。
2. `apps/quant-assistant/` **不得** import `apps/stock-assistant/` 源码。CI 通过 grep 检查。
3. `common/` **不反向 import** `apps/*`。CI 通过 grep 检查。
4. 跨语言类型**只能**在 `common/schemas/*.schema.json` 定义；其他位置由 `codegen.sh` 生成。
5. `common/data-store/market.duckdb` **仅 apps/stock-assistant 可写**；其他进程 read-only。CI 通过 grep 检查。

---

## 5. 技术栈

### stock-assistant（Python）

FastAPI，Polars，LiteLLM，pytest，ruff / mypy

### quant-assistant（Rust）

axum + tokio，polars，duckdb-rs，serde + serde_json，anyhow + thiserror，tracing

### 共享前端

React 18 + TypeScript，Zustand，TradingView Lightweight Charts，Tailwind CSS v4，Vite 6

### 数据层

| 存储 | 用途 |
|---|---|
| DuckDB | 历史行情（market.duckdb）、回测结果 |
| Redis | 实时行情缓存（端口 6379） |
| SQLite | 配置、审计日志 |
| Parquet | 归档数据 |

---

## 6. Schema Codegen 流水线

```
common/schemas/*.schema.json  （源，手写）
    ├──► datamodel-codegen   → common/python/quantpilot_common/schemas/*.py
    ├──► typify              → apps/quant-assistant/backend/src/schemas/
    └──► json-schema-to-ts   → common/frontend-components/src/types/
```

生成产物全部提交入库；CI 通过 `codegen.sh + git diff --exit-code` 检测漂移。

---

## 7. DuckDB 写权限协议（摘要）

| 角色 | market.duckdb | 自有 db |
|---|---|---|
| stock-assistant | 读 + 写 | — |
| quant-assistant | read-only | `apps/quant-assistant/data/results.duckdb`（预留） |
| golden-generator | 不动 | `common/data-store/golden/` |
| ml-trainer | read-only | `common/data-store/models/` |

完整协议见 `docs/protocols/duckdb-write-discipline.md`。

---

## 8. 验收流程（摘要）

1. **Task spec**：`docs/tasks/<phase>/<task-id>.md`，含验收标准（AC）、测试集合、文件白名单
2. **实现**：commit message 末尾加 `Refs: docs/tasks/<phase>/<task-id>.md`
3. **acceptance-agent**：跑 AC 测试，写 `docs/acceptance/<phase>/<task-id>.md` 报告
4. **合并条件**：报告 verdict = ✅ PASS

完整规范见 `docs/conventions/acceptance-process.md`。

---

## 9. 路线图（当前状态）

| Phase | 状态 | 摘要 |
|---|---|---|
| A | ✅ 2026-04-27 | Monorepo 拆分（8 PR），500 测试，3 app 互不耦合 |
| Step 4 | ✅ 2026-04-27 | 删除 Python 量化临时后端（见 MIGRATION.md） |
| B | ✅ 含于 Phase A–E | Rust MVP：axum + Polars backtest |
| C | ✅ (Phase D) | Walk-forward / optimize / indicators API |
| D | ✅ 2026-04-28 | src/api/ 模块化 + trade tracking |
| E | ✅ 2026-04-28 | 前端 wire-up（BacktestPanel + OptimizationPanel） |
| A1 | ✅ 2026-04-28 | BacktestPanel 权益曲线折线图（纯 SVG） |
| A2 | ✅ 2026-04-28 | Walk-Forward 验证面板（第三 Tab） |
| A3 | ✅ 2026-04-28 | POST /api/ml/predict ONNX 推理端点 |
| B1 | ✅ 2026-04-28 | 提取共享 ApiError 到 api/mod.rs（DRY） |
| B4 | ✅ 2026-04-28 | mypy 类型覆盖：common/python + stock-assistant 各 0 错误 |
