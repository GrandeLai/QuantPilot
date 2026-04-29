# Task F.14: Price Momentum Signal — Jegadeesh-Titman 动量因子

## 背景与目的

Jegadeesh & Titman (1993) 是量化金融里最经典的研究之一：
- **12-1 月动量**（过去 12 个月 skip 最近 1 个月的收益）是最稳健的中频 alpha 来源之一
- 高动量股票在未来 3-12 个月持续跑赢市场；低动量（近期大跌）股票持续跑输
- Fama-French 5 因子模型中动量是标准构成部分
- **可度量收益**：多空组合年化 alpha ~1%/月（Jegadeesh & Titman 1993, 2001）

本任务实现动量因子引擎（`momentum/engine.py`）、API 端点（`api/momentum.py`）和前端面板（`MomentumPanel.tsx`）。

## 验收标准（AC）

### AC-1 引擎（momentum/engine.py）
- [ ] `MomentumGrade = Literal["strong_momentum","momentum","neutral","reversal_risk","strong_reversal"]`
- [ ] `MomentumSignal` dataclass：ticker, momentum_12_1, return_1m, return_3m, return_6m, high_52w, low_52w, current_price, proximity_52w_high, grade, interpretation, as_of_date
- [ ] `_momentum_grade(pct)` → grade：>20%=strong_momentum, >5%=momentum, >-5%=neutral, >-20%=reversal_risk, else=strong_reversal
- [ ] `compute_momentum_signal(ticker)` → `MomentumSignal | None`：数据不足返回 None，不抛异常
- [ ] 使用 yfinance `ticker.history(period="13mo")` 取历史收盘价
- [ ] 12-1 月动量 = price(-1m) / price(-12m) - 1（-1m 和 -12m 基于交易日近似）
- [ ] 52 周高低通过 rolling 252 日窗口计算
- [ ] proximity_52w_high = current_price / high_52w（越接近 1.0 越强）

### AC-2 API（api/momentum.py）
- [ ] `GET /api/momentum?ticker=AAPL` → 200 + MomentumSignalResponse
- [ ] 无数据 → 404
- [ ] 缺 ticker → 422
- [ ] 路由通过 `include_with_api_alias` 注册

### AC-3 前端（MomentumPanel.tsx + client.ts）
- [ ] `MomentumSignalData`、`MomentumGrade` 类型加入 `client.ts`
- [ ] `fetchMomentumSignal(ticker)` 函数加入 `client.ts`
- [ ] `MomentumPanel.tsx` 展示：12-1m/1m/3m/6m 收益率 + 52w 高低位置仪表 + grade badge + 解读
- [ ] `MomentumPanel` 加入 `RiskReviewCenter.tsx`
- [ ] TypeScript 构建无报错

### AC-4 测试（≥ 18 个）
- [ ] `_momentum_grade` 全档边界
- [ ] `compute_momentum_signal` happy path：收益率和 grade 正确
- [ ] 数据不足 → None
- [ ] 异常 → None
- [ ] API 200/404/422

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/momentum/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/momentum/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/momentum.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_momentum.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/MomentumPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF14/momentum-signal.md`
- `docs/acceptance/phaseF14/momentum-signal.md`
