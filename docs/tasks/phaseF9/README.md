# Phase F.9 — 空头兴趣 + 轧空风险检测

**起源**：Brainstorm 延伸 — 空头兴趣（Short Interest）+ 轧空风险（Short Squeeze Risk）。

**盈利逻辑**：
- 高空头兴趣 + 正向动量 = 轧空设置（GameStop 模式）。
- 空头兴趣增加 + 基本面不变 = 主力看空信号（短期看空 alpha）。
- Days-to-Cover (DTC) > 5 + 正向动量 = 轧空触发概率 > 40%（Academic: Cohen et al. 2007）。
- 数据完全来自 yfinance info（免费，每月更新）。

**数据来源**：yfinance `ticker.info`（shortPercentOfFloat, shortRatio, sharesShort, 等）

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.9.1** | `phaseF9.short-interest-engine` | 空头兴趣 + 轧空风险引擎 |
| **F.9.2** | `phaseF9.short-interest-api` | `/api/short-interest/*` 路由 |
| **F.9.3** | `phaseF9.short-interest-panel` | 前端 ShortInterestPanel |
