# Task F.36 — 均线多空排列评分 (Moving Average Alignment Score)

## 背景

移动平均线（MA）排列是技术分析最基础的多空判断工具之一：
- **多头排列**：SMA20 > SMA50 > SMA200，且价格在三条均线上方，是长期牛市信号
- **空头排列**：SMA200 > SMA50 > SMA20，且价格在均线下方，是长期熊市信号
- **金叉/死叉**：SMA50 穿越 SMA200 向上（金叉）或向下（死叉）

本功能计算综合均线多空评分（0-100），识别趋势结构，帮助用户判断当前处于什么市场周期。

数据来源：yfinance 日线（1 年，免费）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/ma_alignment/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/ma_alignment/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/ma_alignment.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_ma_alignment.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/MAAlignmentPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF36/ma-alignment.md
```

## 验收标准（AC）

### AC-1 数据模型

- `MASignal` = Literal["full_bull","partial_bull","neutral","partial_bear","full_bear","no_data"]
- `MAAlignmentData` dataclass：
  - ticker
  - price（当前收盘价）
  - sma20, sma50, sma200（各均线值，None 表示数据不足）
  - dist_from_20（价格距 SMA20 的百分比偏差，decimal）
  - dist_from_50
  - dist_from_200
  - ma_score（0-100 综合多空评分）
  - golden_cross（bool，SMA50 是否在 SMA200 上方，即金叉状态）
  - full_bull_align（bool，SMA20 > SMA50 > SMA200 且 price > SMA20）
  - full_bear_align（bool，SMA200 > SMA50 > SMA20 且 price < SMA200）
  - signal
  - interpretation
  - as_of_date
  - data_available

### AC-2 计算逻辑

- 获取 1 年日线收盘价（`tk.history(period="1y", interval="1d")`）
- SMA20 = rolling(20).mean() 最后值；SMA50/SMA200 同理
- dist_from_X = (price - SMAX) / SMAX（可正可负）
- MA 评分（共 7 分基础，映射到 0-100）：
  - price > SMA20 → +1
  - price > SMA50 → +1
  - price > SMA200 → +1
  - SMA20 > SMA50 → +1
  - SMA50 > SMA200 → +1
  - golden_cross（SMA50 > SMA200）→ 已含在上面
  - full_bull_align → 额外 +2（MA 完美排列奖励）
  - full_bear_align → 额外 -2
  - raw score 在 [-2, 7] 之间，线性映射到 [0, 100]
- Signal（基于 ma_score）：
  - ≥ 80 → full_bull
  - ≥ 60 → partial_bull
  - ≥ 40 → neutral
  - ≥ 20 → partial_bear
  - < 20 → full_bear
  - 无数据 → no_data

### AC-3 降级策略

- 历史数据不足（< 21 个交易日）→ data_available=True，signal=no_data
- SMA200 数据不足 → sma200=None，仅计算有效均线的部分评分
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_ma_score 各输入组合
- 覆盖：_classify_signal 所有档位（含边界）
- 覆盖：compute_ma_alignment 正常 + 不足数据 + yfinance 失败
- 覆盖：API GET /api/ma-alignment?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/ma-alignment?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(ma_alignment_router)` 注册

### AC-6 前端

- `client.ts`：MASignal / MAAlignmentData / fetchMAAlignment
- `MAAlignmentPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - 信号徽章
  - MA 评分条（0-100）
  - MA 价格水位图（价格 vs SMA20/50/200 的位置关系）
  - 距各均线的偏差百分比
  - 金叉/死叉状态指示
  - 解读文字
- RiskReviewCenter.tsx 引入并渲染 `<MAAlignmentPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_ma_alignment.py -v
```
