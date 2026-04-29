# Task F.16: Unusual Options Activity Scanner (UOA)

## 背景与目的

当机构在重大事件前建仓时，往往选择期权而非现货，留下可识别的"指纹"：特定合约的成交量远超未平仓量（volume >> OI）。
UOA（Unusual Options Activity）是散户可观察到的少数"聪明钱"信号之一，被 Barchart、Unusual Whales 等平台作为核心功能，月费 $30-$100。

数据源：yfinance 免费期权链（同 GEXPanel 使用的数据）

## 盈利逻辑

- volume/OI 比值极大（> 3）的期权合约往往预示方向性押注
- 极端的 Put/Call 成交量失衡（看跌买入聚集）是反向或对冲信号
- 大幅溢价买入（ask side）的 sweep order 与后续走势相关

## 验收标准（AC）

### AC-1 引擎（unusual_options/engine.py）

- [ ] `OptionsGrade = Literal["bullish_unusual","bearish_unusual","mixed_unusual","neutral"]`
- [ ] `UnusualContract` dataclass: ticker, expiry, strike, option_type("call"/"put"), volume, open_interest, volume_oi_ratio, implied_volatility, in_the_money, is_unusual(bool)
- [ ] `UnusualOptionsData` dataclass: ticker, total_unusual_calls, total_unusual_puts, total_call_volume, total_put_volume, put_call_ratio, grade, top_unusual(list[UnusualContract], top 5), interpretation, as_of_date, data_available
- [ ] `_volume_oi_ratio_threshold = 3.0` — 超过此值视为 unusual
- [ ] `_put_call_grade(put_call_ratio)` → grade：< 0.5=bullish_unusual, < 0.8=neutral, < 1.5=neutral, >=1.5=bearish_unusual; 若 total_unusual_calls > 2*total_unusual_puts=bullish_unusual
- [ ] `compute_unusual_options(ticker)` → `UnusualOptionsData`（始终返回，永不抛出；yfinance 失败时 data_available=False）
- [ ] 对每个近期到期日（最近 3 个），扫描 call 和 put chain
- [ ] 使用 yfinance `ticker.options` + `ticker.option_chain(expiry)`
- [ ] 超时/异常时优雅降级（data_available=False）

### AC-2 API（api/unusual_options.py）

- [ ] `GET /api/unusual-options?ticker=AAPL` → 200 + UnusualOptionsResponse（始终 200）
- [ ] 缺 ticker → 422
- [ ] 路由通过 `include_with_api_alias` 注册

### AC-3 前端

- [ ] `UnusualContract`、`UnusualOptionsData`、`OptionsGrade` 类型加入 `client.ts`
- [ ] `fetchUnusualOptions(ticker)` 加入 `client.ts`
- [ ] `UnusualOptionsPanel.tsx`：Put/Call 比例条 + top unusual contracts 列表 + grade badge + 降级提示
- [ ] `UnusualOptionsPanel` 加入 `RiskReviewCenter.tsx`
- [ ] TypeScript 构建无报错

### AC-4 测试（≥ 16 个）

- [ ] `_put_call_grade` 边界
- [ ] `volume_oi_ratio` 阈值逻辑
- [ ] `compute_unusual_options` happy path（mocked yfinance）
- [ ] yfinance 不可达 → data_available=False，永不抛出
- [ ] API 200 + 422

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/unusual_options/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/unusual_options/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/unusual_options.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_unusual_options.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/UnusualOptionsPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF16/unusual-options.md`
- `docs/acceptance/phaseF16/unusual-options.md`

## Grade 逻辑

```
if total_unusual_calls > 2 * total_unusual_puts and total_unusual_calls >= 2:
    grade = "bullish_unusual"
elif total_unusual_puts > 2 * total_unusual_calls and total_unusual_puts >= 2:
    grade = "bearish_unusual"
elif total_unusual_calls + total_unusual_puts >= 3:
    grade = "mixed_unusual"
else:
    grade = "neutral"
```

Put/Call ratio = total_put_volume / max(1, total_call_volume)

## API 降级行为

yfinance 期权链可能不可达（网络超时、无期权数据）：
- 发生任何异常 → data_available=False，返回默认值
- 永不返回 None，永不 raise
