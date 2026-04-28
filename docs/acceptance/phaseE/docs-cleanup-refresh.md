# Acceptance Report: phaseE.docs-cleanup-refresh

**Run at**: 2026-04-29T00:45:00Z
**Implementation PR**: commits 854ebfb (new docs) + 93e8a92 (file moves bundled with phaseF risk-engine commit)
**Diff range**: `d77a230..854ebfb` (HEAD)
**Acceptance-agent invocation**: claude-sonnet-4-6, session 2026-04-29
**Verdict**: PASS

---

## 文件影响范围检查

Combined diff across both commits (`93e8a92^..854ebfb`):

| 文件 | 在白名单内 | 备注 |
|---|---|---|
| `docs/README.md` | YES | 新增，854ebfb |
| `docs/architecture/features.md` | YES | 新增，854ebfb |
| `docs/architecture/stock-assistant-api.md` | YES | 新增，854ebfb |
| `docs/architecture/tech-stack.md` | YES | 新增，854ebfb |
| `docs/archive/README.md` | YES | 新增，854ebfb |
| `docs/archive/legacy/Claude_Code_Usage_Guide.md` | YES | git mv from docs/ root，93e8a92 |
| `docs/archive/legacy/factor_guide.md` | YES | git mv from docs/ root，93e8a92 |
| `docs/archive/legacy/llm-agent-layer-design.md` | YES | git mv from docs/ root，93e8a92 |
| `docs/archive/legacy/tab-pages-guide.md` | YES | git mv from docs/ root，93e8a92 |
| `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py` | OUT-OF-SCOPE | 属于 phaseF.risk-var-cvar，同在 93e8a92 中 |
| `apps/stock-assistant/backend/src/quantpilot_stock/risk/var_cvar.py` | OUT-OF-SCOPE | 属于 phaseF.risk-var-cvar，同在 93e8a92 中 |
| `apps/stock-assistant/backend/tests/test_risk_var_cvar.py` | OUT-OF-SCOPE | 属于 phaseF.risk-var-cvar，同在 93e8a92 中 |
| `docs/tasks/phaseF/risk-var-cvar.md` | OUT-OF-SCOPE | 属于 phaseF.risk-var-cvar task spec，同在 93e8a92 中 |

- 改动文件总数：13（跨两个 commit）
- 在白名单内：9（含 4 个 git rename 归档文件 + 5 个新文档）
- 超出白名单：4

**范围超出说明（workflow 异常，不构成此任务违规）**：

4 个 out-of-scope 文件均来自 commit `93e8a92`，该 commit 的 subject 是 `feat(risk): add Historical VaR / CVaR / Parametric VaR engine (phaseF.1.3)`。这 4 个文件是 phaseF.risk-var-cvar 任务的产物，与本任务无关。本任务从 93e8a92 中实际使用的内容仅是其中的 4 个 `docs/archive/legacy/` 文件（git mv 操作），完全在白名单内。

task spec 的 commit message 注释 (`854ebfb`) 和用户 prompt 均已声明此 bundling 是"inadvertent workflow oddity"而非本任务的 scope creep。out-of-scope 文件已由 phaseF.risk-var-cvar 独立走验收（`docs/acceptance/phaseF/risk-var-cvar.md` 或对应报告）。

**结论**：不将此视为本任务的范围违规，维持 PASS 判断。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 4 个 stale 文档已从 `docs/` 顶层移除 | ✅ PASS | `test ! -f docs/Claude_Code_Usage_Guide.md && ...` 退出码 0；`ls docs/` 仅剩 DESIGN.md、MIGRATION.md、README.md、acceptance/、architecture/、archive/、conventions/、protocols/、quant_tutorial/、superpowers/、tasks/ |
| AC-2: 4 个 stale 文档已搬到 `docs/archive/legacy/` | ✅ PASS | `test -f docs/archive/legacy/Claude_Code_Usage_Guide.md && ...` 退出码 0；git 以 R100 rename 跟踪，内容完整保留 |
| AC-3: `docs/archive/README.md` 存在且为每个归档文件给出归档原因（≥ 4 matches） | ✅ PASS | `grep -c "归档原因\|reason\|Phase 4\|Pre-split" docs/archive/README.md` = **6**（>= 4）；README 包含完整表格，每行含归档原因 + 替代位置 |
| AC-4: 4 个新综合文档存在 | ✅ PASS | 所有 4 个文件存在（docs/README.md 91行、architecture/features.md 148行、architecture/tech-stack.md 216行、architecture/stock-assistant-api.md 308行） |
| AC-5: `docs/README.md` 包含到所有顶层 active 文档的链接（≥ 6 matches） | ✅ PASS | `grep -c "DESIGN.md\|MIGRATION.md\|features.md\|tech-stack.md\|quant-assistant-api.md\|stock-assistant-api.md" docs/README.md` = **7**（>= 6） |
| AC-6: `docs/architecture/features.md` 同时覆盖两个 app（≥ 2 matches） | ✅ PASS | `grep -c "stock-assistant\|quant-assistant" docs/architecture/features.md` = **7**（>= 2）；包含独立章节 "1. stock-assistant 功能矩阵" 和 "2. quant-assistant 功能矩阵" |
| AC-7: `docs/architecture/stock-assistant-api.md` 列出至少 10 条路由 | ✅ PASS | 主要格式为 table rows：`grep -cE "^\| (GET\|POST\|PUT\|DELETE) \|"` = **90**（>= 10）；此为 task spec 提供的 alternative 校验方式 |
| AC-8: `docs/quant_tutorial/`、`docs/tasks/`、`docs/acceptance/` 文件数量未减少 | ✅ PASS | quant_tutorial: 13→13（不变）；tasks: 33→34（+1，新增 phaseF task spec）；acceptance: 36→38（+2，新增验收报告）；三个目录均无文件被删除（`git diff --name-only --diff-filter=D` 无匹配） |

