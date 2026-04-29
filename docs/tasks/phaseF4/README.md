# Phase F.4 — 基本面 Alpha: PEAD + Piotroski F-Score

**起源**：见 Phase F brainstorm（`prompt-cached-sutherland.md`）。最高准则——**为用户赚钱**。

**盈利逻辑**：
- **PEAD**（Post-Earnings Announcement Drift）：财报超预期后 1-60 日存在持续漂移，年化超额 8-12%（经学术验证最稳健的中频 alpha 之一）。
- **Piotroski F-Score**：9 维财务健康指标，高分（≥7）股票历史超额 7-8%/年，低分（≤2）是财务红旗（潜在空头信号）。

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.4.1** | `phaseF4.fundamental-engine` | PEAD 引擎 + Piotroski F-Score 引擎（纯 Python + yfinance） |
| **F.4.2** | `phaseF4.fundamental-api` | `/api/fundamental/*` 路由 |
| **F.4.3** | `phaseF4.fundamental-panel` | 前端 FundamentalPanel |

## 数据来源

- **yfinance**（免费）：EPS 历史（`get_earnings_history`）、财务报表（`get_financials`、`get_balance_sheet`、`get_cash_flow`）、价格历史
- 无外部付费 API 依赖

## 合规说明

- 不构成投资建议；仅供参考
- 数据来源 yfinance，遵守其 ToS
