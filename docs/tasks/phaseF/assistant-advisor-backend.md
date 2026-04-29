# Task phaseF.assistant-advisor-backend: 实现 assistant advisor 后端路由

**Phase**: Phase F.1 修复
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

assistant frontend（5174 端口）调用了以下后端路由，但均未实现：

| 路由 | 调用方 | 状态 |
|------|--------|------|
| `GET /api/advisor/overview` | PortfolioOverview, ReviewAsk | ❌ 404 |
| `GET /api/advisor/crypto/opportunities?symbol=...` | OpportunityPool, RebalanceSuggestions, ReviewAsk | ❌ 404 |
| `GET /api/advisor/crypto/risks?symbol=...` | RiskRadar, RebalanceSuggestions, ReviewAsk | ❌ 404 |
| `GET /api/crypto/research/latest?symbol=...` | OpportunityPool, RebalanceSuggestions, ReviewAsk | ❌ 404 |
| `POST /api/crypto/research/optimize` | OpportunityPool, RebalanceSuggestions | ❌ 404 |
| `GET /api/crypto/research/optimize/latest?symbol=...&strategy_id=...` | OpportunityPool, RebalanceSuggestions | ❌ 404 |

当前结果：UI 一片 "暂未接入" 空状态（graceful，但无数据）。

### 目标

用已有数据源（crypto_derivs 模块 + portfolio manager）实现上述路由 MVP，让 assistant frontend 5 个 tab 均显示真实数据。

### 实现策略

#### 数据来源

- **advisor/overview**：复用 portfolio manager 内存快照（`_manager.summary()`）
- **advisor/crypto/opportunities + risks**：
  - 从 Binance/OKX 拉取资金费率历史（90 条 × 2 所）
  - 用 `funding_extreme_signal` 生成机会 / 风险 AdvisorCard
  - 信号逻辑：`contrarian_long` → 机会；`contrarian_short` → 风险；中间态也生成轻度卡片
- **crypto/research/latest**：
  - 同样基于 funding percentile 推断市场机制（overheated_bull / bull_trending / ranging / bear_ranging / bear_trending）
  - 映射到推荐策略 ID 和时间框架
- **crypto/research/optimize / optimize/latest**：
  - MVP 返回每种机制对应的固定最优参数（基于规则，非实时网格搜索）

#### 新建文件

- `apps/stock-assistant/backend/src/quantpilot_stock/api/advisor.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_research.py`

#### 修改文件

- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`（注册两个新 router）

#### 不动文件

- 所有前端
- 后端其他模块
- workbench
- quant-assistant

### 不做什么

- 不做完整参数网格搜索（optimize MVP = 规则参数）
- 不引入新外部数据源（只用 Binance/OKX 公共 API）
- 不改 portfolio manager 逻辑

---

## 验收标准

- [ ] **AC-1**: 路由存在（不 404）
  - `grep -q "advisor" apps/stock-assistant/backend/src/quantpilot_stock/api/advisor.py`
  - `grep -q "crypto_research\|crypto/research" apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_research.py`
- [ ] **AC-2**: advisor + crypto_research 已注册进 main.py
  - `grep -q "advisor_router" apps/stock-assistant/backend/src/quantpilot_stock/main.py`
  - `grep -q "crypto_research_router" apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- [ ] **AC-3**: overview 返回正确 schema
  - advisor.py 中包含 `net_worth` 字段
  - advisor.py 中包含 `cash_ratio` 字段
  - advisor.py 中包含 `generated_at` 字段
- [ ] **AC-4**: opportunities/risks 使用 funding 信号（引用 analytics）
  - `grep -q "funding_extreme_signal\|fetch_binance_funding_history\|fetch_okx_funding_history" apps/stock-assistant/backend/src/quantpilot_stock/api/advisor.py`
- [ ] **AC-5**: crypto_research 返回 market_regime
  - `grep -q "market_regime\|recommended_strategy_ids" apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_research.py`
- [ ] **AC-6**: 测试通过
  - `(cd apps/stock-assistant/backend && GVM_ROOT=/Users/bytedance/.gvm uv run --group dev pytest tests/test_advisor.py tests/test_crypto_research.py -v)` 退出码 0
- [ ] **AC-7**: type-check 通过
  - `(cd apps/stock-assistant/backend && GVM_ROOT=/Users/bytedance/.gvm uv run mypy src/)` 退出码 0
- [ ] **AC-8**: 不动 workbench / quant-assistant / common
  - `git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/quant-assistant/ common/` 输出为空

---

## 测试集合

```bash
export GVM_ROOT=/Users/bytedance/.gvm
(cd apps/stock-assistant/backend && uv run --group dev pytest tests/test_advisor.py tests/test_crypto_research.py -v)
(cd apps/stock-assistant/backend && uv run mypy src/)
git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/quant-assistant/ common/
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/advisor.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_research.py`
- `apps/stock-assistant/backend/tests/test_advisor.py`
- `apps/stock-assistant/backend/tests/test_crypto_research.py`
- `docs/tasks/phaseF/assistant-advisor-backend.md`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

不允许改：所有其它路径。
