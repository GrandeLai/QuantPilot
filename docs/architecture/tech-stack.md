# QuantPilot 技术实现详解

> **范围**：技术选型 + 关键代码位置 + 设计取舍
> **最后更新**：2026-05-08

按运行时层切分技术栈。每条都给出"选了什么 / 为什么 / 关键文件"。

---

## 1. stock-assistant（Python，端口 8001）

### 1.1 Web 层

| 选型 | 理由 | 关键文件 |
|---|---|---|
| FastAPI + uvicorn | async-first；自动 OpenAPI；Pydantic v2 校验 | `apps/stock-assistant/backend/src/quantpilot_stock/main.py` |
| WebSocket（标准库 + FastAPI 内建） | 实时行情广播 / 信号订阅 | `apps/stock-assistant/backend/src/quantpilot_stock/api/ws.py` |
| API 路由分包 | 按业务域分文件（trading / portfolio / advisor / ...） | `apps/stock-assistant/backend/src/quantpilot_stock/api/*.py` |

### 1.2 Broker 层

| 选型 | 理由 | 关键文件 |
|---|---|---|
| `longbridge>=0.4` | 主交易目标（美 / 港股，sandbox/testnet + 实盘） | `quantpilot_stock/broker/longbridge.py` |
| `futu-api>=9.3`（Linux 限定） | 备选 broker；arm64 macOS 装不上故 marker 限定 | `quantpilot_stock/broker/futu.py` |
| `okx>=2.1` | 加密交易（现货 / 永续 / 期权） | `quantpilot_stock/broker/okx_*.py` |
| 统一抽象 `TradingProvider` | 屏蔽不同 broker 差异，对 API 路由暴露统一形状 | `quantpilot_stock/broker/types.py` |
| Mock provider | 无凭证场景 / CI / 演示 | `quantpilot_stock/broker/mock.py` |

### 1.3 Agent 层

| 选型 | 理由 | 关键文件 |
|---|---|---|
| `litellm>=1.40` | 仅用于内部 agent 的模型路由，不对外暴露通用 chat API | `quantpilot_stock/agent/provider.py` |
| Circuit Breaker + 指数退避 | 任一模型挂掉自动切换 | `quantpilot_stock/agent/router.py` |
| 中间件链（middleware hook） | 注入证据约束 / 日志 / 限流 | `quantpilot_stock/agent/agent.py` |

### 1.4 数据 / 计算

| 选型 | 理由 | 关键文件 |
|---|---|---|
| Polars + NumPy | DataFrame 高性能；比 Pandas 快 5–10× | `quantpilot_common/data/...` |
| `pandas-ta` | 技术指标实现成熟 | （间接） |
| `vaderSentiment` + `feedparser` | 轻量情绪分析 + RSS 拉新闻 | `quantpilot_stock/sentiment/` |
| Pydantic v2 | 类型安全 + JSON Schema 兼容 | 全 API 层 |

### 1.5 持久化

| 选型 | 理由 | 关键文件 |
|---|---|---|
| DuckDB（read+write） | 单文件、列存、零运维；支持 parquet 导入导出 | `quantpilot_common/data/storage.py` |
| Redis 7 + `redis.asyncio` | 实时行情缓存 | `quantpilot_common/redis/` |
| SQLite | 配置 / 审计 | `quantpilot_stock/portfolio/snapshots.py` 等 |
| `keyring>=25` | broker API key OS-level 加密存储 | `quantpilot_stock/security/` |
| GitPython | 策略文件 Git 版本管理 | `quantpilot_common/strategy_persistence/git_manager.py` |

### 1.6 测试 / 工具链

| 选型 | 理由 |
|---|---|
| pytest + `pytest-asyncio`（auto mode） | async-first 项目标配 |
| `fakeredis` | Redis 单元测试 |
| ruff + mypy（strict mode） | lint + 类型检查（B4 后 stock-assistant 0 mypy 错误） |
| uv workspace | 多 Python 包共享解析（common / stock-assistant / tools） |

---

## 2. quant-assistant（Rust，端口 8002）

### 2.1 Web 层

| 选型 | 理由 | 关键文件 |
|---|---|---|
| `axum 0.7` + `tokio` | 主流 async HTTP 框架；与 tower 生态兼容 | `apps/quant-assistant/backend/src/main.rs` |
| `tower-http` | CORS、tracing 中间件 | `main.rs` |
| API 子模块 | 与 Python 同形（每端点一个文件） | `src/api/{backtest,walk_forward,optimize,indicators,ml_predict}.rs` |
| 共享 `ApiError` | 跨路由统一错误响应（B1 抽出） | `src/api/mod.rs::ApiError` |

### 2.2 计算层

| 选型 | 理由 | 关键文件 |
|---|---|---|
| `polars 0.43` | DataFrame；与 Python 同库，行为一致性高 | `lib.rs` 全篇 |
| `serde + serde_json` | request / response 序列化 | 全 API |
| `chrono` | 时间处理 | `lib.rs::Bar` |
| `anyhow`（应用层）+ `thiserror`（库层） | 错误处理分层 | 全代码库 |

### 2.3 ML 推理

| 选型 | 理由 | 关键文件 |
|---|---|---|
| `tract-onnx 0.21` | 纯 Rust ONNX runtime，无 C++ 依赖；CI 友好 | `src/ml_runner.rs` |
| 模型契约 | `common/data-store/models/<model_id>/{model.onnx, meta.json}` | meta 由 `ml_model_meta.schema.json` 约束 |
| Path traversal guard | `model_id` 不允许 `/` 或 `..`，避免读取沙盒外文件 | `src/api/ml_predict.rs` |

