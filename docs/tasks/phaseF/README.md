# Phase F — Profit-Oriented Alpha Features

**起源**：见 brainstorm 成果（plan: `prompt-cached-sutherland.md`）。最高准则——**所有功能的唯一目的是为用户赚钱**（提升 alpha / 降低成本 / 控制回撤）。本轮聚焦 **美股 + 加密**，A 股 / 港股本轮不做。

## 三批落地路线

| 批次 | 周期 | 内容 |
|---|---|---|
| **第 1 批 (Phase F.1)** | 4-6 周 | 风控三件套 + 期权 GEX 仪表盘 + 加密资金面板 MVP |
| **第 2 批 (Phase F.2)** | 6-8 周 | SEC 三合一事件流（8-K diff + Form 4 cluster + 电话会议 NLP） |
| **第 3 批 (Phase F.3)** | 8-12 周 | TLH + TWAP/VWAP + TCA |

## Phase F.1 任务拆分（第 1 批）

### 风控三件套（Top-5 #5）— 优先做，零外部 API 依赖

- **F.1.1** `phaseF.risk-engine-core` — Kelly Fraction + Vol Target 数学引擎（纯 numpy/scipy） ⬅ **本任务起点**
- **F.1.2** `phaseF.risk-sharpe-decay` — 滚动 Sharpe 衰减监控（基于实盘前验证回测结果与 broker 账户权益快照）
- **F.1.3** `phaseF.risk-var-cvar` — Historical VaR / CVaR + 简单尾部模型
- **F.1.4** `phaseF.risk-api-endpoints` — `/api/risk/*` 路由暴露引擎能力
- **F.1.5** `phaseF.risk-metrics-panel` — workbench 前端 RiskReviewCenter 接入

### 期权 GEX/Vanna 仪表盘（Top-5 #1）

- **F.1.6** `phaseF.options-tradier-provider` — Tradier API 期权链 provider 接入（备选 yfinance）
- **F.1.7** `phaseF.options-gex-engine` — GEX/VEX/Charm 计算（基于已有 BSM）
- **F.1.8** `phaseF.options-gex-api` — `/api/options/gex` 端点
- **F.1.9** `phaseF.options-gex-panel` — 前端 GEX 曲线 + Magnet Level + Flip 可视化

### 加密资金费率 / OI / Basis / ETF Flow 综合面板（Top-5 #2）

- **F.1.10** `phaseF.crypto-derivs-collector` — Binance/OKX 公共 API 抓 funding/OI
- **F.1.11** `phaseF.crypto-basis-engine` — Spot-Perp basis 计算 + cash-and-carry yield
- **F.1.12** `phaseF.crypto-etf-flow` — IBIT/FBTC/ETHA 净流入数据接入
- **F.1.13** `phaseF.crypto-derivs-panel` — 前端综合面板

## 不变式（继承 CLAUDE.md）

- `apps/stock-assistant/` 与 `apps/quant-assistant/` 互不 import 对方源码
- `common/` 不反向 import `apps/*`
- 跨语言类型只能在 `common/schemas/*.schema.json` 定义
- 所有任务实现前必须先有 task spec，验收通过才能合 PR

## 验收方式（每个任务都遵循）

1. 写 `docs/tasks/phaseF/<task-id>.md`（含 AC、测试集合、文件白名单）
2. 实现，commit message 末尾 `Refs: docs/tasks/phaseF/<task-id>.md`
3. 调用 `acceptance-agent` 跑 AC，写 `docs/acceptance/phaseF/<task-id>.md`
4. verdict = ✅ PASS 才能合 PR
