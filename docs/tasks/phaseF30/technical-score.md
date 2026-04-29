# Task F.30 — 技术动量评分面板 (Technical Momentum Score)

## 背景

技术分析信号的组合评分是量化投资中成熟的短中期 alpha 因子。多个技术指标的一致方向
（"confirmation"）显著优于单一指标：

- **RSI**：超买/超卖（Wilder, 1978），14 日 RSI>70 为超买，<30 为超卖
- **MACD**：动量反转（Appel, 1979），MACD 线穿越信号线为交叉信号
- **布林带位置**：当前价格在带内的相对位置（0-100%）
- **成交量比**：当前成交量 / 20 日平均，> 2 = 放量确认
- **52 周位置**：当前价格在 52 周高低区间的百分位
- **综合评分**：多信号加权得分（-100 到 +100），驱动最终信号

数据来源：yfinance（免费，历史价格）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/technical_score/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/technical_score/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/technical_score.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_technical_score.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/TechnicalScorePanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF30/technical-score.md
```

## 验收标准（AC）

### AC-1 数据模型

- `TechSignal` = Literal["strong_buy","buy","neutral","sell","strong_sell","no_data"]
- `TechnicalScoreData` dataclass：ticker, current_price, rsi14, macd_line, macd_signal,
  macd_histogram, bb_position, volume_ratio, week52_position,
  composite_score, signal, interpretation, as_of_date, data_available

### AC-2 计算逻辑

- RSI(14)：标准 Wilder RSI（EWM with alpha=1/14）
- MACD：EMA12 - EMA26；Signal = EMA9(MACD)；Histogram = MACD - Signal
- BB：(close - lower) / (upper - lower) × 100，BB20，2σ
- Volume ratio：最新成交量 / 20 日平均
- 52w position：(close - 52w_low) / (52w_high - 52w_low) × 100
- Composite score（-100 到 +100）：5 个分项各±20 分加权：
  - RSI < 30 → +20, RSI > 70 → -20; else → 线性插值到 0
  - MACD histogram > 0 → +20; < 0 → -20（基于 histogram 符号）
  - BB position < 20 → +20; > 80 → -20; else → 0
  - Volume ratio > 2 + (close > prev_close) → +10; volume > 2 + down → -10; else → 0
  - 52w position < 30 → +10; > 70 → -10（均值回归势力）反向
- Signal：score ≥ 60 → strong_buy; 30-60 → buy; -30 to 30 → neutral;
  -60 to -30 → sell; ≤ -60 → strong_sell

### AC-3 降级策略

- 数据不足（< 30 日）→ data_available=True，部分字段 None
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_rsi、_compute_macd、_compute_bb、_compute_composite_score
- 覆盖：_classify_signal 所有档位
- 覆盖：compute_technical_score 正常 + 数据不足 + yfinance 失败
- 覆盖：API GET /api/technical-score?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/technical-score?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(technical_score_router)` 注册

### AC-6 前端

- `client.ts`：TechSignal / TechnicalScoreData / fetchTechnicalScore
- `TechnicalScorePanel.tsx`：
  - ticker 输入框 + 分析按钮
  - 综合评分仪表盘（-100 到 +100 水平条）
  - 5 个分项指标卡：RSI + MACD histogram + BB位置 + 成交量比 + 52w位置
  - 信号徽章
- RiskReviewCenter.tsx 引入并渲染 `<TechnicalScorePanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_technical_score.py -v
```
