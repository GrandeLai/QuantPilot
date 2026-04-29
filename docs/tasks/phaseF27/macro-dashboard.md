# Task F.27 — 宏观仪表盘 (Macro Dashboard)

## 背景

宏观环境是所有股票投资的底层基础。本面板自动（无需用户输入）实时显示：
- VIX 恐慌指数（水平 + 52 周百分位）
- 收益率曲线形态（10 年 - 3 月 利差）及反转信号
- 美元指数（DXY）趋势
- 黄金与原油价格
- 综合宏观情绪分级（风险偏好 / 中性 / 避险）

用于指导股票仓位大小：风险偏好环境 → 加仓；避险环境 → 减仓。

数据来源：yfinance 免费宏观符号（^VIX、^TNX、^IRX、DX-Y.NYB、GC=F、CL=F）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/macro_dashboard/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/macro_dashboard/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/macro_dashboard.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_macro_dashboard.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/MacroDashboardPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF27/macro-dashboard.md
```

## 验收标准（AC）

### AC-1 数据模型

- `MacroRegime` = Literal["risk_on","neutral","risk_off","extreme_risk_off","unknown"]
- `MacroDashboardData` dataclass：vix, vix_pct_52w, yield_10y, yield_3m,
  yield_spread, yield_curve_inverted, dxy, gold, oil,
  regime, interpretation, as_of_date, data_available

### AC-2 计算逻辑

- yield_spread = yield_10y − yield_3m（百分比点差，如 0.5 表示 50 bps）
- yield_curve_inverted = yield_spread < 0
- vix_pct_52w = VIX 当前值在过去 52 周 VIX 序列中的百分位（0-100）
- 情绪分级：
  - VIX ≥ 30 OR (inverted AND vix_pct_52w ≥ 70) → extreme_risk_off
  - VIX ≥ 20 OR vix_pct_52w ≥ 50 → risk_off
  - VIX < 15 AND yield_spread > 0 AND vix_pct_52w < 40 → risk_on
  - 其余 → neutral

### AC-3 降级策略

- 单个 symbol 获取失败 → 对应字段 None，其他字段继续计算
- 全部 symbol 失败 → data_available=False
- 部分成功 → data_available=True，失败字段 None

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_classify_regime 所有四档（含 None 输入）
- 覆盖：compute_macro_dashboard 正常（所有字段）
- 覆盖：extreme_risk_off（VIX ≥ 30）
- 覆盖：risk_on（VIX < 15 + 正利差 + 低百分位）
- 覆盖：收益率曲线反转检测
- 覆盖：单个 symbol 失败降级（其他字段仍有值）
- 覆盖：全部失败 → data_available=False
- 覆盖：API GET /api/macro-dashboard 无参数 → 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/macro-dashboard`（无需 ticker 参数）
- 始终 200；通过 `include_with_api_alias(macro_dashboard_router)` 注册

### AC-6 前端

- `client.ts`：MacroRegime / MacroDashboardData / fetchMacroDashboard
- `MacroDashboardPanel.tsx`：自动加载（无搜索框）+ 情绪旗帜 + 各项宏观指标卡 + 收益率曲线状态
- RiskReviewCenter.tsx 引入并渲染 `<MacroDashboardPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_macro_dashboard.py -v
```
