# Phase F.8 — 自动化 DCF + 蒙特卡洛估值

**起源**：Brainstorm 候选 #13 — 自动化 DCF + 蒙特卡洛敏感度。

**盈利逻辑**：
- DCF = 公允价值的锚，识别市场定价偏差（margin of safety > 20% → 买入信号）。
- 蒙特卡洛模拟 1000 次 WACC/增长率/终值倍数组合 → P5/P50/P95 公允价值分布。
- P50 公允价值 vs 现价的上行空间 = 可量化的 alpha 来源。
- 历史数据：深度价值股（margin of safety > 30%）未来 12 月平均超额 8-15%。

**数据来源**：yfinance financials/balance_sheet/cash_flow（免费，无需 API Key）

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.8.1** | `phaseF8.dcf-engine` | DCF + WACC 计算 + 蒙特卡洛 |
| **F.8.2** | `phaseF8.dcf-api` | `/api/dcf/*` 路由 |
| **F.8.3** | `phaseF8.dcf-panel` | 前端 DCFPanel |
