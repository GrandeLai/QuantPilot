# Acceptance Report: phaseF16.unusual-options

**Run at**: 2026-04-30T00:00:00Z
**Implementation PR**: commit `2f69204` (feat(F.16): add Unusual Options Activity (UOA) scanner)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session, 2026-04-30
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

所有改动文件均在 task spec 白名单内：
- `apps/stock-assistant/backend/src/quantpilot_stock/unusual_options/__init__.py` ✓
- `apps/stock-assistant/backend/src/quantpilot_stock/unusual_options/engine.py` ✓
- `apps/stock-assistant/backend/src/quantpilot_stock/api/unusual_options.py` ✓
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py` ✓
- `apps/stock-assistant/backend/tests/test_unusual_options.py` ✓
- `apps/stock-assistant/frontends/workbench/src/api/client.ts` ✓
- `apps/stock-assistant/frontends/workbench/src/components/UnusualOptionsPanel.tsx` ✓
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` ✓
- `docs/tasks/phaseF16/unusual-options.md` ✓

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 引擎 (engine.py) 含 OptionsGrade Literal、UnusualContract/UnusualOptionsData dataclass、阈值常量、grade 逻辑、graceful degradation | ✅ PASS | 代码 review 确认全部字段正确；`_VOLUME_OI_THRESHOLD = 3.0`；grade 逻辑与 spec "Grade 逻辑"块完全一致；mypy 无报错 |
| AC-2: GET /api/unusual-options?ticker=AAPL → 200；缺 ticker → 422；通过 include_with_api_alias 注册 | ✅ PASS | 测试 `test_always_returns_200_even_when_degraded` 和 `test_missing_ticker_returns_422` 通过；main.py 第 129-130 行确认注册 |
| AC-3: 前端 UnusualContractData/UnusualOptionsData/OptionsGrade 类型 + fetchUnusualOptions；UnusualOptionsPanel.tsx P/C bar + top contracts + grade badge + degradation banner；加入 RiskReviewCenter；TS 构建无报错 | ✅ PASS | client.ts lines 1451-1501 含全部类型和 fetch 函数；UnusualOptionsPanel.tsx 含 PutCallBar、ContractRow、grade badge、降级提示；RiskReviewCenter.tsx line 33 确认挂载；`npm run build` 退出码 0 |
| AC-4: ≥16 个测试（_options_grade 边界、volume_oi_ratio 阈值、happy path mocked、降级、API 200+422） | ✅ PASS | 27 个测试全部通过（exit code 0）；覆盖 grade 边界 8 项、parse_chain 5 项、compute 6 项、降级 4 项、API 4 项 |

---

## 测试执行日志摘要

### `uv run pytest tests/test_unusual_options.py -v`
- 退出码：0
- 结果：27 passed in 7.01s
- 关键用例：
  - TestOptionsGrade (8 tests) — 全部 PASSED
  - TestParseChain (5 tests) — 全部 PASSED
  - TestComputeUnusualOptions (6 tests) — 全部 PASSED
  - TestGracefulDegradation (4 tests) — 全部 PASSED
  - TestUnusualOptionsAPIEndpoint (4 tests) — 全部 PASSED

### `mypy unusual_options/ api/unusual_options.py`（via backend/.venv/bin/mypy）
- 退出码：0
- 输出：`Success: no issues found in 3 source files`

### `ruff check unusual_options/ api/unusual_options.py`（via backend/.venv/bin/ruff）
- 退出码：0
- 输出：`All checks passed!`

### `npm run build` (workbench frontend)
- 退出码：0
- 输出：`✓ built in 757ms`，无 TypeScript 错误

---

## 代码 Review 备注

以下是不阻塞 PASS 的观察：

1. **命名分歧（PARTIAL 观察，已视为 PASS）**：spec AC-1 写了 `_volume_oi_ratio_threshold = 3.0`（小写）和 `_put_call_grade(put_call_ratio)` 函数名，但实现用了 `_VOLUME_OI_THRESHOLD`（Python 常量惯例，UPPER_SNAKE_CASE）和 `_options_grade(unusual_calls, unusual_puts)`（参数为计数而非 ratio）。实际 grade 算法与 spec "Grade 逻辑"代码块**完全一致**，且所有测试通过。命名差异未违背语义约束，视为可接受的实现选择。如需严格对齐 spec 字面命名，建议修订 spec。

2. **`is_unusual` 额外条件**：`_parse_chain` 中的 `is_unusual` 判断增加了 `vol > 10` 过滤，以排除成交量极小的合约噪声。spec 仅说"ratio > 3.0 视为 unusual"，未明确禁止额外过滤，这是合理的实现增强。

3. **模块文档**：`engine.py` 有完整模块级 docstring 和类型注解，符合 CLAUDE.md 约束。

4. **跨 app import**：无跨 app import；`common/` 亦未被反向 import。

---

## 后续动作

PASS — PR 可直接合并。无需额外操作。
