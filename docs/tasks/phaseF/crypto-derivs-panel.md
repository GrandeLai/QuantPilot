# Task phaseF.crypto-derivs-panel: 加密衍生品面板（API + 前端）

**Phase**: Phase F.1（加密衍生品面板之 4 — Phase F.1 收尾任务）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

F.1.10/11/12 已交付加密衍生品所有数据 + 分析能力（collector + basis + funding analytics + ETF flow analytics）。本任务把它们暴露成 HTTP API 并做前端面板，作为 Phase F.1 收尾。

### 做什么

#### 后端：新增 `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_derivs.py`

3 个端点：

- **POST /crypto-derivs/snapshot**
  - Body: `{"asset": "BTC"}`（默认 BTC）
  - Response: 直接返回 `fetch_aggregated_derivs` 的输出（funding/OI per exchange + errors dict）

- **POST /crypto-derivs/funding-stats**
  - Body: `{"history": [...], "current": float | null, "z_threshold": 2.0}`
  - Response: `{"stats": funding_percentile_stats(history), "signal": funding_extreme_signal(current, history, z_threshold) | None}`
  - history < 30 → 400

- **POST /crypto-derivs/etf-flow-stats**
  - Body: `{"history": [...], "current": float | null, "z_threshold": 2.0}`
  - Response: `{"stats": {mean, std, p5/25/50/75/95, n_samples}, "signal": flow_extreme_signal(current, history, z_threshold) | None}`
  - 注：`stats` 部分手算（avg/std/quantile），不复用 funding_percentile_stats（语义不同）

注册：`include_with_api_alias(crypto_derivs_router)` 在 main.py。

测试：`tests/test_crypto_derivs_api.py`，≥ 10 用例。snapshot 端点用 `monkeypatch.setattr` 替换 `fetch_aggregated_derivs`。

#### 前端：新增 `apps/stock-assistant/frontends/workbench/src/components/CryptoDerivsPanel.tsx`

布局（同 RiskMetricsPanel 风格）：

1. **Asset Selector** — BTC / ETH / SOL 切换（buttons）
2. **Live Snapshot** — 「Refresh」按钮调 `/snapshot` →
   - Funding rates table: Binance / OKX 各一行（rate %, next funding time, raw_symbol）
   - OI table: Binance / OKX 各一行（OI value, OI USD if available）
   - Errors banner（如果 errors dict 非空）
3. **Funding Extreme Analyzer** — paste history textarea + current 数字输入 + z_threshold（默认 2.0）→ 调 `/funding-stats` → 显示 signal badge（contrarian_short=red、contrarian_long=green、neutral=gray）+ z-score、percentile

API client 扩展（`src/api/client.ts` 末尾）：3 个新函数 + 类型。

挂载点：`RiskReviewCenter.tsx` 在 RiskMetricsPanel 之下、PortfolioPanel 之上。

#### 客户端测试 `src/api/client.cryptoDerivs.test.ts`

≥ 4 个 node:test 用例（mock fetch，验证 URL/body/响应解析）。

### 不做什么

- 不做 ETF flow 前端 UI（数据输入复杂，留单独任务）— 但 etf-flow-stats 端点已有，便于将来接
- 不做实时 WebSocket
- 不做 OI 历史走势图
- 不做 SOL/etc 之外的山寨币（前端只 hardcode BTC/ETH/SOL）
- 不引入新 npm/python 依赖

---

## 验收标准

- [ ] **AC-1**: 后端文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_derivs.py`
  - `test -f apps/stock-assistant/backend/tests/test_crypto_derivs_api.py`
- [ ] **AC-2**: 前端文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/CryptoDerivsPanel.tsx`
  - `test -f apps/stock-assistant/frontends/workbench/src/api/client.cryptoDerivs.test.ts`
- [ ] **AC-3**: router 已挂载
  - `grep -q "from quantpilot_stock.api.crypto_derivs import router as crypto_derivs_router" apps/stock-assistant/backend/src/quantpilot_stock/main.py`
  - `grep -q "include_with_api_alias(crypto_derivs_router)" apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- [ ] **AC-4**: 前端 panel 已挂载
  - `grep -q "CryptoDerivsPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- [ ] **AC-5**: 后端单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_api.py -v)`；用例数 ≥ 10
- [ ] **AC-6**: 后端 ruff + mypy
  - `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/api/crypto_derivs.py tests/test_crypto_derivs_api.py)`
  - `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/api/crypto_derivs.py --ignore-missing-imports)`
- [ ] **AC-7**: 后端回归无问题 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_api.py -q)` 退出码 0
- [ ] **AC-8**: 前端 type-check + build — `(cd apps/stock-assistant/frontends/workbench && npm run type-check && npm run build)` 退出码 0
- [ ] **AC-9**: 前端 client 测试 — `(cd apps/stock-assistant/frontends/workbench && node --test --experimental-strip-types src/api/client.cryptoDerivs.test.ts)` 退出码 0；用例数 ≥ 4
- [ ] **AC-10**: 不引入新依赖
  - `git diff main -- apps/stock-assistant/backend/pyproject.toml apps/stock-assistant/frontends/workbench/package.json` 输出为空

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_api.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/api/crypto_derivs.py tests/test_crypto_derivs_api.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/api/crypto_derivs.py --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_api.py -q)
(cd apps/stock-assistant/frontends/workbench && npm run type-check)
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/workbench && node --test --experimental-strip-types src/api/client.cryptoDerivs.test.ts)
git diff main -- apps/stock-assistant/backend/pyproject.toml apps/stock-assistant/frontends/workbench/package.json
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_derivs.py`
- `apps/stock-assistant/backend/tests/test_crypto_derivs_api.py`
- `apps/stock-assistant/frontends/workbench/src/components/CryptoDerivsPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/api/client.cryptoDerivs.test.ts`
- `docs/tasks/phaseF/crypto-derivs-panel.md`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`（注册 router）
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`（追加 3 个 fetch 函数）
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`（挂载 panel）

不允许改：所有其它路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #2；F.1 README
- **上游依赖**：F.1.10 / F.1.11 / F.1.12
- **下游依赖**：无（Phase F.1 收尾任务）；ETF flow 数据 provider 是独立后续任务
