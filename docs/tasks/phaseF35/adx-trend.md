# Task F.35 — ADX 趋势强度指标 (ADX Trend Strength)

## 背景

ADX（Average Directional Index，平均方向指数）由 Wilder (1978) 提出，是最权威的趋势强度测量工具。
ADX 不区分方向（只测量趋势强度），配合 +DI/-DI（方向性指标）确认趋势方向。
- ADX < 20：盘整（无趋势），适合均值回归策略
- ADX 20-40：趋势初现，适合趋势追踪入场
- ADX > 40：强趋势，持仓不应逆势

数据来源：yfinance 日线（免费）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/adx_trend/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/adx_trend/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/adx_trend.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_adx_trend.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/ADXTrendPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF35/adx-trend.md
```

## 验收标准（AC）

### AC-1 数据模型

- `TrendSignal` = Literal["strong_uptrend","uptrend","ranging","downtrend","strong_downtrend","no_data"]
- `ADXData` dataclass：
  - ticker
  - adx（ADX 值，0-100）
  - plus_di（+DI 值）
  - minus_di（-DI 值）
  - atr（Average True Range，绝对值）
  - signal
  - trend_strength（"strong" / "moderate" / "weak" / "none"，仅基于 ADX 大小）
  - interpretation
  - as_of_date
  - data_available

### AC-2 计算逻辑

- 获取最近 1 年日线 OHLC（`tk.history(period="1y", interval="1d")`）
- 使用 Wilder 平滑（period=14）计算 +DM / -DM / TR
- ATR = Wilder MA(TR, 14)
- +DI = 100 × Wilder_MA(+DM, 14) / ATR
- -DI = 100 × Wilder_MA(-DM, 14) / ATR
- DX = 100 × |+DI - -DI| / (+DI + -DI)
- ADX = Wilder_MA(DX, 14)
- Signal：
  - ADX ≥ 40 and +DI > -DI → strong_uptrend
  - ADX ≥ 20 and +DI > -DI → uptrend
  - ADX ≥ 40 and -DI > +DI → strong_downtrend
  - ADX ≥ 20 and -DI > +DI → downtrend
  - ADX < 20 → ranging
  - 无数据 → no_data
- trend_strength：ADX ≥ 40 → "strong"；ADX ≥ 25 → "moderate"；ADX ≥ 15 → "weak"；< 15 → "none"

### AC-3 降级策略

- 历史数据不足（< 30 个交易日）→ data_available=True，signal=no_data
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_wilder_smooth 基本平滑行为
- 覆盖：_compute_adx 正常 + 不足数据（返回 None）
- 覆盖：_classify_signal 所有档位
- 覆盖：compute_adx_trend 正常 + 不足数据 + yfinance 失败
- 覆盖：API GET /api/adx-trend?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/adx-trend?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(adx_trend_router)` 注册

### AC-6 前端

- `client.ts`：TrendSignal / ADXData / fetchADXTrend
- `ADXTrendPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - ADX 仪表条（0-100，25 和 40 阈值线标注）
  - 信号徽章
  - +DI / -DI / ATR 指标卡
  - 趋势强度等级标注
  - 解读文字
- RiskReviewCenter.tsx 引入并渲染 `<ADXTrendPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_adx_trend.py -v
```
