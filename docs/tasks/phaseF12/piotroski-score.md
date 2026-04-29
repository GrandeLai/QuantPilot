# Task F.12: Piotroski F-Score — 盈利质量财务健康评分

## 背景与目的

Piotroski F-Score (Piotroski 2000) 是 9 个二元财务标准的加总（满分 9 分），
系统性识别高质量 vs 低质量盈利股票：
- **盈利驱动**：高 F-Score (7-9) 年化超额 23%；低 F-Score (0-2) 显著负 alpha；
  多空组合年化 alpha 7.5%（23 个国家实证验证）。
- **本任务** 将 Piotroski F-Score 接入 `quant_signals/engine.py`，
  暴露 `/api/quant-signals/piotroski` 端点，并在 `QuantSignalsPanel.tsx` 新增 PiotroskiSection，
  完成"盈利质量三件套"（Beneish ✓ Sloan ✓ Piotroski ⬅）。

## 验收标准（AC）

### AC-1 引擎（engine.py）
- [ ] `PiotroskiCriteria` dataclass，含 9 个 bool 字段（f1~f9，见下表）
- [ ] `PiotroskiScore` dataclass，含 `ticker`, `f_score: int (0-9)`, `grade`, `criteria`, `interpretation`, `as_of_date`
- [ ] `_piotroski_grade(score) -> Literal["strong","neutral","weak"]`：score ≥ 7 = strong，≤ 3 = weak，else neutral
- [ ] `compute_piotroski_score(ticker: str) -> PiotroskiScore | None`：
  数据不足/异常返回 None，不抛出异常
- [ ] 所有 9 个标准按下表计算正确

| # | 字段 | 标准 |
|---|---|---|
| F1 | `roa_positive` | ROA = NI / avg_TA > 0 |
| F2 | `cfo_positive` | Operating Cash Flow > 0 |
| F3 | `roa_improving` | ROA(t) > ROA(t-1) |
| F4 | `accruals_ok` | CFO/avg_TA > ROA （现金盈利优于应计盈利）|
| F5 | `leverage_ok` | 长期负债率 (LTD/avg_TA) 下降（或 t 年无长期负债） |
| F6 | `liquidity_ok` | 流动比率 (CA/CL) 上升 |
| F7 | `no_dilution` | 流通股数量未增加 |
| F8 | `margin_ok` | 毛利率上升 |
| F9 | `turnover_ok` | 总资产周转率 (Revenue/avg_TA) 上升 |

### AC-2 API（quant_signals.py）
- [ ] `PiotroskiScoreResponse` Pydantic model，含全部字段
- [ ] `GET /api/quant-signals/piotroski?ticker=AAPL` 返回 200 + PiotroskiScoreResponse
- [ ] 数据不足时返回 404
- [ ] 缺 ticker 参数时返回 422
- [ ] `QuantSignalsSummaryResponse` 新增 `piotroski: PiotroskiScoreResponse | None`
- [ ] `GET /api/quant-signals/summary` 并发返回 4 个信号（beneish/russell/sloan/piotroski）

### AC-3 前端（QuantSignalsPanel.tsx + client.ts）
- [ ] `PiotroskiScoreData` 类型，`PiotroskiCriteriaData` 类型加入 `client.ts`
- [ ] `QuantSignalsSummary` 新增 `piotroski: PiotroskiScoreData | null`
- [ ] `PiotroskiSection` 子组件：9 个标准显示为绿✓/红✗，F-score 数字 + grade badge
- [ ] `QuantSignalsPanel` 主组件渲染 PiotroskiSection，空态和无数据降级均正确
- [ ] 前端 TypeScript 构建无报错

### AC-4 测试
- [ ] ≥ 20 个单元测试，覆盖：
  - `_piotroski_grade` 的全部 3 档及边界
  - 每个标准的 True / False 分支
  - `compute_piotroski_score` happy path：score 正确、grade 正确
  - 数据不足（empty df）返回 None
  - 异常（网络错误）返回 None
  - API 200 / 404 / 422
  - summary 包含 piotroski 字段

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/quant_signals/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/quant_signals.py`
- `apps/stock-assistant/backend/tests/test_piotroski_score.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/QuantSignalsPanel.tsx`
- `docs/tasks/phaseF12/piotroski-score.md`
- `docs/acceptance/phaseF12/piotroski-score.md`

## 数据来源

yfinance：`ticker.financials`, `ticker.cashflow`, `ticker.balance_sheet`, `ticker.info`
- `Total Revenue` → gross margin = (Revenue - COGS) / Revenue，COGS = Revenue - Gross Profit
- `Long Term Debt`, `Current Assets`, `Current Liabilities`, `Total Assets`
- `shares_outstanding` via `ticker.info["sharesOutstanding"]`
- 需要最新两期年度数据（t 和 t-1）

## 不变式

- 继承 CLAUDE.md 不变式
- 不改动 `apps/quant-assistant/` 任何文件
