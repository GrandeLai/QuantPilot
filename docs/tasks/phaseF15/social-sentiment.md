# Task F.15: Social Sentiment & Pump Risk — StockTwits 散户情绪

## 背景与目的

散户情绪极值是经典反向信号（#8 in brainstorm）：
- **极度看涨 + 高消息量** → 散户拥挤，抛压风险（pump risk）
- **极度看空** → 可能是短期超卖机会
- 盈利逻辑：散户聚集度作为**反向因子**帮用户规避 meme 股陷阱

数据源：StockTwits 公开 API（无需 API Key，free tier），
`https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json`

## 验收标准（AC）

### AC-1 引擎（social_sentiment/engine.py）
- [ ] `SentimentGrade = Literal["very_bullish","bullish","neutral","bearish","very_bearish"]`
- [ ] `PumpRiskLevel = Literal["high","elevated","low"]`
- [ ] `SocialSentimentData` dataclass：ticker, total_messages, bullish_count, bearish_count, bullish_ratio, sentiment_grade, pump_risk_level, pump_risk_score, interpretation, as_of_date, api_accessible
- [ ] `_sentiment_grade(bullish_ratio)` → grade：>0.70=very_bullish, >0.55=bullish, >0.45=neutral, >0.30=bearish, else=very_bearish
- [ ] `_pump_risk_score(bullish_ratio, message_count)` → float ∈ [0, 1]：bullish_ratio contribution + volume proxy
- [ ] `compute_social_sentiment(ticker)` → `SocialSentimentData`（始终返回，永不抛出；API 不可达时 api_accessible=False）
- [ ] 使用 httpx 或 requests 调用 StockTwits API；超时 10s
- [ ] API 不可达时 graceful degradation（返回默认值 + api_accessible=False）

### AC-2 API（api/social_sentiment.py）
- [ ] `GET /api/social-sentiment?ticker=AAPL` → 200 + SocialSentimentResponse（始终 200，包含 api_accessible 字段）
- [ ] 缺 ticker → 422
- [ ] 路由通过 `include_with_api_alias` 注册

### AC-3 前端（SocialSentimentPanel.tsx + client.ts）
- [ ] `SocialSentimentData`、`SentimentGrade`、`PumpRiskLevel` 类型加入 `client.ts`
- [ ] `fetchSocialSentiment(ticker)` 函数加入 `client.ts`
- [ ] `SocialSentimentPanel.tsx`：Bullish/Bearish 比例条 + pump_risk 指示 + API 不可达降级提示
- [ ] `SocialSentimentPanel` 加入 `RiskReviewCenter.tsx`
- [ ] TypeScript 构建无报错

### AC-4 测试（≥ 16 个）
- [ ] `_sentiment_grade` 全档边界
- [ ] `_pump_risk_score` 逻辑（高 bullish_ratio + 高 count → 高 score）
- [ ] `compute_social_sentiment` happy path
- [ ] API 不可达 → api_accessible=False，grade=neutral
- [ ] API 200 + 422

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/social_sentiment/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/social_sentiment/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/social_sentiment.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_social_sentiment.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/SocialSentimentPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF15/social-sentiment.md`
- `docs/acceptance/phaseF15/social-sentiment.md`

## pump_risk_score 公式

```
bullish_extremity = max(0.0, bullish_ratio - 0.5) * 2  # 0 if <50%, 1 if 100%
volume_factor = min(1.0, message_count / 20.0)          # saturates at 20 msgs
pump_risk_score = 0.7 * bullish_extremity + 0.3 * volume_factor
```

pump_risk_level：
- high: > 0.6
- elevated: > 0.3
- low: ≤ 0.3

## API 降级行为

StockTwits API 可能被限速或不可达：
- 发生任何 HTTP 异常或超时 → 返回 SocialSentimentData 其中 api_accessible=False，所有计数为 0
- 永不返回 None，永不 raise
