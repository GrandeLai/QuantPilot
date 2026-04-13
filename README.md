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

## 技术架构

```
frontend/        React 18 + TypeScript + Vite 8 + TradingView Lightweight Charts
assistant_frontend/ React 19 + TypeScript + Vite 8 + Zustand
backend/         Python 3.12 + FastAPI + DuckDB + LiteLLM
rust_core/       Rust + PyO3（高性能回测引擎核心）
```

### 产品结构说明

- `frontend/`：QuantPilot 主工作台，承载研究、策略、验证、运行等量化工作流
- `assistant_frontend/`：Investment Assistant 前端，承载资产总览、机会池、调仓建议、风险雷达、复盘与问答
- `backend/`：共享后端与平台层，同时服务主工作台与投资助理

## 快速开始

### 环境要求

| 工具 | 版本 | 安装 |
|---|---|---|
| Python | ≥ 3.12 | 由 uv 自动管理 |
| uv | ≥ 0.11 | `brew install uv` |
| Rust | ≥ 1.75 | `brew install rust` |
| Node.js | ≥ 20 | `brew install node` |
| Docker | ≥ 24 | [docker.com](https://docker.com) |

### 一键启动（推荐）

```bash
# 启动所有服务（Redis + 后端 API）
./scripts/dev.sh

# 仅启动基础设施（Redis）
./scripts/infra.sh
```

### 分步启动

```bash
# 1. 启动基础设施
docker compose up redis -d

# 2. 安装后端依赖 & 构建 Rust 扩展
cd backend
uv sync --extra dev
uv run maturin develop --manifest-path ../rust_core/Cargo.toml
cd ..

# 3. 启动后端 API（http://localhost:8000）
./scripts/start_backend.sh

# 4. 安装前端依赖 & 启动开发服务器（http://localhost:5173）
./scripts/start_frontend.sh
```

### Docker Compose 完整部署

```bash
docker compose up -d
```

## 开发命令

### 后端（`cd backend`）

```bash
uv sync --extra dev              # 安装依赖（含开发工具）
uv run pytest tests/ -v          # 运行测试
uv run ruff check src/ tests/    # 代码检查
uv run ruff format src/ tests/   # 代码格式化
uv run mypy src/                 # 类型检查
```

### Rust 核心（`cd rust_core`）

```bash
cargo build                      # 编译（debug）
cargo build --release            # 编译（release，性能优化）
cargo test                       # 运行 Rust 单元测试

# 构建并安装 Python 扩展（在 backend/ 目录下执行）
cd ../backend && uv run maturin develop --manifest-path ../rust_core/Cargo.toml
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
- **Phase 3**：好用版 — LLM 深度集成、因子研究、期权模块
- **Phase 4**：生态版 — 插件系统、ML 策略、社交跟单

详见 [docs/DESIGN.md](docs/DESIGN.md)。

## 许可证

MIT License
