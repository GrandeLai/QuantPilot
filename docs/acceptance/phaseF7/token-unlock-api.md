# Acceptance Report: phaseF7.token-unlock-api

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: commit 4e7dc8a (feat(F.6+F.7): EPS revision momentum + crypto token unlock calendar)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-29
**Verdict**: PASS

## 文件影响范围检查
- 改动文件总数：24 (full PR scope)
- 在白名单内：全部在 apps/stock-assistant/ 和 docs/tasks/ 之下
- 超出白名单：0

## 验收标准核对
| AC | 状态 | 证据 |
|---|---|---|
| AC-1: File exists and registered in main.py | ✅ PASS | `test -f` 退出码 0；`grep -q "token_unlock_router\|from.*token_unlock.*import"` 在 main.py 命中，退出码 0 |
| AC-2: ≥3 endpoints | ✅ PASS | `grep -c "@router\."` 返回 3，满足 ≥3 |
| AC-3: Tests pass (≥8) | ✅ PASS | `pytest tests/test_token_unlock_api.py` — 11 passed, 0 failed, 退出码 0 |
| AC-4: mypy passes | ✅ PASS | `mypy src/quantpilot_stock/api/token_unlock.py` — "Success: no issues found in 1 source file" |

## 测试执行日志摘要

### `uv run pytest tests/test_token_unlock_api.py -v`
- 退出码：0
- 关键输出：11 passed in 5.73s
- 测试类：TestUpcomingEndpoint (5 tests), TestBySymbolEndpoint (3 tests), TestHighRiskEndpoint (3 tests)
- 覆盖场景：200 正常响应、空日历、按 symbol 过滤、422 缺参数、自定义 min_score

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/token_unlock.py`
- 退出码：0
- 关键输出：Success: no issues found in 1 source file

## 代码 Review 备注
- 3 个端点：GET /token-unlock/upcoming、GET /token-unlock/by-symbol、GET /token-unlock/high-risk，接口分层清晰
- 无跨 app import

## 后续动作
- PASS：PR 可合。无阻塞项。
