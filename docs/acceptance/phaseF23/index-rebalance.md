# Acceptance Report — F.23 指数调仓机会面板 (Index Rebalance Preview)

| 字段 | 值 |
|------|-----|
| Task ID | phaseF23.index-rebalance |
| Task Spec | docs/tasks/phaseF23/index-rebalance.md |
| PR Commit | d81b14b (feat(F.23): 指数调仓机会面板) |
| Acceptance Date | 2026-04-30 |
| Verdict | PASS |
| Report Version | v1 |

---

## 1. 文件影响范围检查

`git diff --name-only HEAD~1 HEAD` 输出的 9 个文件与 task spec 白名单完全一致，无多余文件：

```
apps/stock-assistant/backend/src/quantpilot_stock/api/index_rebalance.py
apps/stock-assistant/backend/src/quantpilot_stock/index_rebalance/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/index_rebalance/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_index_rebalance.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/IndexRebalancePanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF23/index-rebalance.md
```

结论：文件范围 ✅ 完全符合白名单。

---

## 2. 代码 Review

- 所有新增 Python 文件均有模块级 docstring 和完整 type hints（`__init__.py`、`engine.py`、`api/index_rebalance.py`）。
- 无跨 app 源码 import（无 `quant_assistant` 或 `apps.*` 引用）。
- `common/` 未反向 import `apps/*`。
- 任务范围内无顺带重构。
- `pandas`、`yfinance` 均为 `pyproject.toml` 已声明依赖（`pandas>=2.0.0`），无新增 DESIGN.md Section 4 之外的依赖。
- mypy 配置 `ignore_missing_imports = true` 已在 `apps/stock-assistant/backend/pyproject.toml` 中全局声明，从后端目录运行 mypy 时 3 个源文件全部通过（`Success: no issues found`）。

---

## 3. 测试集合执行结果

### 3.1 pytest

命令：`uv run pytest tests/test_index_rebalance.py -v`（从 backend 目录）

```
35 passed in 5.89s
```

退出码：0（期望：0）✅

覆盖范围：
- `TestAssessSP500Risk`（7 tests）：所有边界（member/non_member + high/moderate/stable/unknown）
- `TestAssessNQ100Risk`（6 tests）：所有边界
- `TestAssessRussellRisk`（4 tests）：in-range、above-max、below-min、None
- `TestComputeIndexRebalance`（9 tests）：S&P 500/NASDAQ 100 成员检测、市值计算、ticker 大写化、日期、解读文本非空、三指数返回
- `TestGracefulDegradation`（5 tests）：exception、RuntimeError、ticker 保留、日期保留、空 info
- `TestIndexRebalanceAPIEndpoint`（4 tests）：422 无 ticker、200 降级、200 完整字段、status+risk 字段校验

### 3.2 ruff check

命令：`uv run ruff check src/quantpilot_stock/index_rebalance/ src/quantpilot_stock/api/index_rebalance.py tests/test_index_rebalance.py`

输出：`All checks passed!`，退出码：0 ✅

### 3.3 mypy

命令：`uv run mypy src/quantpilot_stock/index_rebalance/ src/quantpilot_stock/api/index_rebalance.py`（从 backend 目录，使用 backend/pyproject.toml 配置）

输出：`Success: no issues found in 3 source files`，退出码：0 ✅

### 3.4 TypeScript tsc --noEmit

命令：`npx tsc --noEmit`（从 workbench 目录）

输出：无输出（无错误），退出码：0 ✅

### 3.5 Vite build

命令：`npm run build`（从 workbench 目录）

输出：`✓ built in 415ms`，退出码：0 ✅

---

## 4. AC 逐条核对

### AC-1 数据模型 ✅ PASS

- `IndexStatus = Literal["member","non_member","unknown"]` — engine.py:34 ✓
- `RebalanceRisk = Literal["high_addition_risk","moderate_addition_risk","stable","moderate_deletion_risk","high_deletion_risk","unknown"]` — engine.py:35-36 ✓
- `IndexMembership` dataclass：index_name, status, market_cap_rank, market_cap_pct, rebalance_risk — engine.py:39-45 ✓
- `IndexRebalanceData` dataclass：ticker, market_cap, market_cap_b, float_shares, price, eps_ttm, indices, interpretation, as_of_date, data_available — engine.py:48-61 ✓

### AC-2 风险评估逻辑 ✅ PASS

- S&P 500：member && cap < $10B (`_SP500_DEL_CAP_B=10.0`) → high_deletion ✓；non_member && cap > 1.5×$14.5B = $21.75B (`_SP500_MIN_CAP_B*1.5`) → high_addition ✓
- NASDAQ 100：member && cap < 0.8×$5B = $4B (`_NQ100_MIN_CAP_B*0.8`) → high_deletion ✓；non_member && cap > 2×$5B = $10B → high_addition ✓
- Russell 2000：按市值范围 [$300M, $3.5B] 估算，中间 stable，超上限 moderate_deletion，低于下限 high_deletion ✓

### AC-3 指数成员检测 ✅ PASS

- S&P 500：`_fetch_sp500_tickers()` 从 Wikipedia `List_of_S%26P_500_companies` 读取首表 Symbol 列 ✓
- NASDAQ 100：`_fetch_nq100_tickers()` 从 Wikipedia `Nasdaq-100` 读取含 ticker/symbol 列的表格 ✓
- Russell 2000：基于市值范围规则估算（无免费成分股 API）✓

### AC-4 测试要求 ✅ PASS

- 测试总数：35（≥ 16 且 spec 预期的 35）✓
- 全部覆盖项验证：sp500/nq100/russell 边界、mocked Wikipedia+yfinance、yfinance 异常 → data_available=False、空 info → data_available=False、API 无 ticker 422 + 有 ticker 200 ✓
- 所有测试均 mock 网络调用（patch yf.Ticker + _fetch_sp500_tickers + _fetch_nq100_tickers）✓

### AC-5 API ✅ PASS

- 路由：`GET /api/index-rebalance?ticker=<TICKER>`（router prefix="/index-rebalance"，FastAPI Query 参数）✓
- 无 ticker → HTTP 422（测试验证）✓；有 ticker → 始终 200（测试验证）✓
- `include_with_api_alias(index_rebalance_router)` 在 main.py:143-144 注册 ✓

### AC-6 前端 ✅ PASS

- `client.ts`：`IndexStatus`、`RebalanceRisk`、`IndexMembershipItem`、`IndexRebalanceData`、`fetchIndexRebalance` 均已导出（client.ts:1767-1812）✓
- `IndexRebalancePanel.tsx`：市值信息卡（市值/价格/EPS TTM/调仓机会数）+ 三指数成分行（状态标签 + 风险标签）+ 调仓机会计数（`opportunities`）✓
- `RiskReviewCenter.tsx` line 26：`import IndexRebalancePanel from "../IndexRebalancePanel"`；line 47：`<IndexRebalancePanel />` ✓
- TypeScript tsc --noEmit：通过 ✓；Vite 构建：通过（built in 415ms）✓

---

## 5. 总结

| AC | 状态 |
|----|------|
| AC-1 数据模型 | ✅ PASS |
| AC-2 风险评估逻辑 | ✅ PASS |
| AC-3 指数成员检测 | ✅ PASS |
| AC-4 测试要求（35/35 通过）| ✅ PASS |
| AC-5 API 注册 | ✅ PASS |
| AC-6 前端组件 | ✅ PASS |
| 文件范围 | ✅ PASS |
| ruff lint | ✅ PASS |
| mypy | ✅ PASS |

**总 Verdict：PASS**

无发现阻塞性问题，无范围外改动，无顺带重构。
