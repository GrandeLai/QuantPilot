# QuantPilot

> 本地优先、LLM 原生、多资产覆盖的个人量化交易平台

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Rust](https://img.shields.io/badge/Rust-1.94-orange)](https://rust-lang.org)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)

## 项目简介

QuantPilot 是一款面向个人量化交易者的本地优先平台，兼具专业量化工具的深度和私人银行理财助理的易用性。

**核心特性**

- **全资产覆盖**：股票（A/港/美）、期货、期权、加密货币、基金/ETF、外汇、债券
- **端到端工作流**：数据获取 → 因子研究 → 策略编写 → 回测验证 → 模拟/实盘 → 复盘总结
- **LLM 深度集成**：AI 贯穿策略生成、风险分析、复盘解读全链路
- **本地优先**：数据和策略默认本地加密存储，隐私安全
- **OKX 加密研究链路**：已补齐 BTC/ETH 多时间维度研究数据集、核心因子 provider、walk-forward 验证、反转概率输出，并同时接入主工作台与投资助理
- **趋势策略模板**：已内置 `VWAP + 双 EMA` 的加密趋势策略模板，支持动态止损、超时离场和后续参数搜索

## 技术架构（Phase A 完成后的拆分版）

QuantPilot 拆成两个独立产品 + 共享基础：

```
apps/
├── stock-assistant/        # Python: 股票/期权/加密的人决策交易（端口 8001）
│   ├── backend/                FastAPI + Longbridge/FuTu/OKX broker + paper trading + LLM 投顾
│   └── frontends/
│       ├── workbench/          React 19 工作台（端口 5173）
│       └── assistant/          React 19 决策辅助 UI（端口 5174）
│
├── quant-assistant-py/     # Phase A 临时态：Python 量化研究后端（端口 8002，Step 4 删除）
│   └── backend/                回测、因子、ML、信号、策略、优化、研究
│
└── quant-assistant/        # Phase B+：Rust 量化助手
    ├── backend/                axum + Polars + duckdb-rs（Phase A 仅 PyO3 seed）
    └── frontend/               研究台 (端口 5175，Phase A skeleton)

common/
├── schemas/                JSON Schema 单源 → 三语言 codegen
├── data-store/             共享 DuckDB 行情库（stock 单写，其他只读）
├── frontend-components/    跨前端共享 TS 类型 + UI 组件
├── python/                 共享 Python 设施（config / redis / data / contracts / risk / ...）
└── docs/

tools/
├── ml-trainer/             Python ML 训练 → ONNX (Phase B+)
└── golden-generator/       跨语言行为等价基准数据集生成 (Phase A skeleton)
```

详细拆分历史 + 模块归属 见 [`docs/MIGRATION.md`](docs/MIGRATION.md)。

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
# 从仓库根目录
uv sync                # 同步所有 Python workspace member（common/python + 三个 app + tools）
npm install            # 同步所有前端 npm workspace
```

### 启动各 app（按需）

```bash
# 股票助手（推荐主开发模式）
./scripts/dev-stock.sh
# → API:       http://localhost:8001
# → workbench: http://localhost:5173
# → assistant: http://localhost:5174

# 量化助手 Python 临时态（Phase A 期间）
./scripts/dev-quant-py.sh
# → API:       http://localhost:8002
# → frontend:  http://localhost:5175

# 量化助手 Rust（Phase B+ 起真正可用）
./scripts/dev-quant.sh
```

每个脚本独立可跑，不需要全部启动。

## 开发命令

### Python 测试（按 app）

```bash
# common/python
(cd common/python && uv run --group dev pytest tests/ -v)

# stock-assistant
(cd apps/stock-assistant/backend && uv run pytest tests/ -v)

# quant-assistant-py
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -v)
```

### Rust（quant-assistant 后端）

```bash
(cd apps/quant-assistant/backend && cargo check)
(cd apps/quant-assistant/backend && cargo test)
```

### 前端 build

```bash
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
(cd common/frontend-components && npm run build)
```

### Schema codegen（改 schema 后必跑）

```bash
bash common/schemas/codegen.sh
```
```

