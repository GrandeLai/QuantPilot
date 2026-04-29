# Acceptance Report: phaseF3.tlh-engine

**Run at**: 2026-04-29T09:42:09Z
**Implementation PR**: working tree (uncommitted changes vs HEAD b69856f)
**Diff range**: `HEAD` (git diff HEAD — modified tracked files + untracked new files)
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-29
**Verdict**: NEEDS-REVISION

---

## 文件影响范围检查

- 改动文件总数（tracked, `git diff --name-only HEAD`）：3
- 在白名单内（tlh-engine 白名单）：0
- 超出白名单：3

```
apps/stock-assistant/backend/src/quantpilot_stock/main.py      — 属于 phaseF3.tlh-api 白名单
apps/stock-assistant/frontends/workbench/src/api/client.ts     — 属于 phaseF3.tlh-panel 白名单
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx — 属于 phaseF3.tlh-panel 白名单
```

**说明**：上述 3 个 tracked 修改文件均属于其他 task 的白名单（tlh-api / tlh-panel），不属于 tlh-engine。
tlh-engine 白名单中的 3 个文件（tlh/__init__.py、tlh/engine.py、tests/test_tlh_engine.py）
均为 untracked 新文件，未出现在 `git diff --name-only HEAD` 中（因实现尚未提交）。

这是多 task 实现共存于同一工作树导致的 scope 交叉，属于 NEEDS-REVISION 类型 (a)：
implementation agent 应将各 task 分开 commit，使每个 PR 只包含其白名单内的文件。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 模块文件存在（__init__.py + engine.py） | ✅ PASS | `test -f` 两个文件均存在 |
| AC-2: 关键符号存在（TaxLot, TLHCandidate, scan_tlh_candidates, estimate_tax_saving） | ✅ PASS | `grep -q` 命中，均在 engine.py 中定义 |
| AC-3: Wash sale 逻辑（wash_sale / 30 / days） | ✅ PASS | `grep -q` 命中；`_WASH_SALE_WINDOW_DAYS = 30`、`days_since`、`_check_wash_sale` 均存在 |
| AC-4: ETF 替代表（REPLACEMENT_MAP / replacement_tickers / VOO / QQQM） | ✅ PASS | `grep -q` 命中；`_REPLACEMENT_MAP` 定义 30+ 条目，含 VOO、QQQM |
| AC-5: 单元测试通过（>= 10 个，覆盖候选扫描/wash sale/最小亏损/税额/ETF） | ✅ PASS | `pytest tests/test_tlh_engine.py -v` 退出码 0，**24 passed**（>= 10 满足） |
| AC-6: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/tlh/` 退出码 0，"Success: no issues found in 2 source files" |

---

## 测试执行日志摘要

### `uv run pytest tests/test_tlh_engine.py -v`
- 退出码：0
- 收集：24 items
- 结果：**24 passed in 0.02s**
- 覆盖：TestReplacementMap (7)、TestScanTLHCandidates (7)、TestHoldingPeriod (2)、TestWashSaleDetection (4)、TestEstimateTaxSaving (4)

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/tlh/`
- 退出码：0
- 输出：`Success: no issues found in 2 source files`

---

## 代码 Review 备注

- engine.py 有完整模块级 docstring（含功能说明 + 合规免责声明）。
- 所有 dataclass 字段均有类型注解；`scan_tlh_candidates` 和 `estimate_tax_saving` 均有完整参数类型 + 返回类型注解。
- `_REPLACEMENT_MAP` 包含 30 条目，超出 spec 要求的最小集（满足 AC-5 中 `>= 20` 的子检查）。
- 无跨 app import（仅用 stdlib + 项目内 tlh 模块）。
- 无 `from apps.*` 反向 import。
- `estimate_tax_saving` 返回值使用 `round(..., 2)` 确保货币精度。
- `_check_wash_sale` 将 `< 30` 而非 `<= 30` 作为风险窗口，与 AC-3 测试预期一致（恰好 30 天不触发）。
- 无"顺带重构"；引擎文件纯粹实现 spec 要求功能。

---

## 后续动作

**NEEDS-REVISION 原因**：多 task（tlh-engine、tlh-api、tlh-panel、execution）的实现共存于同一工作树但尚未分开提交，导致 `git diff --name-only HEAD` 输出包含不属于 tlh-engine 白名单的文件。

**建议**：
1. 将 tlh-engine 白名单内的 3 个文件单独 commit（`tlh/__init__.py`、`tlh/engine.py`、`tests/test_tlh_engine.py`）；
2. 同理分开 commit tlh-api、tlh-panel、execution 各自的文件；
3. 分开 commit 后重跑本次验收（`-v2` 报告）。

如用户接受"多 task 合并一次 commit"的方式，可在确认白名单追加后给出 PASS；
所有 AC 测试本次均已通过（24/24 passed，mypy clean）。
