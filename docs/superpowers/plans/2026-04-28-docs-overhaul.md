# Documentation Overhaul (Phase A–E) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update all major docs to accurately reflect the current two-app monorepo state after Phases A–E, and create two new architecture reference documents.

**Architecture:** Documentation-only task. No code changes. Seven files updated, two new files created, all gated behind a task spec + acceptance-agent workflow per project conventions.

**Tech Stack:** Markdown. Acceptance verified with grep AC checks + file-existence checks.

---

## File Map

| Action | Path | What changes |
|---|---|---|
| Create | `docs/tasks/phaseE/docs-overhaul.md` | Task spec for this work (required before implementation) |
| Create | `docs/architecture/quant-assistant-api.md` | Rust HTTP API reference (all 5 endpoints) |
| Create | `docs/architecture/frontend-routing.md` | Vite dev proxy routing table |
| Append | `docs/MIGRATION.md` | Step 4 + Phase D + Phase E entries |
| Minor edit | `docs/conventions/acceptance-process.md` | Clarify NEEDS-REVISION resolution path |
| Minor edit | `docs/protocols/duckdb-write-discipline.md` | Note about quant-assistant results.duckdb |
| Major edit | `CLAUDE.md` | Add Phase D endpoints, update quant frontend port reference |
| Full rewrite | `docs/DESIGN.md` | Reflect Phase A–E state; replace pre-split architecture description |
| Update | `README.md` | Remove old single-backend layout, update architecture section |

---

## Task 1: Write Task Spec

**Files:**
- Create: `docs/tasks/phaseE/docs-overhaul.md`

- [ ] **Step 1: Create the task spec**

Create `docs/tasks/phaseE/docs-overhaul.md` with the following content:

```markdown
# Task phaseE.docs-overhaul: Phase A–E 文档全面更新

**Phase**: Phase E
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

Phase A–E 已完成（monorepo 拆分 + Rust 量化后端 + API 模块化 + 前端接线），但大多数文档仍反映 Phase A 或拆分前状态。本任务将所有核心文档对齐到当前实现状态。

### 做什么

1. **更新 `docs/DESIGN.md`**：完整重写，反映 Phase A–E 双产品结构
2. **更新 `README.md`**：反映当前 monorepo 布局，删除对旧 backend/、rust_core/ 的引用
3. **更新 `CLAUDE.md`**：添加 Phase D 四个端点、确认 quant 前端端口 5175
4. **追加 `docs/MIGRATION.md`**：Step 4（quant-py 删除）+ Phase D + Phase E
5. **小改 `docs/protocols/duckdb-write-discipline.md`**：添加 results.duckdb 说明
6. **小改 `docs/conventions/acceptance-process.md`**：NEEDS-REVISION 解决路径说明
7. **新建 `docs/architecture/quant-assistant-api.md`**：Rust 5 个端点完整参考
8. **新建 `docs/architecture/frontend-routing.md`**：Vite proxy 路由表

### 不做什么

- 不改任何代码
- 不改验收工具（acceptance-agent）
- 不覆盖已有验收记录

---

## 验收标准

- [ ] **AC-1**: `grep -r "quant-assistant-py\|rust_core\|apps/backend" docs/ README.md CLAUDE.md` 在 MIGRATION.md 之外无命中（MIGRATION.md 中的引用是历史记录，允许）
- [ ] **AC-2**: `test -f docs/architecture/quant-assistant-api.md` 且文件包含 `/api/backtest/run`、`/api/walk-forward`、`/api/optimize`、`/api/indicators`、`/healthz`（`grep -c "api/" docs/architecture/quant-assistant-api.md` >= 4）
- [ ] **AC-3**: `test -f docs/architecture/frontend-routing.md` 且文件包含 `8001` 和 `8002`
- [ ] **AC-4**: `grep -c "api/backtest\|api/walk-forward\|api/optimize\|api/indicators" CLAUDE.md` >= 4
- [ ] **AC-5**: `grep -c "apps/stock-assistant\|apps/quant-assistant" docs/DESIGN.md` >= 2 且 `grep -c "8001\|8002" docs/DESIGN.md` >= 2

---

## 文件影响范围（白名单）

修改：
- docs/DESIGN.md
- README.md
- CLAUDE.md
- docs/MIGRATION.md
- docs/protocols/duckdb-write-discipline.md
- docs/conventions/acceptance-process.md

新建：
- docs/tasks/phaseE/docs-overhaul.md（本文件）
- docs/architecture/quant-assistant-api.md
- docs/architecture/frontend-routing.md
- docs/acceptance/phaseE/docs-overhaul.md（验收记录，acceptance-agent 产出）
```

