# Task F.31 — 相关性与 Beta 监控面板 (Correlation & Beta Monitor)

## 背景

理解股票相对于市场的风险暴露是控制组合回撤的核心工具：
- **Beta > 1.5**：高杠杆市场暴露，牛市跑赢但熊市放大损失
- **低相关性（< 0.5）**：真正的 Alpha（独立于市场的超额收益）
- **R²（决定系数）**：系统性风险占总风险比例；R² 低 = 特质性风险高
- **特质波动率**：剔除市场因子后的残差波动，Ang et al. (2006) 研究表明高特质波动 = 高预期收益

数据来源：yfinance（历史价格，免费）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/beta_correlation/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/beta_correlation/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/beta_correlation.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_beta_correlation.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/BetaCorrelationPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF31/beta-correlation.md
```

## 验收标准（AC）

### AC-1 数据模型

- `BetaSignal` = Literal["high_beta","moderate_beta","low_beta","defensive","no_data"]
- `BetaCorrelationData` dataclass：
  ticker, beta_1y, beta_63d, corr_spy_1y, corr_qqq_1y, r_squared_1y,
  idio_vol_ann, signal, interpretation, as_of_date, data_available

### AC-2 计算逻辑

- 日收益率 = close.pct_change()，使用 1Y 历史（252 日）
- beta_1y = Cov(stock, SPY) / Var(SPY)（1Y 日收益率）
- beta_63d = 同上，63 日（约 3 个月）
- corr_spy_1y = 皮尔逊相关（stock_ret, spy_ret）1Y
- corr_qqq_1y = 皮尔逊相关（stock_ret, qqq_ret）1Y
- r_squared_1y = corr_spy_1y²
- idio_vol_ann = std(stock_ret - beta_1y * spy_ret) × sqrt(252)（年化特质波动率，小数）
- Signal：beta_1y ≥ 1.5 → high_beta; 1.0-1.5 → moderate_beta; 0.5-1.0 → low_beta; < 0.5 → defensive

### AC-3 降级策略

- 数据不足 < 30 日 → data_available=True, 相关字段 None, signal=no_data
- yfinance 失败（任一）→ data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_beta 正常 + 数据不足
- 覆盖：_compute_correlation 正常
- 覆盖：_compute_r_squared 正常
- 覆盖：_compute_idio_vol 正常
- 覆盖：_classify_signal 所有档位（high/moderate/low/defensive/no_data）
- 覆盖：compute_beta_correlation 正常 + yfinance 失败
- 覆盖：API GET /api/beta-correlation?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用（包括 SPY 和 QQQ）

### AC-5 API

- 路由：`GET /api/beta-correlation?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(beta_correlation_router)` 注册

### AC-6 前端

- `client.ts`：BetaSignal / BetaCorrelationData / fetchBetaCorrelation
- `BetaCorrelationPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - Beta 仪表（0-3 水平条，1.0 为中性线）
  - Beta 1Y / Beta 63d / 相关性 SPY / 相关性 QQQ / R² / 特质波动率 指标卡
  - 信号徽章（high_beta 红、moderate_beta 橙、low_beta 绿、defensive 蓝）
- RiskReviewCenter.tsx 引入并渲染 `<BetaCorrelationPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_beta_correlation.py -v
```
