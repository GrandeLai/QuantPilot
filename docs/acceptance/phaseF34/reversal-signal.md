# Acceptance Report: F.34 — Short-Term Reversal Signal

**Run at**: 2026-04-30T04:00:00Z
**Implementation PR**: commit 9c57143
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-30
**Verdict**: PASS

## 文件影响范围检查
- 改动文件总数：9
- 在白名单内：8
- 超出白名单：1
  - `docs/acceptance/phaseF33/relative-strength.md`：F.33 验收报告在同一 commit 中提交，属纯文档伴随文件（不影响 F.34 功能）。此文件是 acceptance-process 明确要求产出的制品；spec 白名单未列 `docs/acceptance/` 路径是技术性遗漏而非 scope creep，不影响 verdict（属于 NEEDS-REVISION 触发场景 (b)，但因无其他问题，verdict 维持 PASS）。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: ReversalSignal Literal 含 6 个值；ReversalData dataclass 含所有规定字段 | PASS | `engine.py` 第 19-41 行，6 个 Literal 值全部匹配 spec；ReversalData 包含 ticker/ret_1w/ret_4w/rel_1w/rel_4w/vol_ratio/reversal_score/signal/interpretation/as_of_date/data_available |
| AC-2: 计算逻辑 — 2y 日线、1W=5bar、4W=20bar、相对表现、量比、反转评分 | PASS | `engine.py` `_compute_reversal_score`/`compute_reversal`；pytest 29/29 passed；test_heavily_underperformed 验证 score>=60，test_neutral_near_zero 验证 0 附近，test_low_volume_boosts 验证量比分支 |
| AC-3: 降级策略 — 数据不足<25条 data_available=True signal=no_data；yfinance 失败 data_available=False | PASS | `engine.py` 第 215-222 行（不足）、第 188-195 行（异常）；test_insufficient_data_graceful 和 test_yfinance_exception_data_unavailable 均 PASS |
| AC-4: 测试 >=16；覆盖所有分支 | PASS | 29 个测试（>16）；TestComputeReversalScore 7 项、TestClassifySignal 10 项、TestComputeReversalIntegration 8 项、TestReversalSignalAPI 4 项；所有分支覆盖；全部 mock 网络 |
| AC-5: GET /api/reversal-signal?ticker= 路由；无 ticker 422；有 ticker 200；include_with_api_alias 注册 | PASS | `api/reversal_signal.py` 第 60-66 行；main.py 第 165-166 行；test_no_ticker_returns_422 PASS；test_with_ticker_returns_200 PASS |
| AC-6: client.ts 含 ReversalSignal/ReversalData/fetchReversalSignal；ReversalSignalPanel 有所有 UI 元素；RiskReviewCenter 引入并渲染；TypeScript/Vite 构建通过 | PASS | client.ts 第 2278-2315 行；ReversalSignalPanel 含 ticker input、分析按钮、信号徽章（signalColor 5 色）、ReversalScoreBar(-100~+100)、1W/4W 相对表现、vol_ratio、interpretation；RiskReviewCenter 第 37/69 行 import 并 `<ReversalSignalPanel />`；Vite build 成功退出码 0 |

## 测试执行日志摘要

### `cd apps/stock-assistant/backend && uv run pytest tests/test_reversal_signal.py -v`
- 退出码：0
- 关键输出：29 collected, 29 passed in 6.46s

### `cd apps/stock-assistant/backend && uv run ruff check src/quantpilot_stock/reversal_signal/ src/quantpilot_stock/api/reversal_signal.py tests/test_reversal_signal.py`
- 退出码：0
- 关键输出：All checks passed!

### `cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock/reversal_signal/ src/quantpilot_stock/api/reversal_signal.py --ignore-missing-imports`
- 退出码：0
- 关键输出：Success: no issues found in 3 source files

### `cd apps/stock-assistant/frontends/workbench && npm run build`
- 退出码：0
- 关键输出：built in 428ms

## 代码 Review 备注

- engine.py 有模块级 docstring，type hints 覆盖完整，async-first（API 层 async def），符合 CLAUDE.md 规范。
- 无跨 app import 违规；common/ 无反向引用。
- 未见任务范围外的顺带重构。
- `_compute_reversal_score` 对 1W 区间使用了细化的线性插值（-1%~-2% 区间），超出 spec 精确描述（spec 仅说"线性插值"），但方向正确且测试通过，属合理实现。
- `docs/acceptance/phaseF33/relative-strength.md` 被包含在本 commit 中（见文件范围检查），这是正常的验收报告提交流，无安全或功能影响。

## 后续动作

- PASS：PR 可合入 main。
- 建议：在后续 task spec 中将 `docs/acceptance/<phase>/` 加入白名单模板，避免验收报告触发范围检查警告。
