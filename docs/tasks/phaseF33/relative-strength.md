# Task F.33 — 相对强度评分 (Relative Strength Score)

## 背景

IBD（Investor's Business Daily）的 RS Rating 是最广泛使用的股票相对强度指标之一：
将股票在 12 个月的价格表现与市场整体进行比较，以 1-99 百分位衡量。
相对强度高的股票（RS > 80）在历史上有显著超额收益。

本功能基于 yfinance 免费数据，计算每只股票相对 SPY（标准普尔 500 ETF）在多个时间框架的相对收益率，
给出综合 RS 分数（0-100 分）及交易信号。

数据来源：yfinance（免费，最多 2 年日线数据）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/relative_strength/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/relative_strength/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/relative_strength.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_relative_strength.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/RelativeStrengthPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF33/relative-strength.md
```

## 验收标准（AC）

### AC-1 数据模型

- `RSSignal` = Literal["strong_outperformer","outperformer","neutral","underperformer","strong_underperformer","no_data"]
- `PeriodRS` dataclass：period（"1M"/"3M"/"6M"/"12M"），stock_return，spy_return，relative_return（股票收益率 - SPY 收益率）
- `RSData` dataclass：ticker，periods（list[PeriodRS]），rs_score（0-100 综合分，基于加权相对表现），
  signal，interpretation，as_of_date，data_available

### AC-2 计算逻辑

- 获取 SPY + stock 2 年日线收盘价（`tk.history(period="2y", interval="1d")`）
- 计算 1M/3M/6M/12M 各区间总收益率（起始价→末价，不用 pct_change 累计）
- 相对收益 = stock_return - spy_return（绝对差，单位百分比）
- 加权综合 RS 分数（仿 IBD 加权，从近到远权重 2:1.5:1:0.5，各区间归一化后加权平均）
  - 单区间分数 = 将相对表现 clip 到 [-50%,+50%] 后线性映射到 [0,100]（-50%→0，+50%→100，0%→50）
  - rs_score = 加权平均（四个区间分数）
- Signal（基于 rs_score）：
  - ≥ 80 → strong_outperformer
  - ≥ 60 → outperformer
  - ≥ 40 → neutral
  - ≥ 20 → underperformer
  - < 20 → strong_underperformer
  - 无数据 → no_data

### AC-3 降级策略

- 历史数据不足（< 20 个交易日）→ data_available=True，periods=[]，signal=no_data
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_period_returns 正常 + 不足数据
- 覆盖：_period_to_rs_score 各输入范围
- 覆盖：_classify_signal 所有档位
- 覆盖：compute_rs 正常 + 不足数据 + yfinance 失败
- 覆盖：API GET /api/relative-strength?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/relative-strength?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(relative_strength_router)` 注册

### AC-6 前端

- `client.ts`：RSSignal / PeriodRS / RSData / fetchRelativeStrength
- `RelativeStrengthPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - RS 评分仪表条（0-100，阈值线标注）
  - 信号徽章
  - 四个时间框架对比表格（股票收益 / SPY 收益 / 超额收益，超额正绿负红）
  - 解读文字
- RiskReviewCenter.tsx 引入并渲染 `<RelativeStrengthPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_relative_strength.py -v
```
