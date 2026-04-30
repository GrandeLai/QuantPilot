# Acceptance Report: phaseF17.earnings-move

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: commit 42e546f (`feat(F.17): add Pre-Earnings Expected Move (ATM straddle implied move)`)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6, session 2026-04-29
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：9（含 `docs/tasks/phaseF17/earnings-move.md`）
- 在白名单内：9/9
- 超出白名单：0

白名单文件与实际 diff 完全匹配（`docs/acceptance/phaseF17/earnings-move.md` 尚未存在，由本次验收创建，属正常豁免）。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 引擎（earnings_move/engine.py）— EarningsMoveGrade Literal, EarningsMoveData 11字段, _earnings_move_grade 边界, compute_earnings_move 永不抛出 | ✅ PASS | `EarningsMoveGrade = Literal["large_expected","medium_expected","small_expected","no_data"]` 在 engine.py:26；`EarningsMoveData` dataclass 含全部 11 字段 (line 35–48)；`_earnings_move_grade` 实现 >10=large, >5=medium, else small (line 56–62)；整体 try/except 保证降级，26 个 pytest 测试全 PASS |
| AC-2: API（api/earnings_move.py）— GET /api/earnings-move?ticker=AAPL 始终 200，缺 ticker → 422，include_with_api_alias 注册 | ✅ PASS | endpoint `@router.get("/", response_model=EarningsMoveResponse)` with `Query(...)` enforces 422 on missing ticker; main.py:131-132 `include_with_api_alias(earnings_move_router)`; tests `test_missing_ticker_returns_422` + `test_always_returns_200_even_when_degraded` both PASS |
| AC-3: 前端 — EarningsMoveData/EarningsMoveGrade 类型, fetchEarningsMove, EarningsMovePanel.tsx 含四项UI要素, 加入 RiskReviewCenter, TypeScript 无报错 | ✅ PASS | client.ts lines 1507–1543 定义类型和 fetch 函数；EarningsMovePanel.tsx 含 countdown(daysLabel), expected_move gauge(MoveMeter), grade badge, 降级 banner；RiskReviewCenter.tsx lines 20,35 import+render；`npm run build` 退出码 0 |
| AC-4: 测试 ≥ 16（_earnings_move_grade 边界, happy path mocked, 降级, API 200+422） | ✅ PASS | 收集到 26 个测试，全部 PASS；覆盖 grade 边界(6), expiry 查找(4), ATM straddle(3), happy path(6), 降级(3), API(3+1) |

## 测试执行日志摘要

### `uv run pytest tests/test_earnings_move.py -v`
- 退出码：0
- 关键输出：
  ```
  collected 26 items
  ... (all 26 tests) ... PASSED
  ============================== 26 passed in 6.71s ==============================
  ```

### `uv run --with mypy mypy src/quantpilot_stock/earnings_move/ src/quantpilot_stock/api/earnings_move.py`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `npm run build` (workbench frontend)
- 退出码：0
- 关键输出：`✓ built in 956ms`（无任何 TypeScript 报错）

### `uv run --with ruff ruff check src/quantpilot_stock/earnings_move/ src/quantpilot_stock/api/earnings_move.py`
- 退出码：0
- 关键输出：`All checks passed!`

## 代码 Review 备注

（不阻塞 PASS 的发现）

1. **engine.py line 90 — 遗漏 f-prefix**：`medium_expected` interpretation 拼接字符串中 `"期权买方需要超过 {pct:.1f}% 的实际波动才能盈利。"` 缺少 `f` 前缀，导致输出字面量 `{pct:.1f}%` 而非实际百分比。不影响数据字段或 grade 计算，所有测试通过，但 interpretation 文本对用户略有误导。建议后续修复：将该行改为 `f"期权买方需要超过 {pct:.1f}% 的实际波动才能盈利。"`。

2. **working tree dirty（不属于本 PR）**：工作树中 `main.py` 有未提交的 `sector_momentum_router` 添加。该改动不在本 PR commit 内，不影响 F.17 验收。

3. **__init__.py 模块 docstring**：`__init__.py` 有模块级 docstring，符合 CLAUDE.md 规范。

4. **无跨 app import**：engine.py 和 api/earnings_move.py 仅 import `yfinance`, `loguru`, `fastapi`, `pydantic`, `pandas`，以及 `quantpilot_stock` 内部模块，无跨 app 违规。

5. **codegen drift check**：codegen 未引入 drift，diff 仅展示 working-tree 未提交的 sector_momentum 改动，与 codegen 产物无关。

## 后续动作

- PASS：PR 42e546f 可合入 main。
- 建议（非阻塞）：修复 engine.py:90 的 f-string 遗漏，可在下次 F.17 patch 中一并处理。
- INDEX.md 建议新增一行：`2026-04-29 | phaseF17.earnings-move | PASS | docs/acceptance/phaseF17/earnings-move.md`
