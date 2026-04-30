# Acceptance Report: F.22 — 大单不对称积分 Smart Money Flow

**Run at**: 2026-04-30T00:00:00Z
**Implementation PR**: commit 7c14d01
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-30
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

全部 9 个改动文件均在 task spec 白名单内：

1. `apps/stock-assistant/backend/src/quantpilot_stock/smart_money/__init__.py`
2. `apps/stock-assistant/backend/src/quantpilot_stock/smart_money/engine.py`
3. `apps/stock-assistant/backend/src/quantpilot_stock/api/smart_money.py`
4. `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
5. `apps/stock-assistant/backend/tests/test_smart_money.py`
6. `apps/stock-assistant/frontends/workbench/src/api/client.ts`
7. `apps/stock-assistant/frontends/workbench/src/components/SmartMoneyPanel.tsx`
8. `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
9. `docs/tasks/phaseF22/smart-money.md`

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 数据模型 — SmartMoneySignal / DailyFlow / SmartMoneyData | PASS | `engine.py` 定义了 `SmartMoneySignal = Literal[...]` 含全部 6 个值；`DailyFlow` dataclass 含 6 个字段（date, large_buy_usd, large_sell_usd, buy_pressure_pct, total_large_usd, large_bar_count）；`SmartMoneyData` dataclass 含全部 9 个字段（ticker, signal, today_buy_pressure_pct, avg_5d_buy_pressure_pct, large_threshold_usd, daily_flows, interpretation, as_of_date, data_available） |
| AC-2: 大单分类逻辑 — 2× 中位数阈值、close>open→buy、close<open→sell、doji 不计入、小于阈值不计入 | PASS | `_classify_bars()` 实现完整：`usd < threshold_usd` 跳过（小于阈值）；`close > open_` → `large_buy`；`close < open_` → `large_sell`；`close == open` 走到 `# neutral → skip`；阈值在 `compute_smart_money` 中取 `median × 2.0` |
| AC-3: 信号规则 — 所有分支 | PASS | `_compute_signal_from_pressure()` 实现：today>60 且 delta≥10 → `smart_money_buy`；today<40 且 delta≤-10 → `smart_money_sell`；today>55 → `accumulation`；today<45 → `distribution`；其他 → `neutral`；today=None → `no_data` |
| AC-4: 测试要求 ≥16 条（实际 38 条），覆盖所有函数分支，全部 mock yfinance | PASS | `pytest tests/test_smart_money.py -v` 收集并通过 38 tests；TestClassifyBars(6)、TestBuyPressure(5)、TestComputeSignalFromPressure(8)、TestBuildInterpretation(4)、TestComputeSmartMoney(7)、TestGracefulDegradation(4)、TestSmartMoneyAPIEndpoint(4)；所有 yfinance 调用均以 `unittest.mock.patch` mock，无真实网络请求 |
| AC-5: API GET /api/smart-money?ticker=<TICKER>，无 ticker→422，有 ticker→200，通过 include_with_api_alias 注册 | PASS | `main.py` line 141-142：`from quantpilot_stock.api.smart_money import router as smart_money_router` + `include_with_api_alias(smart_money_router)`；测试验证：无 ticker 422，有 ticker 始终 200（含降级场景） |
| AC-6: 前端 — client.ts 类型定义和 fetchSmartMoney；SmartMoneyPanel.tsx 含信号 badge + 买压条 + 日度流向柱图；RiskReviewCenter.tsx 引入并渲染；TypeScript 构建通过 | PASS | `client.ts` 定义 `SmartMoneySignal`、`DailyFlowItem`、`SmartMoneyData`、`fetchSmartMoney()`；`SmartMoneyPanel.tsx` 含 `BuyPressureBar` 组件（条形 + 5 日均值标记）和 `DailyFlowBar` 组件（迷你柱状图），信号 badge 覆盖 6 种信号；`RiskReviewCenter.tsx` line 25 `import SmartMoneyPanel`，line 45 渲染 `<SmartMoneyPanel />`；Vite 构建成功（exit code 0） |

## 测试执行日志摘要

### `uv run pytest tests/test_smart_money.py -v`
- 退出码：0
- 关键输出：
  ```
  collected 38 items
  ... 38 tests PASSED ...
  ============================== 38 passed in 6.93s ==============================
  ```

### `uv run ruff check src/quantpilot_stock/smart_money/ src/quantpilot_stock/api/smart_money.py tests/test_smart_money.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/smart_money/ src/quantpilot_stock/api/smart_money.py`
- 退出码：0（使用项目配置 `--config-file pyproject.toml` / 从 backend 目录执行）
- 关键输出：`Success: no issues found in 3 source files`
- 备注：用绝对路径直接调用 mypy 时（不经过项目目录）会因 pyproject.toml 的 `ignore_missing_imports = true` 未被加载而报 yfinance/pandas 缺失 stubs 的 error；这是调用姿势问题，非代码问题。从项目目录运行完全通过。

### `npm run build --workspace=apps/stock-assistant/frontends/workbench`
- 退出码：0
- 关键输出：`✓ built in 512ms`

## 代码 Review 备注

- 无跨 app import；`smart_money/` 仅依赖 `yfinance`、`pandas` 和标准库，`common/` 无反向 import。
- `engine.py` 有模块级 docstring（详尽的算法说明），所有公开函数有 type hints，符合 CLAUDE.md 规范。
- `_classify_bars` 使用 `iterrows()` 而非向量化，性能上有改进空间（1 分钟 K 线每天约 390 条，5 天约 1950 条，对此场景可接受）。不阻塞验收。
- `compute_smart_money` 裸 `except Exception` + `# noqa: BLE001` 符合"始终返回，绝不抛出"设计。
- 前端 `SmartMoneyPanel.tsx` 使用 inline style，与其他同类 Panel 保持一致风格，无异常依赖引入。

## 后续动作

- PR 可合并。无阻塞项。
- 建议（非强制）：后续可考虑将 `_classify_bars` 改为 pandas 向量化操作以提升性能。