### 前端（`cd frontend`）

```bash
npm install                      # 安装依赖
npm run dev                      # 启动开发服务器（热更新）
npm run build                    # 生产构建
npm run type-check               # TypeScript 类型检查
```

### 加密研究与优化

当前加密研究链路基于 OKX 数据，已支持：

- BTC / ETH 的 `15m / 1h / 4h / 1d / 1w` 多时间维度研究数据集
- `VWAP_EMA_Trend` 趋势策略模板
- `POST /api/crypto/research/train` 多周期研究摘要
- `GET /api/crypto/research/latest` 最近一次缓存研究结果
- `POST /api/crypto/research/optimize` 基于现有 Optuna 引擎的参数搜索
- `GET /api/crypto/research/optimize/latest` 最近一次缓存优化结果

当前主工作台的加密回测会优先推荐 `VWAP_EMA_Trend`，默认按 `1h` 周期进入验证；Investment Assistant 也会复用同一份最新研究与优化摘要来展示市场状态、推荐策略和最优参数。

## 项目结构

```
QuantPilot/
├── backend/                    # Python FastAPI 后端
│   ├── src/quantpilot/         # 主包
│   │   ├── main.py             # FastAPI 应用入口
│   │   ├── config.py           # 配置管理
│   │   └── cli.py              # CLI 工具
│   ├── tests/                  # 测试套件
│   └── pyproject.toml          # Python 项目配置
├── rust_core/                  # Rust 高性能计算核心
│   ├── src/lib.rs              # PyO3 模块（回测引擎、指标计算）
│   ├── Cargo.toml              # Rust 项目配置
│   └── pyproject.toml          # maturin 构建配置
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.tsx             # 根组件
│   │   └── components/
│   │       └── CandlestickChart.tsx  # TradingView K 线图组件
│   └── package.json
├── assistant_frontend/         # Investment Assistant React 前端
│   ├── src/
│   │   ├── App.tsx             # 投资助理壳层
│   │   └── components/         # 助理核心视图组件
│   └── package.json
├── docs/
│   └── DESIGN.md               # 完整设计文档（必读）
├── data/                       # 本地数据目录（git ignored）
├── scripts/                    # 启动脚本
└── docker-compose.yml          # Docker 编排配置
```

## API 文档

后端启动后访问：
- Swagger UI：[http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc：[http://localhost:8000/redoc](http://localhost:8000/redoc)

## 开发路线图

- **Phase 0**（已完成）：技术验证 — 脚手架、DuckDB、Rust PyO3、TradingView、LiteLLM
- **Phase 1**（进行中）：MVP — 数据模块、K 线可视化、策略编辑器、基础回测
- **Phase 2**：可用版 — 模拟盘、券商接入、实盘交易、告警系统

当前交易执行层的实际状态是：

- 股票/通用交易已经统一到 `/api/trading/*`
- `Futu provider` 已接入 unified trading 主线，并显式暴露配置 / SDK / OpenD 可用性
- `Longbridge` 为正式股票交易 provider
- `mock provider` 为本地兜底与测试闭环
- 加密货币继续通过 `OKX` 专用链路执行
- `/api/trading/orders` 现在会在提交前执行基础风控检查，并对超限订单返回结构化 `risk_rejected` 错误
- `/api/trading/orders/{order_id}/events` 现已提供最小 OMS 事件时间线，交易页可查看提交 / 成交 / 撤单等状态流
- **Phase 3**：好用版 — LLM 深度集成、因子研究、期权模块
- **Phase 4**：生态版 — 插件系统、ML 策略、社交跟单

详见 [docs/DESIGN.md](docs/DESIGN.md)。

## 许可证

MIT License
