# Task F.29 — 期权最大痛苦值面板 (Options Max Pain Calculator)

## 背景

Max Pain（最大痛苦值）= 期权到期时，所有期权持有者（买方）总损失最大的标的价格，
即做市商/卖方损失最小的价格。研究表明标的价格在到期日前后有向 Max Pain 靠拢的倾向
（"pin" 效应），每周到期日尤为明显。

策略应用：
- **价格钉子（Pin Risk）**：到期日前 1-2 天，标的接近 Max Pain → 价格被"钉住"
- **方向性择时**：当前价格高于 Max Pain → 做空/卖 Call 有优势；低于 Max Pain → 做多
- **距离阈值**：距离 < 2% 为钉子区；2-5% 为近端；> 5% 为远端

数据来源：yfinance（免费期权链）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/max_pain/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/max_pain/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/max_pain.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_max_pain.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/MaxPainPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF29/max-pain.md
```

## 验收标准（AC）

### AC-1 数据模型

- `MaxPainSignal` = Literal["pin_zone","bullish_pull","bearish_pull","weak_pull","unknown"]
- `ExpiryMaxPain` dataclass：expiry, dte, max_pain_strike, current_price,
  distance_pct, total_call_oi, total_put_oi, signal
- `MaxPainData` dataclass：ticker, current_price, as_of_date, data_available,
  interpretation, expiries: list[ExpiryMaxPain]

### AC-2 计算逻辑

- Max Pain Strike = argmin_K Σ [call_OI_K * max(0, K-spot) + put_OI_K * max(0, spot-K)]
  over all evaluated spot prices (i.e. every strike in chain)
- distance_pct = (max_pain - current_price) / current_price × 100
- Signal：
  - |distance| < 2% → pin_zone
  - distance > 0 and 2-5% → bullish_pull (price below max pain → up pull)
  - distance < 0 and 2-5% → bearish_pull (price above max pain → down pull)
  - |distance| ≥ 5% → weak_pull (weakening magnet)
  - 无数据 → unknown
- 取最近 4 个到期日（DTE 1-45）

### AC-3 降级策略

- 无期权数据 → data_available=True, expiries=[], interpretation 说明
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_max_pain 正常 + 空链
- 覆盖：_classify_signal 所有档位（pin_zone / bullish_pull / bearish_pull / near_pin / unknown）
- 覆盖：compute_max_pain 正常（有期权）
- 覆盖：无期权 → data_available=True, expiries=[]
- 覆盖：yfinance 异常 → data_available=False
- 覆盖：API GET /api/max-pain?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/max-pain?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(max_pain_router)` 注册

### AC-6 前端

- `client.ts`：MaxPainSignal / ExpiryMaxPain / MaxPainData / fetchMaxPain
- `MaxPainPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - 每个到期日：Max Pain 价格 + 距离 + 信号 + DTE
  - 可视化：当前价格 vs Max Pain 的条形/标注
  - 信号徽章（pin_zone 金色、bullish_pull 绿、bearish_pull 红）
- RiskReviewCenter.tsx 引入并渲染 `<MaxPainPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_max_pain.py -v
```
