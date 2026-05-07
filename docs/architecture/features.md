# QuantPilot 功能总结

> **状态**：Phase A–E 完工，Phase G1 共享市场宇宙落地
> **最后更新**：2026-05-07

按"是否有人参与决策"切线，QuantPilot 的能力分配在两个 app 中：

| 维度 | stock-assistant (Python, 8001) | quant-assistant (Rust, 8002) |
|---|---|---|
| 决策模式 | 人参与 | 自动化、规则化 |
| 主要工作流 | broker 接入 / 实盘 / 投顾 / portfolio | 回测 / 优化 / walk-forward / 推理 |
| 数据流 | 写入 market.duckdb | read-only 消费 |
| 支持资产 | 美股 / ETF / 港股 / A 股 / 期权 / OKX 加密 | 美股 / ETF / 港股 / A 股 / OKX 加密 |
| ML | 不做训练，不做推理 | 仅 ONNX 推理 |
| LLM | 多模型路由 + agent | 不接 LLM |

---

## 1. stock-assistant 功能矩阵

### 1.1 多 broker 接入与交易

| 能力 | 模块 | 路由前缀 |
|---|---|---|
| 统一交易接口（Longbridge / FuTu / Mock） | `quantpilot_stock.broker.*` | `/api/trading` |
| 模拟账户（持仓 / 订单 / 现金流） | `quantpilot_stock.paper` | `/api/paper` |
| 加密交易（OKX 现货 / 永续 / 期权） | `quantpilot_stock.broker.okx_*` + 直接路由 | `/api/crypto` |
| 期权希腊字母 / 隐含波动率 / 情景分析 | `quantpilot_stock.options` | `/api/options` |
| API Key 管理（keyring 加密） | `quantpilot_stock.security` | `/api/security` |

支持 broker 列表（`get_status` 返回 `TradingProviderStatus`）：
- **Longbridge**（美股、港股，主要目标）
- **FuTu**（美股、港股，需本地 OpenD）
- **OKX**（加密现货 + 永续 + 期权）
- **Mock**（无凭证场景）

### 1.2 投资组合与监控

| 能力 | 模块 | 路由前缀 |
|---|---|---|
| 持仓快照 / 资产分配 / PnL 归因 | `quantpilot_stock.portfolio` | `/api/portfolio` |
| 告警规则（价格 / 指标 / 事件） | `quantpilot_stock.alerts` | `/api/alerts` |
| WebSocket 实时行情 / 信号订阅 | `quantpilot_stock.api.ws` | `/ws/bars`、`/ws/signals` |
| 飞书 / Telegram 推送 | `quantpilot_stock.alerts.notifiers` | （触发器） |

### 1.3 数据与研究

| 能力 | 模块 | 路由前缀 |
|---|---|---|
| 行情拉取（yfinance / akshare / OKX） | `quantpilot_common.data.fetchers` | `/api/data` |
| 行情入库（market.duckdb 单写方） | `quantpilot_common.data.storage` | （后台任务） |
| 标的搜索 / 元信息 | `quantpilot_common.data.fetchers.*.search_symbols` | `/api/data/symbols` |
| 双产品市场宇宙 | `quantpilot_common.data.universe` | `/api/data/universe` |
| 选股 / 选币 screener | `quantpilot_stock.screener` | `/api/screener` |
| 情绪分析（VADER + RSS） | `quantpilot_stock.sentiment` | `/api/sentiment` |
| Insights（基本面 / 同行 / 宏观） | `quantpilot_stock.insights` | `/api/insights` |

### 1.4 LLM 投顾与 Agent

| 能力 | 模块 | 路由前缀 |
|---|---|---|
| 多模型路由（GPT-4o / Claude / DeepSeek / Ollama） | `quantpilot_stock.llm` | `/api/llm` |
| 流式 chat / generate-strategy | `quantpilot_stock.api.llm` | `/api/llm/stream`、`/api/llm/generate-strategy` |
| Agent 中间件 + 熔断 / 退避 / fallback | `quantpilot_stock.agent` | (内部) |

### 1.5 平台 / 插件

| 能力 | 模块 | 路由前缀 |
|---|---|---|
| Provider 状态汇总 | `quantpilot_stock.api.platform` | `/api/platform/summary` |
| 插件注册（pluggy hookspec） | `quantpilot_common.plugins` + `quantpilot_stock.api.plugins` | `/api/plugins` |
| 健康检查 | `quantpilot_stock.api.platform` | `/healthz` |

---

## 2. quant-assistant 功能矩阵

### 2.1 量化计算 API（5 个端点 + healthz）

