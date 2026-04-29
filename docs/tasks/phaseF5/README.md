# Phase F.5 — 盈利操纵检测 + 指数调仓预览

**起源**：Phase F brainstorm 候选功能扩展。最高准则——**为用户赚钱**。

**盈利逻辑**：
- **Beneish M-Score**：8 维财务比率识别盈利操纵风险（M-Score > -1.78 → 高操纵概率），历史上高 M-Score 股票后续大幅跑输（空头信号）。
- **Russell 调仓预览**：Russell 年度调仓（每年 6 月末）规则透明，仅凭市值排名即可提前预判调入/调出，历史上调入前 5-10 日超额 1-3%。

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.5.1** | `phaseF5.quant-signals-engine` | Beneish M-Score 引擎 + Russell 调仓预览引擎 |
| **F.5.2** | `phaseF5.quant-signals-api` | `/api/quant-signals/*` 路由 |
| **F.5.3** | `phaseF5.quant-signals-panel` | 前端 QuantSignalsPanel |

## 数据来源

- yfinance：财务报表（Beneish M）、市值/浮动股本（Russell preview）
- Russell 规则：公开规则硬编码（市值排名 1-1000 = Russell 1000，1001-2000 = Russell 2000）