全部 8 个 AC 均为 ✅ PASS。

---

## 测试执行日志摘要

### `test ! -f docs/Claude_Code_Usage_Guide.md && test ! -f docs/factor_guide.md && test ! -f docs/llm-agent-layer-design.md && test ! -f docs/tab-pages-guide.md`
- 退出码：**0**
- 结果：4 个 stale 文档均不存在于 docs/ 顶层

### `test -f docs/archive/legacy/Claude_Code_Usage_Guide.md && test -f docs/archive/legacy/factor_guide.md && test -f docs/archive/legacy/llm-agent-layer-design.md && test -f docs/archive/legacy/tab-pages-guide.md`
- 退出码：**0**
- 结果：4 个文件均存在于 archive/legacy/

### `grep -c "归档原因\|reason\|Phase 4\|Pre-split" docs/archive/README.md`
- 退出码：**0**
- 输出：`6` (>= 4 required)

### `test -f docs/README.md && test -f docs/architecture/features.md && test -f docs/architecture/tech-stack.md && test -f docs/architecture/stock-assistant-api.md`
- 退出码：**0**
- 结果：4 个新文档均存在

### `grep -c "DESIGN.md\|MIGRATION.md\|features.md\|tech-stack.md\|quant-assistant-api.md\|stock-assistant-api.md" docs/README.md`
- 退出码：**0**
- 输出：`7` (>= 6 required)

### `grep -c "stock-assistant\|quant-assistant" docs/architecture/features.md`
- 退出码：**0**
- 输出：`7` (>= 2 required)

### `grep -cE "^\| (GET|POST|PUT|DELETE) \|" docs/architecture/stock-assistant-api.md`
- 退出码：**0**
- 输出：`90` (>= 10 required)
- 注：heading-format grep (`^### (GET|POST|PUT|DELETE)`) 仅匹配 1 行（`### GET /healthz`），因文档主体使用 Markdown table 格式列出路由，task spec 已提供此 alternative 检查方式

### File count checks (quant_tutorial / tasks / acceptance)
- quant_tutorial: before=13, after=13 (unchanged)
- tasks: before=33, after=34 (only additions)
- acceptance: before=36, after=38 (only additions)
- 退出码：**0**（无删除）

---

## 代码 Review 备注

1. **commit 粒度**：4 个 legacy 文件的移动操作被混入了 `feat(risk): add Historical VaR / CVaR...` commit (93e8a92)，而非作为独立的 docs-cleanup 提交。此 workflow 异常已在 854ebfb 的 commit message 中明确标注。从 git 历史可追溯性角度，建议后续类似情况用单独 commit 分离文档操作（`git mv` + `git commit --no-edit`），以保持每个 commit 的单一职责。此问题不影响最终状态的正确性。

2. **文档质量**：
   - `docs/archive/README.md`（26行）内容精炼、表格清晰，每个归档文件均有明确的"归档原因"和"替代/后续位置"。
   - `docs/architecture/stock-assistant-api.md`（308行）覆盖约 92 个 HTTP/WS 端点，含模块分组、路由清单和简要业务说明，与 quant-assistant-api.md 风格对齐。
   - `docs/architecture/features.md` 和 `tech-stack.md` 内容实质，分别对两 app 能力和技术选型有明确覆盖。

3. **无跨 app import**：此 PR 为纯文档操作，无代码变更在本任务范围内，无需检查 import 规范。

---

## 后续动作

PASS，无阻塞项。

- PR 可合并。
- 合 PR 后更新 `docs/acceptance/INDEX.md`（按惯例）。
- 建议（可选）：在未来的 phaseF task 中，将文档移动操作与功能代码分成两个独立 commit，以保持 git 历史整洁。
