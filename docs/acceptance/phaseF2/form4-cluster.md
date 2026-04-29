# Acceptance Report: phaseF2.form4-cluster

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: working tree (untracked files, not yet committed)
**Diff range**: working tree vs HEAD (git status --short)
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-29
**Verdict**: NEEDS-REVISION

---

## 文件影响范围检查

- 改动文件总数（工作树）：12（含未跟踪 + 已修改）
- 在白名单内：2
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py` ✓
  - `apps/stock-assistant/backend/tests/test_form4_cluster.py` ✓
- 超出白名单（未跟踪）：
  - `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py`
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py`
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py`
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py`
  - `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`
  - `apps/stock-assistant/backend/tests/test_edgar_client.py`
  - `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py`
  - `apps/stock-assistant/backend/tests/test_sec_api.py`
  - `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`
- 超出白名单（已修改）：
  - `apps/stock-assistant/backend/pyproject.toml`
  - `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
  - `apps/stock-assistant/frontends/workbench/src/api/client.ts`
  - `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
  - `uv.lock`

**判定**：超出白名单。

然而，这些超出文件明显属于 phaseF2 系列中的其他 EDGAR 子任务（EDGAR client、diff-engine、SEC API 路由、前端面板等），而非本任务的 scope creep。`form4_engine.py` 依赖 `edgar/models.py`（导入 `Form4Transaction`）。

原因判断为 **(b) task spec 白名单遗漏必要伴随文件** 或 **工作树混入了多个尚未提交的并行任务**。建议：
1. 将两个任务文件单独 commit（隔离 diff 范围），再重跑验收；或
2. 在 spec 白名单中增加 `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`（因 form4_engine.py 直接依赖它）。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件存在 (`form4_engine.py`) | ✅ PASS | `test -f` 退出码 0 |
| AC-2: 关键符号存在 (`InsiderCluster\|detect_clusters`) | ✅ PASS | `grep -q` 退出码 0；两个符号均在文件中定义 |
| AC-3: 10b5-1 过滤存在 (`10b5_1\|is_10b5_1`) | ✅ PASS | `grep -q` 退出码 0；`not t.is_10b5_1_plan` 在 `detect_clusters` 过滤链中 |
| AC-4: 单元测试通过（≥8 个测试） | ✅ PASS | `pytest tests/test_form4_cluster.py -v` 退出码 0，**23 passed** in 0.02s |
| AC-5: mypy 通过 | ✅ PASS | `mypy src/quantpilot_stock/edgar/form4_engine.py` 退出码 0，"Success: no issues found in 1 source file" |

---

## 测试执行日志摘要

### `uv run pytest tests/test_form4_cluster.py -v`
- 退出码：0
- 收集：23 items
- 全部通过：23 passed in 0.02s
- 覆盖的场景（符合 spec 要求的 ≥8 个测试）：
  - `TestIsKeyInsider` (6 tests)：CEO/CFO/Director/VP 识别、普通职员排除、空字符串排除
  - `TestExtractRoleLabel` (4 tests)：CEO/CFO/Director/President 标签提取
  - `TestComputeSignalStrength` (4 tests)：最小集群低值弱信号、高 insider+金额强信号、零金额、值域 [0,1]
  - `TestDetectClusters` (9 tests)：双 insider 检测、单 insider 不算集群、10b5-1 排除、销售排除、非关键职位排除、窗口边界、信号强度值域、最小金额过滤、空列表

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/form4_engine.py`
- 退出码：0
- 输出：`Success: no issues found in 1 source file`

---

## 代码 Review 备注

**正面：**
- 文件有模块级 docstring（含中文说明 + signal_strength 公式），符合 CLAUDE.md 规范
- 全文件 type hints 完整，mypy strict 无报错
- `from __future__ import annotations` 使用正确
- `@dataclass` + `field(default_factory=list)` 避免 mutable default 陷阱
- signal_strength 公式与 spec 一致（0.4×count + 0.3×value + 0.3×role_bonus）
- 唯一外部导入是同包的 `quantpilot_stock.edgar.models`，无跨 app import 违规
- 窗口去重逻辑合理（`seen_windows` set + `best` dict）

**轻微建议（不阻塞）：**
- `_extract_role_label` 回退到 `title[:20]` 在职位完全不匹配时会截断原始字符串，可考虑返回 `"Other"` 语义更清晰
- `test_outside_window_not_clustered` 的断言使用 `all(c.insider_count < 2 for c in clusters)` — 如果 `clusters` 为空列表，all() 为 True，测试可能掩盖空结果（但这是可接受的边界情况）

---

## 后续动作

**Verdict: NEEDS-REVISION**，原因是文件影响范围超出白名单（工作树混入多个并行任务），而非 AC 失败。

所有 AC-1 至 AC-5 均通过。建议采用以下任一方式解决后重跑验收：

1. **（推荐）将本任务文件单独 commit**，仅包含 `form4_engine.py` 和 `test_form4_cluster.py`，再指定该 commit hash 作为 diff range 重跑验收。
2. 在 task spec 白名单中增加 `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`（因 form4_engine.py 直接依赖 `Form4Transaction`），并说明其他 edgar 文件属于 phaseF2 其他子任务（不在本次验收范围）。

修复后重验将写 `docs/acceptance/phaseF2/form4-cluster-v2.md`。
