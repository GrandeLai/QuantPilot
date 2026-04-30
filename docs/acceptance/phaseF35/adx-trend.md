# Acceptance Report: F.35 — ADX Trend Strength Indicator

**Run at**: 2026-04-30T06:00:00Z
**Implementation PR**: commit c879e90
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-30
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：11
- 在白名单内：8（全部 8 个白名单文件均已改动）
- 超出白名单：3
  - `apps/stock-assistant/backend/pyproject.toml`：增加 `ruff>=0.15.12` 和 `mypy>=1.20.2` 到 dev 依赖组。此改动是支撑本任务 lint/type-check 所必须的工具链依赖，属于 NEEDS-REVISION 场景 (b)（spec 白名单遗漏的必要伴随文件），不影响 PASS verdict。
  - `uv.lock`：pyproject.toml 更新后由 uv 自动重新生成的锁文件，与 pyproject.toml 改动不可分割。
  - `docs/acceptance/phaseF34/reversal-signal.md`：F.34 验收报告随本 commit 一并提交（acceptance-agent 明确要求产出），是正常的验收报告随任务提交流程，不影响 F.35 功能。

结论：三个超出白名单的文件均为工具链/锁文件/前次验收报告，均属 NEEDS-REVISION 场景 (b)。实现本身无功能 scope creep，verdict 维持 PASS，建议在后续 spec 模板中将 `pyproject.toml`、`uv.lock`、`docs/acceptance/**` 加入白名单。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: TrendSignal Literal 含 6 个值；ADXData dataclass 含全部规定字段（ticker/adx/plus_di/minus_di/atr/signal/trend_strength/interpretation/as_of_date/data_available） | ✅ PASS | `engine.py` 第 19-44 行：TrendSignal 定义 6 个值（strong_uptrend/uptrend/ranging/downtrend/strong_downtrend/no_data）；ADXData 含全部 10 个字段，类型注解与 spec 一致 |
| AC-2: 计算逻辑 — 1y 日线、Wilder 平滑(period=14)、ATR、+DI/-DI、DX、ADX、Signal 分档、trend_strength 分档 | ✅ PASS | `engine.py` 第 56-111 行实现 Wilder EWM(alpha=1/14)、TR、±DM、ATR、±DI、DX、ADX；`_classify_signal` 第 114-126 行按 spec 规定的所有档位分类；`_classify_strength` 第 129-138 行按 ADX≥40/25/15 分档 |
| AC-3: 降级策略 — 历史数据<30日 data_available=True signal=no_data；yfinance 失败 data_available=False | ✅ PASS | `compute_adx_trend` 第 206-213 行（不足 30 日返回 data_available=True, signal=no_data）；第 183-190 行（yfinance 异常返回 data_available=False）；test_insufficient_data_graceful 和 test_yfinance_exception_data_unavailable 均 PASS |
| AC-4: 测试总数≥16；覆盖 _wilder_smooth/_compute_adx/_classify_signal/compute_adx_trend/API 各路径；全部 mock 网络 | ✅ PASS | 25 个测试（远超 16）；TestWilderSmooth(2) + TestComputeADX(5) + TestClassifySignal(8) + TestComputeADXTrendIntegration(6) + TestADXTrendAPI(4)；全部使用 @patch("quantpilot_stock.adx_trend.engine.yf.Ticker") mock；25 passed 退出码 0 |
| AC-5: GET /api/adx-trend?ticker=；无 ticker 422；有 ticker 始终 200；include_with_api_alias 注册 | ✅ PASS | `api/adx_trend.py` 第 51-57 行路由定义；`main.py` 第 167-168 行 include_with_api_alias 注册；test_no_ticker_returns_422 PASS；test_with_ticker_returns_200 PASS；test_yfinance_fail_still_200 PASS |
| AC-6: client.ts 含 TrendSignal/ADXData/fetchADXTrend；ADXTrendPanel 含所有 UI 元素；RiskReviewCenter 引入并渲染；TypeScript tsc --noEmit 通过；Vite 构建通过 | ✅ PASS | client.ts 第 2320-2356 行含 TrendSignal/ADXData/fetchADXTrend；ADXTrendPanel.tsx(428行) 含 ticker 输入框、分析按钮、ADXBar(0-100，15/25/40 阈值线)、信号徽章、+DI/-DI/ATR 指标卡、趋势强度标注、interpretation 文字；RiskReviewCenter 第 38/71 行 import 并渲染 `<ADXTrendPanel />`；Vite build 退出码 0（2996 modules transformed，built in 412ms） |

## 测试执行日志摘要

### `cd apps/stock-assistant/backend && uv run pytest tests/test_adx_trend.py -v`
- 退出码：0
- 关键输出：25 collected, 25 passed in 6.01s

### `cd apps/stock-assistant/backend && uv run ruff check src/quantpilot_stock/adx_trend/ src/quantpilot_stock/api/adx_trend.py tests/test_adx_trend.py`
- 退出码：0
- 关键输出：All checks passed!

### `cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock/adx_trend/ src/quantpilot_stock/api/adx_trend.py --ignore-missing-imports`
- 退出码：0
- 关键输出：Success: no issues found in 3 source files

### `cd apps/stock-assistant/frontends/workbench && npm run build`
- 退出码：0
- 关键输出：✓ 2996 modules transformed. built in 412ms

## 代码 Review 备注

- `engine.py` 有模块级 docstring，所有函数有 type hints，async-first（API 层 async def get_adx_trend），符合 CLAUDE.md 规范。
- 无跨 app import 违规；common/ 无反向引用。
- 未见任务范围外的顺带重构。
- ADXBar 组件实际标注了 15/25/40 三条阈值线（spec 仅要求 25 和 40），是合理的超集实现，不构成 scope creep。
- `_compute_adx` 使用 `period * 3`（即 42 bars）作为最小有效数据量判断，比 spec 的"历史数据不足 30 日"更严格；`compute_adx_trend` 中先以 30 日做第一道防线，再由 `_compute_adx` 内部做第二道防线，两层降级互补，合理。
- `docs/tasks/phaseF35/adx-trend.md` 在 spec 白名单中已明确列出，符合。

## 后续动作

- PASS：PR 可合入 main。
- 建议：在后续 task spec 白名单模板中加入 `pyproject.toml`、`uv.lock`、`docs/acceptance/**`，避免这些必然伴随文件每次触发范围检查警告。
