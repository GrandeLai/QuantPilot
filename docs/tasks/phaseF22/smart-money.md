# Task F.22 — 大单不对称积分 / Smart Money Flow

## 背景

基于 yfinance 1 分钟 K 线（最近 5 个交易日，免费），识别机构资金进出方向。

算法：
1. 识别大单 bar（美元成交额 > 2× 5日中位数）
2. 分类方向：close > open → buy，close < open → sell
3. 今日大单买压比 vs 5 日均值，超 10 pp 差值 → 强信号

信号：smart_money_buy / smart_money_sell / accumulation / distribution / neutral / no_data

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/smart_money/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/smart_money/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/smart_money.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_smart_money.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/SmartMoneyPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF22/smart-money.md
```

## 验收标准（AC）

### AC-1 数据模型

- `SmartMoneySignal` = Literal["smart_money_buy","smart_money_sell","accumulation","distribution","neutral","no_data"]
- `DailyFlow` dataclass：date, large_buy_usd, large_sell_usd, buy_pressure_pct, total_large_usd, large_bar_count
- `SmartMoneyData` dataclass：ticker, signal, today_buy_pressure_pct, avg_5d_buy_pressure_pct,
  large_threshold_usd, daily_flows, interpretation, as_of_date, data_available

### AC-2 大单分类逻辑

- 大单阈值 = 2× 所有 bar 的美元成交额中位数
- close > open → buy（买方主导）
- close < open → sell（卖方主导）
- close == open → 不计入（doji）
- 小于阈值的 bar → 不计入

### AC-3 信号规则

| 条件 | 信号 |
|---|---|
| today > 60% 且 delta ≥ 10pp | smart_money_buy |
| today < 40% 且 delta ≤ -10pp | smart_money_sell |
| today > 55% | accumulation |
| today < 45% | distribution |
| 其他 | neutral |
| today_pct = None | no_data |

### AC-4 测试要求

- 测试总数 ≥ 16（实际 38）
- 覆盖：_classify_bars（buy/sell/doji/small/empty）
- 覆盖：_buy_pressure（100%/0%/50%/zero/60%）
- 覆盖：_compute_signal_from_pressure（所有分支）
- 覆盖：_build_interpretation（各信号类型）
- 覆盖：compute_smart_money happy path + 异常 + 空 df
- 覆盖：API GET /api/smart-money，无 ticker 422，有 ticker 200
- 所有测试 mock yfinance.download，不发真实网络请求

### AC-5 API

- 路由：`GET /api/smart-money?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(smart_money_router)` 注册

### AC-6 前端

- `client.ts`：SmartMoneySignal / DailyFlowItem / SmartMoneyData / fetchSmartMoney
- `SmartMoneyPanel.tsx`：信号 badge + 买压比条形（含 5 日均值标记）+ 日度流向迷你柱图
- RiskReviewCenter.tsx 引入并渲染 `<SmartMoneyPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_smart_money.py -v
```
