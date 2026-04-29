# Phase F.2 — SEC 三合一事件流

**起源**：见 Phase F brainstorm（`prompt-cached-sutherland.md`）。最高准则——**为用户赚钱**。

**盈利逻辑**：
- 8-K **item-level diff** 捕捉脚注/风险段落的隐性变化，先于市场 1-3 日交易。
- Form 4 **集群买入**（90 日内 ≥2 高管同向，去除 10b5-1 计划单）历史超额 6-10%/180 日。
- 两类信号合并成一个面板，辅助用户在财报/公告前做方向判断。

## 任务拆分（5 个子任务）

| ID | 任务 | 范围 |
|----|------|------|
| **F.2.1** | `phaseF2.edgar-fetcher` | EDGAR REST API 客户端 + 8-K item 解析 + Form 4 XML 解析 |
| **F.2.2** | `phaseF2.edgar-diff-engine` | 8-K 前后版本 item-level 文本差分（rapidfuzz）|
| **F.2.3** | `phaseF2.form4-cluster` | Form 4 集群信号引擎（90 日窗口 + 角色过滤）|
| **F.2.4** | `phaseF2.sec-api` | `/api/sec/*` 后端路由（暴露三类数据）|
| **F.2.5** | `phaseF2.sec-events-panel` | workbench 前端 SECEventsPanel（8-K diff + Form 4 信号流）|

## MVP 标的范围

MAG7：AAPL、MSFT、GOOGL、AMZN、META、NVDA、TSLA（+ 任意用户输入 ticker）

## 数据依赖

- **EDGAR REST API**（免费，官方）：
  - submissions: `https://data.sec.gov/submissions/CIK{cik:010d}.json`
  - filing index: `https://www.sec.gov/cgi-bin/browse-edgar?...`
  - full-text search: `https://efts.sec.gov/LATEST/search-index?q=...&dateRange=custom&...`
  - Form 4 XML: `https://www.sec.gov/Archives/edgar/data/{cik}/{...}.xml`
- 限速：≤ 10 req/s，User-Agent 必须标识（`QuantPilot/1.0 admin@example.com`）
- 延迟：批处理，4-15 分钟级；不要求实时

## 不变式（继承）

- `apps/stock-assistant/` 与 `apps/quant-assistant/` 互不 import
- 所有任务需先写 task spec，acceptance PASS 才能合 PR
