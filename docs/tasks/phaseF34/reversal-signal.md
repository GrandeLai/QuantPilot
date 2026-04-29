# Task F.34 — 短期反转信号 (Short-Term Reversal Signal)

## 背景

学术研究（Jegadeesh 1990）发现：过去 1 周到 1 个月表现最差的股票，在随后的月份往往有超额回报（短期反转效应），与长期动量（12 个月）的方向相反。本功能利用这一异象，结合 SPY 相对表现与成交量确认，生成短期反转买卖信号。

数据来源：yfinance 日线（最多 2 年，免费）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/reversal_signal/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/reversal_signal/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/reversal_signal.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_reversal_signal.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/ReversalSignalPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF34/reversal-signal.md
```

## 验收标准（AC）

### AC-1 数据模型

- `ReversalSignal` = Literal["strong_reversal_up","reversal_up","neutral","reversal_down","strong_reversal_down","no_data"]
- `ReversalData` dataclass：
  - ticker
  - ret_1w（1 周绝对收益，decimal）
  - ret_4w（4 周绝对收益，decimal）
  - rel_1w（1 周相对 SPY，decimal）
  - rel_4w（4 周相对 SPY，decimal）
  - vol_ratio（当前 5 日均量 / 20 日均量，成交量相对水平）
  - reversal_score（-100 到 100，负数偏空反转，正数偏多反转）
  - signal
  - interpretation
  - as_of_date
  - data_available

### AC-2 计算逻辑

- 获取 stock + SPY 最近 2 年日线（`tk.history(period="2y", interval="1d")`）
- 1 周 = 5 个交易日；4 周 = 20 个交易日
- 相对表现 = stock_return - spy_return（各区间）
- 成交量比 = 最近 5 日均量 / 20 日均量（股票本身）
- 反转评分（逆动量方向）：
  - rel_1w < -5% → +40；rel_1w < -2% → +25；rel_1w > 5% → -40；rel_1w > 2% → -25；其他 → 线性插值
  - rel_4w < -10% → +40；rel_4w < -5% → +25；rel_4w > 10% → -40；rel_4w > 5% → -25；其他 → 线性插值
  - vol_ratio < 0.7（缩量下跌，反转可能性更高）→ 当 rel_1w < 0 时 +20；当 rel_1w > 0 时 -20
  - 综合分 clip 到 [-100, 100]
- Signal（基于 reversal_score）：
  - ≥ 60 → strong_reversal_up
  - ≥ 30 → reversal_up
  - > -30 → neutral
  - > -60 → reversal_down
  - ≤ -60 → strong_reversal_down
  - 无数据 → no_data

### AC-3 降级策略

- 历史数据不足（< 25 个交易日）→ data_available=True，signal=no_data
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_reversal_score 各输入区间
- 覆盖：_classify_signal 所有档位（含边界）
- 覆盖：compute_reversal 正常 + 不足数据 + yfinance 失败
- 覆盖：API GET /api/reversal-signal?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/reversal-signal?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(reversal_signal_router)` 注册

### AC-6 前端

- `client.ts`：ReversalSignal / ReversalData / fetchReversalSignal
- `ReversalSignalPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - 信号徽章（颜色：强多反转绿、弱多绿、中性灰、弱空橙、强空红）
  - 反转评分仪表条（-100 到 +100）
  - 1W/4W 相对表现对比
  - 成交量比值
  - 解读文字
- RiskReviewCenter.tsx 引入并渲染 `<ReversalSignalPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_reversal_signal.py -v
```