| 端点 | 能力 |
|---|---|
| `GET /healthz` | 存活检查 |
| `POST /api/backtest/run` | MA crossover 回测；返回 equity curve + 完整 metrics（Sharpe / Sortino / 胜率 / max drawdown 等） |
| `POST /api/walk-forward` | walk-forward 验证：训练 / 测试窗口切分 + 滚动 equity curve |
| `POST /api/optimize` | 网格搜索（fast×slow MA 周期组合），按 Sharpe top-N 返回 |
| `POST /api/indicators` | SMA / EMA 指标计算 |
| `POST /api/ml/predict` | ONNX 模型推理（按 model_id 加载 + features 数组输入） |

详细 request / response 见 [`quant-assistant-api.md`](quant-assistant-api.md)。

### 2.2 内部能力（不直接暴露端点）

| 能力 | 模块 | 说明 |
|---|---|---|
| 回测引擎核心 | `lib.rs::run_ma_crossover_backtest_with_stats` | MA crossover；Polars 计算；trade tracking |
| Metrics 计算 | `lib.rs::BacktestMetrics` | total / annualized return、Sharpe、Sortino、max drawdown、win rate、profit factor 等 |
| ONNX 推理运行时 | `ml_runner::MlRunner` | 用 `tract-onnx` 加载 + 推理；按 meta.json 指定 input shape |
| 共享 ApiError | `api/mod.rs::ApiError` | 跨子路由统一错误响应（Phase E B1） |

### 2.3 研究前端（端口 5175）

3 个 Tab，全部接 quant-assistant API：

| Tab | 组件 | 调用 |
|---|---|---|
| 回测 | `BacktestPanel.tsx` | `POST /api/backtest/run` + 权益曲线 SVG 图 |
| 参数优化 | `OptimizationPanel.tsx` | `POST /api/optimize` + 排名表 |
| Walk-Forward | `WalkForwardPanel.tsx` | `POST /api/walk-forward` + AbortController + 客户端校验 |

行情数据通过 vite proxy 走 `/api/data/*` → stock-assistant (8001)。回测页从共享市场宇宙提供美股、ETF、港股、A 股与 OKX 加密快捷标的；如 DuckDB 暂无 K 线，会先触发 stock-assistant 数据层补数，再把 OHLCV 交给 Rust API 计算。

---

## 3. common 共享能力

| 模块 | 能力 |
|---|---|
| `common/schemas/` | JSON Schema 单源（`ohlcv`、`symbol`、`factor`、`signal`、`backtest_config`、`backtest_result`） |
| `common/python/quantpilot_common/config` | Pydantic Settings 全局配置 |
| `common/python/quantpilot_common/data/fetchers` | yfinance / akshare / OKX 拉数据 |
| `common/python/quantpilot_common/data/universe` | 双产品共享支持市场宇宙 |
| `common/python/quantpilot_common/redis` | 异步 redis 客户端 + price_cache + order_queue |
| `common/python/quantpilot_common/strategy_persistence` | 策略文件 Git 版本管理（gitpython） |
| `common/python/quantpilot_common/plugins` | pluggy hookspec（on_bar / on_signal / on_alert） |
| `common/python/quantpilot_common/data/storage` | DuckDB 客户端（stock 写、其他读） |
| `common/data-store/market.duckdb` | 共享行情库（stock-assistant 单写） |
| `common/data-store/golden/` | 跨语言行为等价基准数据集（Phase A 骨架） |
| `common/data-store/models/<model_id>/` | ONNX 模型 + meta.json |
| `common/frontend-components/` | 跨前端共享 TS 类型 + UI 组件 + market universe |

---

## 4. tools 离线工具

| 工具 | 能力 | 状态 |
|---|---|---|
| `tools/ml-trainer/` | sklearn / xgboost 训练 → skl2onnx 导出 | Phase B+ 启动 |
| `tools/golden-generator/` | 跑 quant-py 产出 expected/，给 Rust 对齐用 | Phase A 骨架 |

---

## 5. 路线图节选（详见 DESIGN.md §9）

| Phase | 状态 | 摘要 |
|---|---|---|
| A | ✅ 2026-04-27 | Monorepo 拆分（8 PR），500 测试 |
| B | ✅ 含于 Phase A–E | Rust MVP：axum + Polars |
| C | ✅ (Phase D) | walk-forward / optimize / indicators API |
| D | ✅ 2026-04-28 | `src/api/` 模块化 + trade tracking |
| E | ✅ 2026-04-28 | 前端接 Rust API + A1–A3 + B1 + B4 |
| G1 | ✅ 2026-05-07 | 双产品共享市场宇宙；两个产品均支持美股与加密等资产 |
| F | 🔄 启动 | 风控引擎核心（risk-engine-core）等 |
