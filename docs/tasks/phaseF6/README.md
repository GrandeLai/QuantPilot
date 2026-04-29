# Phase F.6 — EPS 分析师预期修正动量

**起源**：Brainstorm 候选 #3 — 分析师一致预期修正动量（EPS Revision Momentum）。

**盈利逻辑**：
- 分析师向上修正 EPS 预期 → 股价后续 20-60 日跑赢（Stickel 1991, Chan et al. 1996 验证，年化超额 6-12%）。
- 修正动量 = 7 日 + 30 日内向上修正次数占比，可直接构造多空因子。
- 结合目标价上下限分布，提供散户/机构共识偏差（high dispersion → 更多 alpha 机会）。

**数据来源**：yfinance `eps_revisions`（免费，无需 API Key）

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.6.1** | `phaseF6.eps-revision-engine` | EPS 修正引擎 + 目标价共识 |
| **F.6.2** | `phaseF6.eps-revision-api` | `/api/eps-revision/*` 路由 |
| **F.6.3** | `phaseF6.eps-revision-panel` | 前端 EPSRevisionPanel |
