# Futu Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 unified trading broker 主线中新增富途 provider，并保持 longbridge / mock / okx 链路稳定。

**Architecture:** 后端新增 `FutuTradingProvider` 适配现有 `TradingProvider` 协议，通过 `trading_provider=futu` 进入统一选择逻辑；当前机器缺少 SDK 或 OpenD 时显式失败或回退，不伪装成功。前端只扩充 provider 类型和状态展示兼容，不新增专属页面。

**Tech Stack:** FastAPI, Pydantic v2, pytest, Ruff, TypeScript strict mode

---

### Task 1: 先补 provider 选择与状态测试

**Files:**
- Modify: `backend/tests/test_trading_api.py`
- Add/Modify: `backend/tests/test_trading_provider_selection.py`

- [ ] Step 1: 先写 `futu` provider 选择与 fallback 的 failing tests
- [ ] Step 2: 运行窄测试确认当前失败
- [ ] Step 3: 再写最小实现去通过这些测试
- [ ] Step 4: 重跑后端测试确认通过
- [ ] Step 5: 提交

### Task 2: 实现 FutuTradingProvider 协议适配

**Files:**
- Create: `backend/src/quantpilot/broker/futu.py`
- Modify: `backend/src/quantpilot/broker/provider.py`
- Modify: `backend/src/quantpilot/broker/__init__.py`
- Modify: `backend/src/quantpilot/broker/types.py`
- Modify: `backend/src/quantpilot/config.py`

- [ ] Step 1: 用 graceful failure 方式实现 `FutuTradingProvider`
- [ ] Step 2: 让 provider 工厂支持 `futu`
- [ ] Step 3: 加上必要配置项
- [ ] Step 4: 跑相关测试与 ruff
- [ ] Step 5: 提交

### Task 3: 让 trading API 与前端状态兼容 futu

**Files:**
- Modify: `backend/src/quantpilot/api/trading.py`
- Modify: `frontend/src/api/trading.ts`
- Modify: `frontend/src/api/trading.test.ts`
- Modify: `frontend/src/components/PaperTradingPanel.tsx`
- Modify: `frontend/src/components/chart/ChartOrderEntry.tsx`

- [ ] Step 1: 扩 provider 类型与状态展示测试
- [ ] Step 2: 让前端识别 `provider=futu`
- [ ] Step 3: 保持现有 longbridge / mock 分支不回退
- [ ] Step 4: 跑前端测试与类型检查
- [ ] Step 5: 提交

### Task 4: 文档同步

**Files:**
- Modify: `docs/DESIGN.md`
- Modify: `README.md`

- [ ] Step 1: 将券商接入口径补成 `Futu / Longbridge / OKX / Mock`
- [ ] Step 2: 写清本轮只完成 provider 占位，不等于完整 OMS 已完成
- [ ] Step 3: 提交

### Task 5: 总体验证

**Files:**
- Test only

- [ ] Step 1: 运行 `cd backend && uv run pytest tests/test_trading_api.py tests/test_trading_provider_selection.py -v`
- [ ] Step 2: 运行 `cd backend && uv run ruff check src/quantpilot/broker src/quantpilot/api/trading.py tests/test_trading_api.py tests/test_trading_provider_selection.py`
- [ ] Step 3: 运行 `cd frontend && node --test --experimental-strip-types src/api/trading.test.ts && npm run type-check`
- [ ] Step 4: 检查 diff 边界，只包含 futu/provider/trading/docs 相关文件