- [ ] **Step 2: Verify file created**

Run: `ls docs/tasks/phaseE/`
Expected: `docs-overhaul.md` appears in listing.

- [ ] **Step 3: Commit the task spec**

```bash
git add docs/tasks/phaseE/docs-overhaul.md
git commit -m "docs(task): add phaseE.docs-overhaul task spec

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 2: Create docs/architecture/ New Files

**Files:**
- Create: `docs/architecture/quant-assistant-api.md`
- Create: `docs/architecture/frontend-routing.md`

- [ ] **Step 1: Create the architecture directory and quant-assistant-api.md**

Create `docs/architecture/quant-assistant-api.md`:

```markdown
# Quant-Assistant HTTP API Reference

**Backend**: `apps/quant-assistant/backend/` (Rust, axum)  
**Port**: 8002 (dev)  
**Base URL**: `http://localhost:8002`

---

## GET /healthz

Liveness check.

**Request**: no body

**Response 200**:
```json
{"status": "ok", "timestamp": "2026-04-28T00:00:00Z"}
```

---

## POST /api/backtest/run

Run a MA crossover backtest on provided OHLCV bars.

**Request**:
```json
{
  "bars": [
    {"close": 150.0, "time": "2024-01-02"},
    ...
  ],
  "fast_period": 5,
  "slow_period": 20,
  "initial_cash": 1000000.0,
  "risk_free_rate": 0.02,
  "periods_per_year": 252
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `bars` | `Bar[]` | ✅ | — | Price bars; minimum 2 needed |
| `fast_period` | `u32` | ✅ | — | Fast MA window |
| `slow_period` | `u32` | ✅ | — | Slow MA window; must be > fast_period |
| `initial_cash` | `f64` | ✅ | — | Starting capital |
| `risk_free_rate` | `f64` | ❌ | `0.02` | Annualized risk-free rate for Sharpe |
| `periods_per_year` | `u32` | ❌ | `252` | Trading days per year |

**Bar object**:
```json
{"close": 150.0, "time": "2024-01-02"}
```
`time` is optional; `close` is required.

**Response 200**:
```json
{
  "symbol": "AAPL",
  "fast_period": 5,
  "slow_period": 20,
  "bars_processed": 300,
  "equity_curve": [1000000.0, 1002000.0, ...],
  "metrics": {
    "total_return": 0.152,
    "annualized_return": 0.148,
    "sharpe_ratio": 1.24,
    "sortino_ratio": 1.87,
    "max_drawdown": -0.089,
    "win_rate": 0.58,
    "profit_factor": 1.72,
    "total_trades": 24,
    "win_trades": 14,
    "loss_trades": 10,
    "avg_win": 0.045,
    "avg_loss": -0.026,
    "start_date": "2023-01-02",
    "end_date": "2024-12-31"
  }
}
```

**Errors**:
- `400 Bad Request`: fewer than 2 bars, fast_period >= slow_period, or internal backtest error.

---

## POST /api/walk-forward

Run walk-forward validation splits on provided closes.

**Request**:
```json
{
  "closes": [150.0, 151.2, ...],
  "fast_period": 5,
  "slow_period": 20,
  "initial_cash": 1000000.0,
  "train_size": 200,
  "test_size": 50,
  "step_size": 1,
  "embargo_size": 0
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `closes` | `f64[]` | ✅ | — | Close price series |
| `fast_period` | `u32` | ✅ | — | Fast MA window |
| `slow_period` | `u32` | ✅ | — | Slow MA window |
| `initial_cash` | `f64` | ✅ | — | Capital per window |
| `train_size` | `usize` | ✅ | — | Training window size in bars |
| `test_size` | `usize` | ✅ | — | Test window size in bars |
| `step_size` | `usize` | ❌ | `1` | Step between windows |
| `embargo_size` | `usize` | ❌ | `0` | Embargo gap between train and test |

**Response 200**:
```json
{
  "n_windows": 5,
  "equity_curve": [1000000.0, 1005000.0, ...],
  "window_splits": [
    {"train_start": 0, "train_end": 199, "test_start": 200, "test_end": 249},
    ...
  ]
}
```

**Errors**:
- `400 Bad Request`: not enough data for even one window.

---

## POST /api/optimize

Grid search over MA crossover parameter combinations, ranked by Sharpe ratio.

**Request**:
```json
{
  "closes": [150.0, 151.2, ...],
  "initial_cash": 1000000.0,
  "fast_periods": [5, 10, 15, 20],
  "slow_periods": [30, 50, 100],
  "top_n": 10
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `closes` | `f64[]` | ✅ | Close price series |
| `initial_cash` | `f64` | ✅ | Capital for each backtest run |
| `fast_periods` | `u32[]` | ✅ | Fast MA period candidates |
| `slow_periods` | `u32[]` | ✅ | Slow MA period candidates |
| `top_n` | `usize` | ✅ | How many top results to return |

**Response 200**:
```json
{
  "total_combinations": 12,
  "results": [
    {
      "fast_period": 10,
      "slow_period": 50,
      "sharpe_ratio": 1.45,
      "total_return": 0.18,
      "max_drawdown": -0.07
    },
    ...
  ]
}
```

Results are ordered by `sharpe_ratio` descending. `results` length = min(`top_n`, valid combinations).

**Errors**:
- `400 Bad Request`: empty period lists, or no valid (fast < slow) combinations.

---

## POST /api/indicators

Compute a technical indicator (SMA or EMA) over a price series.

**Request**:
```json
{
  "closes": [150.0, 151.2, ...],
  "indicator": "Sma",
  "period": 20
}
```

| Field | Type | Values | Description |
|---|---|---|---|
| `closes` | `f64[]` | — | Close price series |
| `indicator` | `string` | `"Sma"`, `"Ema"` | Indicator type |
| `period` | `u32` | ≥ 1 | Lookback window |

**Response 200**:
```json
{
  "indicator": "Sma",
  "period": 20,
  "values": [null, null, ..., 151.4, 151.9, ...]
}
```

`values` has the same length as `closes`. The first `period - 1` entries are `null` (warmup period).

**Errors**:
- `400 Bad Request`: period = 0, or unknown indicator type.

---

## Frontend Proxy

In development, the Vite dev server proxies all `/api/backtest/*`, `/api/walk-forward`, `/api/optimize`, and `/api/indicators` requests to `http://localhost:8002`.

See [`docs/architecture/frontend-routing.md`](./frontend-routing.md) for the full proxy table.
```

- [ ] **Step 2: Create frontend-routing.md**

Create `docs/architecture/frontend-routing.md`:

```markdown
# Frontend Routing & Vite Proxy

QuantPilot has three React frontends. In development each runs its own Vite dev server with a proxy table that routes API calls to the appropriate backend.

---

## Quant-Assistant Frontend (port 5175)

**Config file**: `apps/quant-assistant/frontend/vite.config.ts`

| Prefix | Backend target | Description |
|---|---|---|
| `/api/data/*` | `http://localhost:8001` (stock-assistant) | Market data (bars, symbols) |
| `/api/backtest/*` | `http://localhost:8002` (quant-assistant) | MA crossover backtest |
| `/api/walk-forward` | `http://localhost:8002` | Walk-forward validation |
| `/api/optimize` | `http://localhost:8002` | MA parameter grid search |
| `/api/indicators` | `http://localhost:8002` | SMA/EMA computation |

All proxy entries use `changeOrigin: true`.

**Why two backends?** Market data (fetching, storage) is owned by stock-assistant. Quantitative computation (backtest, optimize, indicators) is owned by quant-assistant. The frontend stitches them together via proxy — calls to `/api/data/*` pull historical bars from stock-assistant's DuckDB writer, then that data is sent to quant-assistant for computation.

---

## Stock-Assistant Workbench (port 5173)

**Config file**: `apps/stock-assistant/frontends/workbench/vite.config.ts`

| Prefix | Backend target | Description |
|---|---|---|
| `/api/*` | `http://localhost:8001` | All stock-assistant API routes |

---

## Stock-Assistant Assistant Frontend (port 5174)

**Config file**: `apps/stock-assistant/frontends/assistant/vite.config.ts`

| Prefix | Backend target | Description |
|---|---|---|
| `/api/*` | `http://localhost:8001` | All stock-assistant API routes |

---

## Production / Deployed Builds

Vite proxy only works in dev mode. For deployed builds, you need a reverse proxy layer (nginx or Caddy) in front of both backends.

Example nginx config fragment:

```nginx
# stock-assistant
location /api/data/ {
    proxy_pass http://127.0.0.1:8001;
}

# quant-assistant
location /api/backtest/ { proxy_pass http://127.0.0.1:8002; }
location /api/walk-forward { proxy_pass http://127.0.0.1:8002; }
location /api/optimize    { proxy_pass http://127.0.0.1:8002; }
location /api/indicators  { proxy_pass http://127.0.0.1:8002; }
```

---

## Port Summary

| Service | Port | Dev URL |
|---|---|---|
| stock-assistant backend | 8001 | http://localhost:8001 |
| quant-assistant backend (Rust) | 8002 | http://localhost:8002 |
| stock-assistant workbench | 5173 | http://localhost:5173 |
| stock-assistant assistant | 5174 | http://localhost:5174 |
| quant-assistant frontend | 5175 | http://localhost:5175 |
| Redis | 6379 | redis://localhost:6379 |
```

- [ ] **Step 3: Verify files created**

```bash
ls docs/architecture/
```
Expected: `frontend-routing.md  quant-assistant-api.md`

- [ ] **Step 4: Commit**

```bash
git add docs/architecture/
git commit -m "docs: add architecture reference docs (Rust API + frontend routing)

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 3: Append docs/MIGRATION.md

**Files:**
- Modify: `docs/MIGRATION.md`

- [ ] **Step 1: Append Step 4 + Phase D + Phase E entries**

At the end of `docs/MIGRATION.md`, append:

```markdown

---

## Step 4：删除 quant-assistant-py（2026-04-27）

**Task**: `docs/tasks/step4/cleanup.md` · **Verdict**: ✅ PASS

### 操作
- `apps/quant-assistant-py/` 整目录从文件系统删除
- `pyproject.toml` workspace members 移除 `apps/quant-assistant-py/backend`
- `scripts/` 移除 `dev-quant-py.sh` 中的 quant-py 相关路径引用
- `common/python/README.md`、`__init__.py`、stock-assistant test 注释等伴随清理

### 测试规模（删除后）
- common: 59 passed
- stock-assistant: 163 passed, 2 skipped
- Rust cargo test: green

---

## Phase D：Rust HTTP API 模块化 + 交易追踪（2026-04-28）

**Task**: `docs/tasks/phaseD/api-expand.md` · **Verdict**: ✅ PASS

### 主要变更

| 文件 | 变更 |
|---|---|
| `apps/quant-assistant/backend/src/lib.rs` | 新增 `Trade`、`TradeStats` struct；新增 `run_ma_crossover_backtest_with_stats()` |
| `apps/quant-assistant/backend/src/api/mod.rs` | 新建：API 路由聚合器 |
| `apps/quant-assistant/backend/src/api/backtest.rs` | 新建：`POST /api/backtest/run` handler |
| `apps/quant-assistant/backend/src/api/indicators.rs` | 新建：`POST /api/indicators` handler |
| `apps/quant-assistant/backend/src/api/optimize.rs` | 新建：`POST /api/optimize` handler |
| `apps/quant-assistant/backend/src/api/walk_forward.rs` | 新建：`POST /api/walk-forward` handler |
| `apps/quant-assistant/backend/src/main.rs` | 重写：仅含 `healthz`、`root`、`build_app`、`main` |

### 新增指标（BacktestMetrics）
`win_rate`、`profit_factor`、`total_trades`、`win_trades`、`loss_trades`、`avg_win`、`avg_loss`、`sortino_ratio`、`start_date`、`end_date`

### API 端点完整列表（Phase D 完工后）
- `GET /healthz`
- `POST /api/backtest/run`
- `POST /api/walk-forward`
- `POST /api/optimize`
- `POST /api/indicators`

---

## Phase E：量化研究前端接通 Rust API（2026-04-28）

**Task**: `docs/tasks/phaseE/frontend-wired.md` · **Verdict**: ✅ PASS

### 主要变更

| 文件 | 变更 |
|---|---|
| `apps/quant-assistant/frontend/package.json` | 添加 `lucide-react`、`tailwindcss`、`@tailwindcss/vite`、`clsx`、`tailwind-merge` |
| `apps/quant-assistant/frontend/vite.config.ts` | 添加完整 proxy 表 + `@/` 路径别名 |
| `apps/quant-assistant/frontend/src/App.tsx` | 重写：Tab 导航（回测 / 参数优化）|
| `apps/quant-assistant/frontend/src/components/BacktestPanel.tsx` | 重写：调 `POST /api/backtest/run`；MA 参数输入；结果展示 |
| `apps/quant-assistant/frontend/src/components/OptimizationPanel.tsx` | 新建：调 `POST /api/optimize`；结果排名表 |
| `apps/quant-assistant/frontend/src/lib/utils.ts` | 新建：`cn()` 工具函数 |
| `apps/quant-assistant/frontend/src/index.css` | 新建：Tailwind v4 入口 |

### 前端数据流
```
quant frontend (5175)
  ├── /api/data/* → stock-assistant (8001): 拉 K 线
  └── /api/backtest/* /api/optimize → quant-assistant (8002): 计算
```
```

- [ ] **Step 2: Verify the append was written correctly**

```bash
tail -30 docs/MIGRATION.md
```
Expected: Shows Phase E section at the bottom.

- [ ] **Step 3: Commit**

```bash
git add docs/MIGRATION.md
git commit -m "docs: append Step 4, Phase D, Phase E to MIGRATION.md

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 4: Minor Protocol and Convention Updates

**Files:**
- Modify: `docs/conventions/acceptance-process.md`
- Modify: `docs/protocols/duckdb-write-discipline.md`

- [ ] **Step 1: Add NEEDS-REVISION clarification to acceptance-process.md**

In `docs/conventions/acceptance-process.md`, after the `NEEDS-REVISION → 用户决断 → 据决断回到 [1] 修 spec 或回到 [2] 修实现` line in the flow diagram, and also in the 不变式 section, add this clarification note.

Find this section in the `## 不变式` section:

```markdown
- **任务范围之外的改动 = FAIL**（不接受"顺手做了一点别的"）
```

Replace it with:

```markdown
- **任务范围之外的改动 = FAIL**（不接受"顺手做了一点别的"）
- **NEEDS-REVISION 的两种原因**：(a) 实现 scope creep（需修实现）；(b) task spec 白名单遗漏必要伴随文件（需修 spec 白名单后重验）。acceptance-agent 报告中会说明属于哪种。
```

- [ ] **Step 2: Add results.duckdb note to duckdb-write-discipline.md**

In `docs/protocols/duckdb-write-discipline.md`, find the Rust section:

```markdown
### Rust quant-assistant 侧（只读方）
- 用 `duckdb-rs` 以 read-only 模式打开 `common/data-store/market.duckdb`
- 自有写入：`apps/quant-assistant/data/results.duckdb`（Rust 独立 db）
```

Replace with:

```markdown
### Rust quant-assistant 侧（只读方）
- 用 `duckdb-rs` 以 read-only 模式打开 `common/data-store/market.duckdb`
- 自有写入（如未来需要持久化回测结果）：`apps/quant-assistant/data/results.duckdb`（独立 db，与 market.duckdb 完全隔离）
- Phase D–E 当前实现：backtest/optimize/indicators 端点只返回 JSON，不写磁盘；results.duckdb 是预留路径
```

- [ ] **Step 3: Commit**

```bash
git add docs/conventions/acceptance-process.md docs/protocols/duckdb-write-discipline.md
git commit -m "docs: clarify NEEDS-REVISION types and quant results.duckdb status

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 5: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

The CLAUDE.md already has the correct Phase D/E commands and port 5175 in the dev scripts section based on the most recent version. The key additions needed are:

1. Under `## 常用命令` → `### 测试` section, verify `cargo test` is present
2. Add a new `### Quant-Assistant API Endpoints` reference section

- [ ] **Step 1: Add endpoint reference section to CLAUDE.md**

In `CLAUDE.md`, find the `## 常用命令` section. After the `### Schema codegen` block (which ends with `bash common/schemas/codegen.sh`), add:

```markdown

### Quant-Assistant API 端点（Rust, port 8002）

```
GET  /healthz
POST /api/backtest/run      # MA crossover 回测（bars + fast/slow period）
POST /api/walk-forward      # Walk-forward 验证窗口切分
POST /api/optimize          # 网格搜索最优参数（top-N by Sharpe）
POST /api/indicators        # SMA / EMA 指标计算
```

详细 request/response schema 见 `docs/architecture/quant-assistant-api.md`。
```

- [ ] **Step 2: Verify the 4 endpoint patterns appear in CLAUDE.md**

```bash
grep -c "api/backtest\|api/walk-forward\|api/optimize\|api/indicators" CLAUDE.md
```
Expected: output `4` (one line per endpoint)

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add quant-assistant API endpoint reference to CLAUDE.md

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 6: Rewrite docs/DESIGN.md

**Files:**
- Modify: `docs/DESIGN.md` (full rewrite)

The current DESIGN.md is 1100+ lines reflecting pre-split architecture. The new version is shorter, focused, and reflects Phase A–E state.

- [ ] **Step 1: Write the new DESIGN.md**

Replace the entire content of `docs/DESIGN.md` with:

```markdown
# QuantPilot — 设计文档

> **文档版本**：v0.3.0  
> **最后更新**：2026-04-28（Phase A–E 完工）  
> **状态**：Active

> **相关文档**：
> - 迁移记录：[`docs/MIGRATION.md`](MIGRATION.md)
> - Rust API 参考：[`docs/architecture/quant-assistant-api.md`](architecture/quant-assistant-api.md)
> - 前端路由：[`docs/architecture/frontend-routing.md`](architecture/frontend-routing.md)
> - DuckDB 写权限协议：[`docs/protocols/duckdb-write-discipline.md`](protocols/duckdb-write-discipline.md)
> - 跨语言类型规范：[`docs/conventions/cross-language-types.md`](conventions/cross-language-types.md)
> - 验收流程：[`docs/conventions/acceptance-process.md`](conventions/acceptance-process.md)

---

## 更新日志

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1.0 | 2026-04-07 | 初始版本，单体架构规划 |
| v0.2.0 | 2026-04-27 | Phase A 完工；双产品 + 共享包结构 |
| v0.3.0 | 2026-04-28 | Phase A–E 完工；Rust 量化后端全 API + 前端接线；删除 quant-assistant-py |

---

## 1. 项目概述

QuantPilot 是本地优先、LLM 原生的个人量化交易平台。核心理念：人参与决策的交易工作流 vs 自动化量化研究，分属两个独立 app，互不耦合。

**当前状态（Phase A–E 完工）**：
- `apps/stock-assistant/` — Python 股票/期权/加密交易助手，生产就绪
- `apps/quant-assistant/` — Rust 量化研究后端 + 研究前端，核心 API 全通

---

## 2. 架构总览

```
QuantPilot Monorepo
├── apps/
│   ├── stock-assistant/            # Python，端口 8001 / 5173 / 5174
│   │   ├── backend/                  FastAPI + broker + LLM + portfolio
│   │   └── frontends/
│   │       ├── workbench/            股票/期权/加密工作台（端口 5173）
│   │       └── assistant/            决策辅助 UI（端口 5174）
│   │
│   └── quant-assistant/            # Rust，端口 8002 / 5175
│       ├── backend/                  axum + Polars（回测/优化/指标）
│       └── frontend/                 量化研究台（端口 5175）
│
├── common/
│   ├── schemas/                    JSON Schema 单源 → 三语言 codegen
│   ├── data-store/                 共享 DuckDB 行情库 + golden 基准集
│   ├── python/quantpilot_common/   共享 Python 设施（config/redis/data/contracts）
│   └── frontend-components/        跨前端共享 TS 类型 + UI 组件
│
└── tools/
    ├── ml-trainer/                 ML 训练 → ONNX（Phase B+）
    └── golden-generator/           跨语言行为等价基准生成（Phase A skeleton）
```

### 端口分配

| 服务 | 端口 |
|---|---|
| stock-assistant 后端 | 8001 |
| stock-assistant workbench | 5173 |
| stock-assistant assistant | 5174 |
| quant-assistant 后端 (Rust) | 8002 |
| quant-assistant 研究前端 | 5175 |
| Redis | 6379 |

---

## 3. 两 App 的职责边界

### stock-assistant（Python）

**做什么**：人参与决策的交易工作流

- 股票（Longbridge / FuTu）、期权、加密（OKX）broker 接入
- Paper trading、实盘订单管理
- Portfolio、screener、sentiment 分析
- LLM 投顾（多模型：GPT-4o / Claude / DeepSeek / Ollama）
- 告警（飞书 / Telegram）
- **市场数据写入方**：拉取 yfinance / akshare / OKX 行情 → 写 `common/data-store/market.duckdb`

**不做什么**：自动化量化研究、ML 训练、无人值守策略执行

### quant-assistant（Rust）

**做什么**：自动化量化研究 + 规则化计算

- MA crossover 回测引擎（`POST /api/backtest/run`）
- Walk-forward 验证窗口切分（`POST /api/walk-forward`）
- 参数网格搜索（`POST /api/optimize`）
- 技术指标计算 SMA/EMA（`POST /api/indicators`）
- **市场数据只读方**：从 market.duckdb 读取行情（或通过 HTTP 向 stock-assistant `/api/data/*` 拉）

**不做什么**：broker 接入、LLM 调用、人决策界面

---

## 4. 关键不变式（强制）

1. `apps/stock-assistant/` 与 `apps/quant-assistant/` **互不 import 对方源码**
2. `common/` 不反向 import `apps/*`
3. 跨语言类型只在 `common/schemas/*.schema.json` 定义
4. `common/data-store/market.duckdb` 仅 stock-assistant 可写（详见协议文档）

CI 在每个 PR 上 grep 验证第 1、2、4 条。

---

## 5. 技术栈

### stock-assistant (Python)

| 层 | 选型 |
|---|---|
| Web 框架 | FastAPI + uvicorn |
| 数据处理 | Polars + NumPy |
| LLM | LiteLLM（路由 GPT-4o / Claude / Ollama） |
| 插件 | pluggy |
| 测试 | pytest + hypothesis |
| Linting | ruff + mypy |

### quant-assistant (Rust)

| 层 | 选型 |
|---|---|
| HTTP | axum + tokio |
| Dataframe | polars |
| DuckDB | duckdb-rs (read-only) |
| 序列化 | serde + serde_json |
| 错误处理 | anyhow (app) + thiserror (lib) |
| 日志 | tracing |

### 共享前端

| 层 | 选型 |
|---|---|
| 框架 | React 18 + TypeScript (strict) |
| 状态 | Zustand |
| 图表 | TradingView Lightweight Charts |
| 样式 | Tailwind CSS v4 + shadcn/ui |
| 构建 | Vite 6 |

### 数据层

| 用途 | 选型 |
|---|---|
| 行情存储 | DuckDB（`common/data-store/market.duckdb`） |
| 实时缓存 | Redis 7 |
| 配置/审计 | SQLite |
| 历史归档 | Parquet |

---

## 6. Schema Codegen 流水线

```
common/schemas/*.schema.json  (源，手写)
    │
    ├──► datamodel-codegen   → common/python/quantpilot_common/schemas/*.py
    ├──► typify              → apps/quant-assistant/backend/src/schemas/
    └──► json-schema-to-ts   → common/frontend-components/src/types/
```

生成产物全部 commit；CI 跑 `codegen.sh` + `git diff --exit-code` 检测漂移。

---

## 7. DuckDB 写权限协议（摘要）

| 角色 | 对 market.duckdb | 自有 db |
|---|---|---|
| stock-assistant | 读 + 写 | — |
| quant-assistant | read-only | `apps/quant-assistant/data/results.duckdb`（预留） |
| tools/golden-generator | 不动 | `common/data-store/golden/` |
| tools/ml-trainer | read-only | `common/data-store/models/` |

详见 `docs/protocols/duckdb-write-discipline.md`。

---

## 8. 验收流程（摘要）

每个 PR/任务：
1. **Task spec**：`docs/tasks/<phase>/<task-id>.md`（含 AC、白名单）
2. **实现**：commit message 末尾 `Refs: docs/tasks/...`
3. **acceptance-agent**：review + 跑 AC 测试 + 写 `docs/acceptance/<phase>/<task-id>.md`
4. **合并条件**：报告 verdict = ✅ PASS

详见 `docs/conventions/acceptance-process.md`。

---

## 9. 路线图（当前状态）

| Phase | 状态 | 摘要 |
|---|---|---|
| A | ✅ 完成 2026-04-27 | Monorepo 拆分（8 PR），500 测试，3 app 互不耦合 |
| Step 4 | ✅ 完成 2026-04-27 | 删除 quant-assistant-py |
| B | ✅ 完成（含于 Phase A~E） | Rust MVP：axum + Polars backtest |
| C | ✅ 完成（Phase D） | Walk-forward / optimize / indicators API |
| D | ✅ 完成 2026-04-28 | src/api/ 模块化 + trade tracking |
| E | ✅ 完成 2026-04-28 | 前端 wire-up（BacktestPanel + OptimizationPanel） |
| A1 | 🔜 待做 | BacktestPanel 加 equity curve 图表 |
| A2 | 🔜 待做 | Walk-Forward 面板 |
| A3 | 🔜 待做 | POST /api/ml/predict ONNX 推理端点 |
| B1 | 🔜 待做 | 提取共享 ApiError（DRY） |

详细 feature 优先级见最新 brainstorming spec。
```

- [ ] **Step 2: Verify DESIGN.md mentions both apps and ports**

```bash
grep -c "apps/stock-assistant\|apps/quant-assistant" docs/DESIGN.md
```
Expected: >= 2

```bash
grep -c "8001\|8002" docs/DESIGN.md
```
Expected: >= 2

- [ ] **Step 3: Commit**

```bash
git add docs/DESIGN.md
git commit -m "docs: rewrite DESIGN.md to reflect Phase A-E state

Previous version described pre-split single-backend architecture.
New version covers two-app monorepo, Rust API endpoints, and current roadmap.

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 7: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite README.md**

Replace the entire content of `README.md` with:

```markdown
# QuantPilot

> 本地优先、LLM 原生的个人量化交易平台

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Rust](https://img.shields.io/badge/Rust-1.82-orange)](https://rust-lang.org)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)

## 项目简介

QuantPilot 是两个独立产品 + 共享基础的 monorepo：

| App | 语言 | 职责 | 端口 |
|---|---|---|---|
| `apps/stock-assistant/` | Python | 股票/期权/加密的人决策交易、portfolio、screener、LLM 投顾 | 8001 (API), 5173 (workbench), 5174 (assistant) |
| `apps/quant-assistant/` | Rust | 自动化量化研究：回测、参数优化、walk-forward、技术指标 | 8002 (API), 5175 (frontend) |

两个 app 互不 import 对方源码，通过 `common/data-store/market.duckdb` 共享行情数据。

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

| 工具 | 版本 |
|---|---|
| Python | ≥ 3.12 |
| uv | ≥ 0.11（`brew install uv`） |
| Rust | ≥ 1.75（`brew install rust`） |
| Node.js | ≥ 20（`brew install node`） |
| Redis | 任意（`brew install redis`） |

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
# Python
(cd common/python && uv run --group dev pytest tests/)
(cd apps/stock-assistant/backend && uv run pytest tests/)

# Rust
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
| [`docs/DESIGN.md`](docs/DESIGN.md) | 架构设计（两 app 结构、技术栈、路线图） |
| [`docs/MIGRATION.md`](docs/MIGRATION.md) | Phase A–E 迁移历史 + 模块归属变更 |
| [`docs/architecture/quant-assistant-api.md`](docs/architecture/quant-assistant-api.md) | Rust HTTP API 完整参考（5 个端点） |
| [`docs/architecture/frontend-routing.md`](docs/architecture/frontend-routing.md) | Vite proxy 路由表 |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code 工作指令（命令、规范、不变式） |

## 许可证

MIT License
```

- [ ] **Step 2: Verify README no longer contains old paths**

```bash
grep -n "backend/\|rust_core\|quant-assistant-py\|apps/backend" README.md
```
Expected: No output (zero matches).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README.md for current two-app monorepo state

Remove references to old backend/, rust_core/, and quant-assistant-py.
Add current port table and link to new architecture docs.

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Task 8: Run Acceptance Agent

**Files:**
- Create: `docs/acceptance/phaseE/docs-overhaul.md` (produced by acceptance-agent)

- [ ] **Step 1: Verify AC checks manually before calling acceptance-agent**

```bash
# AC-1: No stale references in active docs (MIGRATION.md allowed)
grep -r "quant-assistant-py\|rust_core\|apps/backend" docs/ README.md CLAUDE.md | grep -v "docs/MIGRATION.md"
```
Expected: No output.

```bash
# AC-2: quant-assistant-api.md exists with 5 endpoints
test -f docs/architecture/quant-assistant-api.md && echo "EXISTS"
grep -c "api/" docs/architecture/quant-assistant-api.md
```
Expected: `EXISTS` then a number >= 4.

```bash
# AC-3: frontend-routing.md has 8001 and 8002
grep -c "8001\|8002" docs/architecture/frontend-routing.md
```
Expected: >= 2.

```bash
# AC-4: CLAUDE.md has 4 endpoint patterns
grep -c "api/backtest\|api/walk-forward\|api/optimize\|api/indicators" CLAUDE.md
```
Expected: 4.

```bash
# AC-5: DESIGN.md has both apps and ports
grep -c "apps/stock-assistant\|apps/quant-assistant" docs/DESIGN.md
grep -c "8001\|8002" docs/DESIGN.md
```
Expected: >= 2 for both.

- [ ] **Step 2: Call acceptance-agent**

Invoke `acceptance-agent` with:
- Task spec path: `docs/tasks/phaseE/docs-overhaul.md`
- Diff range: commits since `docs/tasks/phaseE/docs-overhaul.md` was created

The agent will produce `docs/acceptance/phaseE/docs-overhaul.md`.

- [ ] **Step 3: Confirm PASS and commit acceptance record**

```bash
git add docs/acceptance/phaseE/docs-overhaul.md
git commit -m "docs(acceptance): phaseE.docs-overhaul PASS

Refs: docs/tasks/phaseE/docs-overhaul.md"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Task 1: task spec created
- ✅ Task 2: docs/architecture/ two new files
- ✅ Task 3: MIGRATION.md append (Step 4 + Phase D + Phase E)
- ✅ Task 4: acceptance-process.md + duckdb-write-discipline.md minor edits
- ✅ Task 5: CLAUDE.md endpoint section
- ✅ Task 6: DESIGN.md full rewrite
- ✅ Task 7: README.md update
- ✅ Task 8: acceptance-agent run

**Placeholder scan:** No TBDs or "implement later" found.

**Type consistency:** No code types; doc links are self-consistent.

**Spec AC coverage:**
- AC-1 tested in Task 7 Step 2 and Task 8 Step 1
- AC-2 tested in Task 8 Step 1
- AC-3 tested in Task 8 Step 1
- AC-4 tested in Task 5 Step 2 and Task 8 Step 1
- AC-5 tested in Task 6 Step 2 and Task 8 Step 1
