# Acceptance Report: phaseF2.form4-cluster

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: commit d2eca0d — feat(edgar): SEC 三合一事件流 — 8-K diff + Form 4 cluster + panel (phaseF2 F.2.1–F.2.5)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: v2 re-run (after batch commit)
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数（本批次 commit）：28 across all phaseF2 tasks
- 在白名单内（form4-cluster 专属）：
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py` ✅
  - `apps/stock-assistant/backend/tests/test_form4_cluster.py` ✅
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py` ✅ (依赖，spec 声明为批次共同提交)
- 超出白名单：批次 commit 含其他 phaseF2 sibling 任务文件（edgar-fetcher、edgar-diff-engine、sec-api、sec-events-panel 等）

**范围裁定**：白名单超出属于同一 phaseF2 批次内的其他 task 文件，各自有独立 task spec 和验收报告。不属于 form4-cluster 的 scope creep，不触发 FAIL。form4-cluster 的核心实现文件与 spec 完全吻合。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件 `form4_engine.py` 存在 | ✅ PASS | `test -f` 退出码 0 |
| AC-2: 符号 `InsiderCluster\|detect_clusters` 存在 | ✅ PASS | `grep -q` 退出码 0；两者均在文件第 79 行（dataclass）和第 123 行（函数）定义 |
| AC-3: `10b5_1\|is_10b5_1` 过滤存在 | ✅ PASS | `grep -q` 退出码 0；`is_10b5_1_plan` 出现于第 158 行过滤条件 |
| AC-4: `pytest tests/test_form4_cluster.py -v` 退出码 0，≥8 测试 | ✅ PASS | 23 passed in 0.03s；覆盖：集群检测、10b5-1 过滤、单 insider 不算集群、90日窗口边界、职位过滤、非关键职位过滤、销售排除、signal_strength 值域、小额过滤、空列表 |
| AC-5: `mypy form4_engine.py` 退出码 0 | ✅ PASS | "Success: no issues found in 1 source file" |

---

## 测试执行日志摘要

### `uv run pytest tests/test_form4_cluster.py -v`
- 退出码：0
- collected 23 items
- 23 passed in 0.03s
- 测试类：TestIsKeyInsider (6)、TestExtractRoleLabel (4)、TestComputeSignalStrength (4)、TestDetectClusters (9)

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/form4_engine.py`
- 退出码：0
- 输出：`Success: no issues found in 1 source file`

---

## 代码 Review 备注

1. **模块级 docstring**：存在且详尽，含 signal_strength 公式说明。满足 CLAUDE.md 约束。
2. **Type hints**：全量覆盖，返回类型、参数类型均完整。
3. **跨 app import**：无。仅 import `quantpilot_stock.edgar.models`（同 app 内）。
4. **signal_strength 公式**：实现与 spec 完全一致（count_score、value_score、role_bonus 权重 0.4/0.3/0.3）。
5. **CEO/CFO senior role 检测**：通过独立 `_SENIOR_ROLE_RE` 正则实现，与主过滤职位正则分离，设计清晰。
6. **去重逻辑**：按 `window_end` 去重，保留 insider_count 最多的集群，合理。
7. **非必要观察（不阻塞）**：`_extract_role_label` 和 `_is_key_insider` 作为私有函数被测试文件直接导入，是合理的 white-box 测试做法。

---

## 后续动作

PASS — PR 可合。无需额外修复。

