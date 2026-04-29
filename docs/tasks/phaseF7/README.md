# Phase F.7 — 加密 Token 解锁日历 + 抛压模型

**起源**：Brainstorm 候选 #18 — 加密 token 解锁日历 + 抛压模型。

**盈利逻辑**：
- Token 解锁 = 内部人/早期投资者获得解除锁定的代币，有强烈出售动机。
- 历史数据：大额解锁（>5% 流通量）解锁前 7 日平均下跌 3-8%，解锁后 14 日反弹 2-5%。
- 策略：解锁前做空 → 解锁后 14 日反弹买入。免费数据足够支撑 MVP。

**数据来源**：
- DefiLlama Emissions API（免费，覆盖 200+ 协议）
- Coingecko 价格/市值数据（免费 API）

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.7.1** | `phaseF7.token-unlock-engine` | 解锁日历引擎 + 抛压评分 |
| **F.7.2** | `phaseF7.token-unlock-api` | `/api/token-unlocks/*` 路由 |
| **F.7.3** | `phaseF7.token-unlock-panel` | 前端 TokenUnlockPanel |
