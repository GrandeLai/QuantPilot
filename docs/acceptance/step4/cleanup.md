# Acceptance Report: step4.cleanup

**Run at**: 2026-04-28T05:30:00Z
**Implementation PR**: commit 0cfeedf7ac946e11d18ce438bac9daecbca1c575
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session, 2026-04-28
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：107
- 在白名单内：107
- 超出白名单：0

所有改动文件均在白名单范围内：
- `apps/quant-assistant-py/` 下 104 个文件（整目录删除，含 .gitkeep + backend 所有源码和测试）
- `scripts/dev-quant-py.sh`（删除）
- `.github/workflows/quant-assistant-py.yml`（删除）
- `pyproject.toml`（修改）
- `uv.lock`（重新生成）
- `CLAUDE.md`（修改）
- `scripts/infra.sh`（修改）
- `common/python/README.md`（修改）
- `common/python/quantpilot_common/__init__.py`（修改）
- `apps/stock-assistant/backend/tests/test_frontend_contracts.py`（修改）
- `apps/stock-assistant/backend/src/quantpilot_stock/api/portfolio.py`（修改）
- `docs/tasks/step4/cleanup.md`（修改）

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `apps/quant-assistant-py/` 目录不存在 | PASS | `test ! -d apps/quant-assistant-py` 退出码 0 |
| AC-2: `scripts/dev-quant-py.sh` 不存在 | PASS | `test ! -f scripts/dev-quant-py.sh` 退出码 0 |
| AC-3: `.github/workflows/quant-assistant-py.yml` 不存在 | PASS | `test ! -f .github/workflows/quant-assistant-py.yml` 退出码 0 |
| AC-4: `pyproject.toml` 不含 `quant-assistant-py` workspace member | PASS | `grep -q "quant-assistant-py" pyproject.toml` 退出码 1（无匹配） |
| AC-5: `apps/stock-assistant/` 中无 `from quantpilot_quant` 直接 import | PASS | `grep -rn "^from quantpilot_quant\|^import quantpilot_quant" apps/stock-assistant/` 无输出；try/except 内的 lazy import 也已被本次提交清除 |
| AC-6: `common/` 中无 `from quantpilot_quant` import | PASS | `grep -rn "from quantpilot_quant\|import quantpilot_quant" common/` 无输出 |
| AC-7: `apps/stock-assistant/backend && uv run pytest tests/ -q` 全过（165 passed） | PASS | 输出：`165 passed in 10.88s`，退出码 0 |
| AC-8: `common/python && uv run --group dev pytest tests/ -q` 全过（59 passed） | PASS | 输出：`59 passed in 2.89s`，退出码 0 |
| AC-9: Rust `cargo test` 全过（无 FAILED） | PASS | 10 个 test result 行，全部 `0 failed`；总计 53 passed（spec 估算 57，实际 53，但无任何 FAILED） |

---

## 测试执行日志摘要

### `test ! -d apps/quant-assistant-py`
- 退出码：0
- 关键输出：（无输出，目录不存在）

### `test ! -f scripts/dev-quant-py.sh`
- 退出码：0
- 关键输出：（无输出，文件不存在）

### `test ! -f .github/workflows/quant-assistant-py.yml`
- 退出码：0
- 关键输出：（无输出，文件不存在）

### `grep -q "quant-assistant-py" pyproject.toml`
- 退出码：1（无匹配 = PASS）

### `grep -rn "^from quantpilot_quant|^import quantpilot_quant" apps/stock-assistant/`
- 退出码：1（无匹配 = PASS）

### `grep -rn "from quantpilot_quant|import quantpilot_quant" common/`
- 退出码：1（无匹配 = PASS）

### `(cd apps/stock-assistant/backend && uv run pytest tests/ -q 2>&1 | tail -3)`
- 退出码：0
- 关键输出：
  ```
  165 passed in 10.88s
  ```

### `(cd common/python && uv run --group dev pytest tests/ -q 2>&1 | tail -3)`
- 退出码：0
- 关键输出：
  ```
  59 passed in 2.89s
  ```

### `(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")`
- 退出码：0
- 关键输出（10 lines, all 0 failed）：
  ```
  test result: ok. 25 passed; 0 failed; 0 ignored; ...
  test result: ok. 2 passed;  0 failed; 0 ignored; ...
  test result: ok. 1 passed;  0 failed; 0 ignored; ...
  test result: ok. 4 passed;  0 failed; 0 ignored; ...
  test result: ok. 4 passed;  0 failed; 0 ignored; ...
  test result: ok. 3 passed;  0 failed; 0 ignored; ...
  test result: ok. 4 passed;  0 failed; 0 ignored; ...
  test result: ok. 2 passed;  0 failed; 0 ignored; ...
  test result: ok. 4 passed;  0 failed; 0 ignored; ...
  test result: ok. 4 passed;  0 failed; 0 ignored; ...
  ```
  Total: 53 passed, 0 failed across all test suites.

---

## 代码 Review 备注

1. **portfolio.py**: The try/except lazy import of `quantpilot_quant.strategy.loader` and `TEMPLATE_STRATEGIES` has been completely removed (not just the comment). The `available_strategies()` docstring now correctly states that template strategies are served by the Rust quant-assistant via HTTP API. This is correct behavior per Step 4 "纯清理" intent.

2. **test_frontend_contracts.py**: Stale Phase A comment about `/api/signals/feed` routing to quant-assistant-py port 8002 has been removed. The test function docstring is now cleaner.

3. **common/python/__init__.py**: Quant-py references removed without affecting common package exports.

4. **Task scope compliance**: No out-of-scope changes detected. The commit description accurately lists all modified files. Rust quant-assistant code is untouched.

5. **AC-9 test count note**: The spec estimated "57 tests" for Rust cargo test. Actual count is 53 (25+2+1+4+4+3+4+2+4+4). This is a minor spec estimate drift — no tests failed. AC-9's actual check condition is "no FAILED" which is fully satisfied.

6. **Isolation verified**: No `from quantpilot_quant` imports remain anywhere in stock-assistant or common. Cross-app coupling is now zero.

---

## 后续动作

- PR 可合，无前置条件。
- 建议在 `docs/acceptance/INDEX.md` 中新增一行记录本次验收结果。
- Optional: 更新 `docs/tasks/step4/cleanup.md` 中 `Status: in-progress` 为 `Status: passed`。
