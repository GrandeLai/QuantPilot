# Acceptance Report: phaseF3.tlh-engine

**Run at**: 2026-04-29T10:30:00Z
**Implementation PR**: commit e00cb1a (feat: Phase F.3 TLH + TWAP/VWAP + TCA 全栈实现)
**Diff range**: `HEAD~1..HEAD` (e00cb1a)
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-29 (v2 re-run)
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数（`git diff HEAD~1 HEAD --name-only`）：25
- 与 tlh-engine 白名单相关：3（全在白名单内）
  - `apps/stock-assistant/backend/src/quantpilot_stock/tlh/__init__.py` ✅
  - `apps/stock-assistant/backend/src/quantpilot_stock/tlh/engine.py` ✅
  - `apps/stock-assistant/backend/tests/test_tlh_engine.py` ✅
- 其余 22 个文件属于同批次其他任务（execution-engine ✅PASS、execution-api ✅PASS、tlh-api、tlh-panel、docs），均有各自对应的 task spec。
- 本次批次按 task spec "批次开发说明"（F.3.1–F.3.5 统一提交）执行，clean working tree 条件满足（`git diff HEAD` 为空）。

**判定**：tlh-engine 白名单内的 3 个文件全部存在且无额外改动，其余文件有合法归属，不影响本 task 验收。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 模块文件存在（`tlh/__init__.py` + `tlh/engine.py`） | ✅ PASS | `test -f` 两个文件均返回退出码 0 |
| AC-2: 关键符号存在（TaxLot、TLHCandidate、scan_tlh_candidates、estimate_tax_saving） | ✅ PASS | `grep -q` 命中；四个符号均在 engine.py 中定义 |
| AC-3: Wash sale 逻辑（wash_sale / 30 / days） | ✅ PASS | `grep -q` 命中；`_WASH_SALE_WINDOW_DAYS = 30`、`days_since`、`_check_wash_sale` 均存在 |
| AC-4: ETF 替代表（REPLACEMENT_MAP / replacement_tickers / VOO / QQQM） | ✅ PASS | `grep -q` 命中；`_REPLACEMENT_MAP` 定义 30+ 条目，含 VOO、QQQM |
| AC-5: 单元测试通过（>= 10 个，覆盖候选扫描/wash sale/最小亏损/税额/ETF） | ✅ PASS | `pytest tests/test_tlh_engine.py -v` 退出码 0，**24 passed in 0.03s** |
| AC-6: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/tlh/` 退出码 0，"Success: no issues found in 2 source files" |

---

## 测试执行日志摘要

### `bash -l -c 'cd apps/stock-assistant/backend && uv run pytest tests/test_tlh_engine.py -v'`
- 退出码：0
- 收集：24 items
- 结果：**24 passed in 0.03s**
- 覆盖：
  - TestReplacementMap (7 tests): SPY 3 replacements、lowercase ticker、QQQ replacements、individual stock sector ETF、NVDA semiconductor ETF、unknown ticker、map >= 20 entries
  - TestScanTLHCandidates (7 tests): basic candidate detected、small loss filtered、small pct loss filtered、profit lot excluded、missing price skipped、sorted by largest loss first、multiple lots same ticker
  - TestHoldingPeriod (2 tests): short-term、long-term
  - TestWashSaleDetection (4 tests): wash sale risk detected、no wash sale beyond window、no wash sale without recent purchase、wash sale exactly at boundary
  - TestEstimateTaxSaving (4 tests): short-term saving、long-term saving、empty candidates returns zero、mixed short and long term

### `bash -l -c 'cd apps/stock-assistant/backend && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/tlh/'`
- 退出码：0
- 出力：`Success: no issues found in 2 source files`

---

## 代码 Review 备注

- engine.py 有完整模块级 docstring（含功能说明 + 合规免责声明）。
- 所有 dataclass 字段均有类型注解；`scan_tlh_candidates` 和 `estimate_tax_saving` 均有完整参数类型 + 返回类型注解。
- `_REPLACEMENT_MAP` 包含 30 条目，超出 spec 要求（满足 test_replacement_map_has_at_least_20_entries 校验）。
- 无跨 app import（仅用 stdlib + 项目内 tlh 模块）。
- `estimate_tax_saving` 返回值使用 `round(..., 2)` 确保货币精度。
- `_check_wash_sale` 以 `< 30` 作为风险窗口边界（恰好 30 天不触发），与测试预期一致。
- 无"顺带重构"；文件纯粹实现 spec 要求功能。

---

## 后续动作

- PASS：可合入 PR。其余同批次 task（tlh-api、tlh-panel）同步验收后统一合入。
