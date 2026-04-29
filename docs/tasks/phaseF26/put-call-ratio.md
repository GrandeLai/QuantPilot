# Task F.26 — Put/Call Ratio 期权情绪面板 (Put/Call Ratio & Options Sentiment)

## 背景

Put/Call Ratio (PCR) 是最经典的期权情绪指标之一。当 PCR 极高时（大量买 Put），市场过度
悲观，往往是反向做多的信号；当 PCR 极低时（大量买 Call），市场过度乐观，往往是风险预警。

PCR 分为两种：
- **Volume PCR**：当日成交量 Put/Call 比率（短线情绪）
- **OI PCR**：持仓量 Put/Call 比率（中线持仓分布）

数据来源：yfinance 期权链（免费）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/put_call_ratio/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/put_call_ratio/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/put_call_ratio.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_put_call_ratio.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/PutCallRatioPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF26/put-call-ratio.md
```

## 验收标准（AC）

### AC-1 数据模型

- `PCRSentiment` = Literal["extreme_bearish","bearish","neutral","bullish","extreme_bullish","unknown"]
- `ExpiryPCR` dataclass：expiry, days_to_expiry, volume_pcr, oi_pcr, call_volume, put_volume
- `PCRData` dataclass：ticker, volume_pcr, oi_pcr, total_call_volume, total_put_volume,
  total_call_oi, total_put_oi, expiry_breakdown, sentiment, interpretation, as_of_date, data_available

### AC-2 计算逻辑

- volume_pcr = total_put_volume / total_call_volume（聚合所有到期日）
- oi_pcr = total_put_oi / total_call_oi
- 情绪分级（基于 volume_pcr）：
  - > 1.5 → extreme_bearish（市场恐慌，反向偏多）
  - 1.0-1.5 → bearish
  - 0.7-1.0 → neutral
  - 0.5-0.7 → bullish
  - < 0.5 → extreme_bullish（市场贪婪，反向偏空）
- expiry_breakdown：每个到期日单独计算 volume/OI PCR

### AC-3 降级策略

- 无期权数据 → data_available=True，volume_pcr=None，sentiment=unknown
- call volume = 0 → volume_pcr=None（避免除零）
- yfinance 完全失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_pcr 正常 + 除零保护 + 单腿为 0
- 覆盖：compute_put_call_ratio 正常（有期权）
- 覆盖：PCR > 1.5 → extreme_bearish；< 0.5 → extreme_bullish
- 覆盖：无期权 → data_available=True，sentiment=unknown
- 覆盖：yfinance 异常 → data_available=False
- 覆盖：expiry_breakdown 正确聚合
- 覆盖：API GET /api/put-call-ratio，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/put-call-ratio?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(put_call_ratio_router)` 注册

### AC-6 前端

- `client.ts`：PCRSentiment / ExpiryPCR / PCRData / fetchPutCallRatio
- `PutCallRatioPanel.tsx`：整体 PCR 仪表盘 + 情绪信号 + OI/Volume 对比 + 到期日明细
- RiskReviewCenter.tsx 引入并渲染 `<PutCallRatioPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_put_call_ratio.py -v
```