> 选 tract 而不是 ort 的取舍详见 plan §6 末尾。

### 2.4 数据

| 选型 | 理由 | 关键文件 |
|---|---|---|
| `duckdb-rs`（read-only） | 量化端不写共享 db | （Phase B 后续接入） |
| HTTP 拉数据 | 通过 `/api/data/*` proxy 到 stock-assistant | 前端 vite.config.ts proxy |

### 2.5 测试 / 工具链

| 选型 | 理由 |
|---|---|
| `cargo test` + 单元测试同 crate | Rust 标配 |
| Golden 数据集（Phase A 骨架） | 跨语言行为等价基准 |
| `cargo clippy` | lint |
| `cargo fmt` | 格式化 |

---

## 3. 前端（React 18 + TypeScript strict）

### 3.1 共有

| 选型 | 理由 |
|---|---|
| Vite 6 | 启动快、HMR 稳；ES modules 原生 |
| TypeScript strict mode | 类型严格 |
| Zustand | 轻量 state；比 Redux 心智负担低 |
| Tailwind CSS v4 + shadcn/ui | 组件库 + 样式 |
| `lucide-react` | 图标 |
| npm workspace（根 `package.json`） | 4 前端共享依赖解析 |

### 3.2 工作台（workbench, 5173）

| 组件 | 用途 |
|---|---|
| `ChartPanel.tsx` | TradingView Lightweight Charts |
| `Trading*.tsx` / `BrokerTradingPanel.tsx` | 多 broker 交易执行 / sandbox 安全模式 |
| `Crypto*.tsx` / `Options*.tsx` | 加密 / 期权专用面板 |
| `Advisor.tsx` / `Screener*.tsx` | 结构化投顾 / 选股 |
| `Sentiment*.tsx` / `Screener*.tsx` | 情绪 / 选股 |

### 3.3 决策辅助（assistant, 5174）

独立前端，通过 `/api/advisor` / `/api/insights` 调 stock-assistant。

### 3.4 量化研究台（quant frontend, 5175）

3 Tab：实盘前验证回测 / 优化 / Walk-Forward。无图表库依赖（用纯 SVG 自绘 equity curve，避免拖大 bundle）。

### 3.5 共享前端组件

| 内容 | 位置 |
|---|---|
| TS 类型（codegen 产出） | `common/frontend-components/src/types/` |
| 图表 / Monaco / API client base | `common/frontend-components/src/` |

---

## 4. 跨语言契约

```
common/schemas/*.schema.json  （JSON Schema 单源，手写）
        │
        ├──► datamodel-codegen        →  common/python/quantpilot_common/schemas/*.py
        ├──► typify                   →  apps/quant-assistant/backend/src/schemas/
        └──► json-schema-to-typescript →  common/frontend-components/src/types/
```

| 流水线脚本 | `common/schemas/codegen.sh` |
| CI 防漂移 | `git diff --exit-code common/` 在 `codegen.sh` 后必须无差 |
| 策略 | "schema 改了就跑"——禁止手改产物 |

---

## 5. 验收 / 协作工作流

| 工具 | 角色 |
|---|---|
| `acceptance-agent`（Claude Code subagent） | 跑 task spec AC + 写报告，不写代码 |
| `docs/tasks/<phase>/<id>.md` | 任务规格（含 AC、白名单、测试集合） |
| `docs/acceptance/<phase>/<id>.md` | 验收报告（PASS / FAIL / NEEDS-REVISION） |
| Conventional Commits | `feat:` / `fix:` / `refactor:` / `chore:` / `docs:` |
| `Refs:` 行 | commit message 末尾必带 task spec 路径 |

详见 [`../conventions/acceptance-process.md`](../conventions/acceptance-process.md)。

---

## 6. 部署 / 运行（本地优先）

```
本地机器
├── Redis 7              (port 6379)
├── stock-assistant      (port 8001)  ──┐
├── workbench            (port 5173)    │ /api/* → 8001
├── assistant            (port 5174)    │ /api/* → 8001
├── quant-assistant      (port 8002)  ──┤
└── quant frontend       (port 5175)    │ /api/data → 8001, 其他 → 8002
                                        │
                            common/data-store/market.duckdb
                                        │
                            stock 单写，其他 read-only
```

部署到生产时（未实施）需 nginx / Caddy 反向代理替代 Vite proxy；详见 [`frontend-routing.md §4`](frontend-routing.md)。

---

## 7. 关键设计取舍备忘

| 决策 | 选项 A（采用） | 选项 B（拒绝） | 理由 |
|---|---|---|---|
| Schema 单源语言 | JSON Schema | Pydantic / Rust types | 真正语言中立；现有 Pydantic 不严格 |
| Rust ONNX runtime | tract-onnx | ort | 无 C++ 依赖；CI 简单 |
| DuckDB 写权限 | stock 单写 | 双写 | 避免多进程锁竞争 |
| 策略 DSL（Phase C.1+） | Rhai + Native trait | 纯 Rhai / Lua / WASM | 性能 + 灵活性平衡 |
| 量化前端图表 | 纯 SVG | 引入 lightweight-charts | bundle size + 简单需求不必上图表库 |
| 验收 agent CI 集成 | 本地手动 + PR 描述粘贴 verdict | GitHub Action 调 Claude API | 避免 token 烧钱（个人项目） |
