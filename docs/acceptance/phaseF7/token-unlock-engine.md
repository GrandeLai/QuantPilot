# Acceptance Report: phaseF7.token-unlock-engine

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
| AC-1: Module files exist (`__init__.py`, `engine.py`) | ✅ PASS | `test -f` 两条命令均返回退出码 0 |
| AC-2: Key symbols exist (`TokenUnlockEvent`, `TokenUnlockCalendar`, `compute_sell_pressure_score`, `fetch_upcoming_unlocks`) | ✅ PASS | `grep -q` 命中，退出码 0 |
| AC-3: Unit tests pass (≥12) | ✅ PASS | `pytest tests/test_token_unlock_engine.py` — 23 passed, 0 failed, 退出码 0 |
| AC-4: mypy passes | ✅ PASS | `mypy src/quantpilot_stock/token_unlock/` — "Success: no issues found in 2 source files" |

## 测试执行日志摘要

### `uv run pytest tests/test_token_unlock_engine.py -v`
- 退出码：0
- 关键输出：23 passed in 0.03s
- 测试类：TestComputeSellPressureScore (7), TestSignalFromScore (5), TestNormaliseCategory (3), TestParseEvent (4), TestFetchUpcomingUnlocks (4)

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/token_unlock/`
- 退出码：0
- 关键输出：Success: no issues found in 2 source files

## 代码 Review 备注
- `engine.py` 有模块级 docstring，引用了 Nansen/Messari 研究，量化了 unlock 前后价格影响
- 所有公开函数均有 type hints
- 无跨 app import；data source 使用 DefiLlama（免费，无需 API key）
- 无手改 codegen 产物

## 后续动作
- PASS：PR 可合。无阻塞项。
