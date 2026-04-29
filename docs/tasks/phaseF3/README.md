# Phase F.3 — TLH + TWAP/VWAP + TCA

**起源**：见 Phase F brainstorm（`prompt-cached-sutherland.md`）。最高准则——**为用户赚钱**。

**盈利逻辑**：
- TLH：美股长短期资本利得税差 12-22%；年化税后多赚 0.5-1.5%（Vanguard 研究）。
- TWAP/VWAP 分单：单笔 > ADV 0.5% 的订单按 5% 切分，降低 5-15 bps 滑点。
- TCA：每笔成交后对比 arrival/VWAP/close，持续发现 broker 路由劣化。

## 任务拆分

| ID | 任务 | 范围 |
|----|------|------|
| **F.3.1** | `phaseF3.tlh-engine` | TLH 引擎（lot P&L + wash sale 守门 + ETF 替代推荐） |
| **F.3.2** | `phaseF3.tlh-api` | `/api/tlh/*` 后端路由 |
| **F.3.3** | `phaseF3.tlh-panel` | 前端 TLHPanel |
| **F.3.4** | `phaseF3.execution-engine` | TWAP/VWAP 分单 + TCA 引擎 |
| **F.3.5** | `phaseF3.execution-api` | `/api/execution/*` 路由 |

## 合规声明

- **不构成税务建议**：UI 显著声明，推荐用户找 CPA 复核
- **wash sale 判断保守**：30 天窗口严格执行，不猜测 IRS 边界
- **审计 trace**：所有推荐操作须记录，方便用户事后复核
