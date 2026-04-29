# Task F.17: Pre-Earnings Expected Move (Implied ±% Move)

## 背景与目的

财报前，期权市场对预期波动隐含了"预期涨跌幅"（expected move）：
- 以 ATM (at-the-money) straddle 价格 / 当前股价 ≈ 市场预期的 ±1σ 涨跌幅
- 在持有股票或期权时，了解市场隐含的财报摆幅可以帮助：
  - 持股者：决定是否在财报前卖出（避免 IV crush 或超预期下跌）
  - 期权卖方：评估是否出售 straddle/strangle 收 premium
  - 期权买方：判断单边期权是否 priced in 太多 premium

数据源：yfinance 期权链（免费）+ yfinance calendar

## 验收标准（AC）

### AC-1 引擎（earnings_move/engine.py）

- [ ] `EarningsMoveGrade = Literal["large_expected","medium_expected","small_expected","no_data"]`
- [ ] `EarningsMoveData` dataclass：ticker, next_earnings_date(str|None), days_to_earnings(int|None), expected_move_pct(float|None), atm_strike(float|None), straddle_price(float|None), current_price(float|None), grade(EarningsMoveGrade), interpretation(str), as_of_date(date), data_available(bool)
- [ ] `_earnings_move_grade(pct)` → grade：> 10=large_expected, > 5=medium_expected, >=0=small_expected
- [ ] `compute_earnings_move(ticker)` → `EarningsMoveData`（始终返回，永不抛出）
  - 从 yfinance calendar 获取下次财报日期
  - 找到财报日期之后的最近期权到期日
  - 计算 ATM strike（最接近 current_price 的行权价）
  - expected_move_pct = (atm_call_price + atm_put_price) / current_price × 100
  - 任何异常 → data_available=False

### AC-2 API（api/earnings_move.py）

- [ ] `GET /api/earnings-move?ticker=AAPL` → 200 + EarningsMoveResponse（始终 200）
- [ ] 缺 ticker → 422
- [ ] 路由通过 `include_with_api_alias` 注册

### AC-3 前端

- [ ] `EarningsMoveData`、`EarningsMoveGrade` 类型加入 `client.ts`
- [ ] `fetchEarningsMove(ticker)` 加入 `client.ts`
- [ ] `EarningsMovePanel.tsx`：倒计时 + expected_move_pct 显示 + grade badge + 降级提示
- [ ] `EarningsMovePanel` 加入 `RiskReviewCenter.tsx`
- [ ] TypeScript 构建无报错

### AC-4 测试（≥ 16 个）

- [ ] `_earnings_move_grade` 边界
- [ ] `compute_earnings_move` happy path（mocked yfinance）
- [ ] yfinance 不可达 → data_available=False，永不抛出
- [ ] API 200 + 422

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/earnings_move/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/earnings_move/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/earnings_move.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_earnings_move.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/EarningsMovePanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF17/earnings-move.md`
- `docs/acceptance/phaseF17/earnings-move.md`

## Expected Move 公式

```
ATM strike = argmin |strike - current_price|
straddle_price = ATM_call_last_price + ATM_put_last_price
expected_move_pct = straddle_price / current_price * 100
```

Grade:
- large_expected: > 10%
- medium_expected: > 5%
- small_expected: >= 0%
- no_data: data_available=False

## 降级行为

- yfinance 无 calendar / 无期权 / 任何异常 → data_available=False
- 永不 raise，永不返回 None
