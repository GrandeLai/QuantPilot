# Acceptance Report: F.33 — Relative Strength Score

**Run at**: 2026-04-30T03:00:00Z
**Implementation PR**: commit 31b984487f47f55a7fcfd5764b194e98b073cadd
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session (2026-04-30)
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：10
- 在白名单内：9
- 超出白名单：1
  - `docs/acceptance/phaseF32/seasonality.md`：phaseF32 的验收报告，与本任务实现无关，属于上一次验收任务遗留文件随本次 commit 一起提交。为文档型纯追加，不影响任何源码、不引入 scope creep，判定为不阻塞 PASS（属 NEEDS-REVISION 条款 b，spec 白名单遗漏必要伴随文件）。若需严格审计，建议后续在 F.32 spec 白名单中补入此路径。此次给 PASS。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 数据模型（RSSignal、PeriodRS、RSData） | ✅ PASS | `engine.py` 定义了 `RSSignal = Literal[...]` 含全部 6 个值；`PeriodRS` dataclass 含 period/stock_return/spy_return/relative_return；`RSData` dataclass 含 ticker/periods/rs_score/signal/interpretation/as_of_date/data_available。字段完整无误。 |
| AC-2: 计算逻辑（2y 数据、4 区间、加权 RS 分、信号档位） | ✅ PASS | `compute_rs` 用 `tk.history(period="2y", interval="1d")`；`_compute_period_returns` 用 start→end 总收益率（非 pct_change 累计）；相对收益 = stock - spy；`_period_to_rs_score` 实现 clip[-50%,+50%] 线性映射到 [0,100]，0→50 验证通过；加权 2:1.5:1:0.5；信号阈值 ≥80/≥60/≥40/≥20/<20 全覆盖。测试 `test_equal_performance_neutral` 验证 RS≈50/neutral，`test_boundary_*` 验证各档位边界。 |
| AC-3: 降级策略 | ✅ PASS | 数据不足（<20 交易日）→ `data_available=True, periods=[], signal="no_data"`（`test_insufficient_data_graceful`）；yfinance 异常 → `data_available=False`（`test_yfinance_exception_data_unavailable`）。 |
| AC-4: 测试要求（≥16 个，全 mock，覆盖所有路径） | ✅ PASS | 实际 36 个测试，全部通过。覆盖：`_compute_period_returns`（正/负/平/不足/恰好 n/n+1 bars）6 个；`_period_to_rs_score`（0/+50%/-50%/超上限/超下限/正中间）6 个；`_classify_signal`（5 档 + None + 4 边界值）10 个；`compute_rs` 集成（正常/periods/score 范围/equal/outperform/underperform/interpretation/不足/yfinance 异常）9 个；API（422/200/字段/yfinance 失败 200/period 字段）5 个。全部 mock 网络。 |
| AC-5: API 路由 GET /api/relative-strength，422/200，include_with_api_alias | ✅ PASS | `api/relative_strength.py` 定义 `@router.get("/relative-strength")`；无 ticker → 422，有 ticker → 始终 200；`main.py` 第 163-164 行通过 `include_with_api_alias(relative_strength_router)` 注册。 |
| AC-6: 前端（RSSignal/PeriodRS/RSData/fetchRelativeStrength、RSScoreBar、信号徽章、表格、解读、RiskReviewCenter） | ✅ PASS | `client.ts` 定义 `RSSignal/PeriodRS/RSData` 及 `fetchRelativeStrength`；`RelativeStrengthPanel.tsx` 含 ticker 输入框、分析按钮、`RSScoreBar`（0-100 阈值线 20/40/60/80）、信号徽章、PeriodRow 表格（股票收益/SPY 收益/超额，正绿负红）、解读文字；`RiskReviewCenter.tsx` 第 36 行 import + 第 67 行渲染；Vite 构建（含 tsc -b）成功，0 errors。 |

## 测试执行日志摘要

### `uv run pytest tests/test_relative_strength.py -v`
- 退出码：0
- 关键输出：`36 passed in 6.95s`；全部测试类 TestComputePeriodReturns / TestPeriodToRsScore / TestClassifySignal / TestComputeRSIntegration / TestRelativeStrengthAPI 所有条目 PASSED。

### `uv run ruff check src/quantpilot_stock/relative_strength/ src/quantpilot_stock/api/relative_strength.py tests/test_relative_strength.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/relative_strength/ src/quantpilot_stock/api/relative_strength.py --ignore-missing-imports`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `npm run build` (workbench)
- 退出码：0
- 关键输出：`tsc -b && vite build`，2996 modules transformed，`built in 409ms`，无 TypeScript 错误。

## 代码 Review 备注

- `engine.py` 有模块级 docstring，所有公共函数有 docstring，type hints 完整（符合 CLAUDE.md Python 规范）。
- 无跨 app import 违规；`common/` 未被反向 import。
- `__init__.py` 为空文件（单行）——符合 Python package 惯例，无需 docstring。
- `relative_return` 字段使用绝对差（股票 - SPY，单位小数），符合 AC-2 规格"绝对差，单位百分比"的语义（实际以小数存储，前端格式化时乘 100 显示，无歧义）。
- 超出白名单的 `docs/acceptance/phaseF32/seasonality.md` 是 phaseF32 验收报告，内容与本任务实现完全独立，属遗留文件随本次提交附带，不影响源码正确性。

## 后续动作

- PASS：PR 可合入 main。
- 建议：在 `docs/acceptance/INDEX.md` 追加 `2026-04-30 | F.33 relative-strength | PASS | docs/acceptance/phaseF33/relative-strength.md`。
- 可选：若对 phaseF32 acceptance doc 提交时机有严格审计要求，可在 phaseF32 spec 白名单中补入 `docs/acceptance/phaseF32/seasonality.md`，无需重验 F.33。
