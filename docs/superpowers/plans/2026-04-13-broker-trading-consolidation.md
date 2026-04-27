# Broker / Trading Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有 broker / trading 半成品收编成 QuantPilot 的正式统一交易主线，并保持加密执行链路独立可用。

**Architecture:** 后端以 `/api/trading/*` + `TradingProvider` 为正式股票/通用交易入口，provider 层固化 `mock / longbridge / auto` 选择与 fallback 语义；前端运行中心与图表下单继续统一消费 trading client + store。加密继续走 `/api/crypto/*` 与 OKX provider，不强行合并模型。

**Tech Stack:** FastAPI, Pydantic v2, pytest, Ruff, React, TypeScript strict mode, Zustand

---

### Task 1: 收编后端 trading / broker 主线

**Files:**
- Modify: `backend/src/quantpilot/main.py`
- Modify: `backend/src/quantpilot/config.py`
- Add/Modify: `backend/src/quantpilot/api/trading.py`
- Add/Modify: `backend/src/quantpilot/broker/__init__.py`
- Add/Modify: `backend/src/quantpilot/broker/provider.py`
- Add/Modify: `backend/src/quantpilot/broker/types.py`
- Add/Modify: `backend/src/quantpilot/broker/catalog.py`
- Add/Modify: `backend/src/quantpilot/broker/mock.py`
- Add/Modify: `backend/src/quantpilot/broker/longbridge.py`
- Test: `backend/tests/test_trading_api.py`

- [ ] Step 1: 运行现有 trading API 测试，确认当前缺口
- [ ] Step 2: 补齐 provider 选择、status、账户、搜索、报价、订单生命周期接口
- [ ] Step 3: 让 `main.py` 正式挂载 trading router，并确认 `config.py` 的 provider 配置字段可用
- [ ] Step 4: 重跑 `backend/tests/test_trading_api.py`
- [ ] Step 5: 扩大到相关回归测试并提交

### Task 2: 收编前端 trading client / store / 运行中心接线

**Files:**
- Add/Modify: `frontend/src/api/trading.ts`
- Add/Modify: `frontend/src/store/tradingStore.ts`
- Modify: `frontend/src/components/PaperTradingPanel.tsx`
- Modify: `frontend/src/components/chart/ChartOrderEntry.tsx`
- Modify: `frontend/src/components/chart/ChartBottomPanels.tsx`
- Test: `backend/tests/test_frontend_contracts.py`

- [ ] Step 1: 写或补 contract 测试，先验证前端依赖的 trading 字段/路径
- [ ] Step 2: 收编 trading client 与 store，统一走 `/api/trading/*`
- [ ] Step 3: 确认运行中心主交易页与图表下单都读同一套 trading 状态
- [ ] Step 4: 运行前端 contract 测试与类型检查
- [ ] Step 5: 提交

### Task 3: 保持 crypto 链路独立且不回退

**Files:**
- Add/Modify: `backend/src/quantpilot/api/crypto.py`
- Add/Modify: `backend/src/quantpilot/broker/okx.py`
- Modify: `frontend/src/api/crypto.ts`
- Modify: `frontend/src/store/cryptoStore.ts`

- [ ] Step 1: 对照统一 trading 收编改动，检查 crypto API / store 是否被间接影响
- [ ] Step 2: 仅做必要兼容修复，不做模型统一大改
- [ ] Step 3: 跑 crypto 相关已有测试与类型检查
- [ ] Step 4: 提交

### Task 4: 文档与路线图同步

**Files:**
- Modify: `docs/DESIGN.md`
- Modify: `README.md`
- Modify: `docs/tab-pages-guide.md`

- [ ] Step 1: 把旧的 “Binance API” 券商接入口径改成 `Longbridge / OKX / Mock provider`
- [ ] Step 2: 将“券商接入 / 实盘交易”状态与当前边界写清
- [ ] Step 3: 运行最小 docs 自检并提交

### Task 5: 总体验证

**Files:**
- Test only

- [ ] Step 1: 运行 `cd backend && uv run pytest tests/test_trading_api.py tests/test_frontend_contracts.py -v`
- [ ] Step 2: 运行 `cd backend && uv run ruff check src/quantpilot/api/trading.py src/quantpilot/broker tests/test_trading_api.py tests/test_frontend_contracts.py`
- [ ] Step 3: 运行 `cd frontend && npm run type-check`
- [ ] Step 4: 如果改到 assistant 或 crypto 前端，再补对应类型检查 / 构建
- [ ] Step 5: 整理 diff 边界，避免卷入本轮范围之外的脏改动
