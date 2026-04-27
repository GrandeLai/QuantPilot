# Acceptance Report: phaseA.pr-0-cleanup

**Run at**: 2026-04-27T11:58:00Z
**Implementation PRs/commits**:
- `60fb932` — checkpoint pre-split in-flight work（含 5 个死组件的删除）
- `1710e2c` — gitignore build artifacts and untrack stale data files
- `4b6b498` — follow-up: add gitignore entries omitted from 1710e2c
**Diff range**: `ba2c7df..4b6b498`
**Acceptance-agent invocation**: Bootstrap self-validation（acceptance-agent 在本会话尚未注册，由 main 会话执行 AC 检查；遵循 `docs/conventions/acceptance-process.md` 流程）
**Verdict**: ✅ **PASS**

---

## 文件影响范围检查

PR 0 范围内（`1710e2c..4b6b498` 的两个 commit）改动文件：
- `.gitignore` ✅ 在白名单内
- `frontend/tsconfig.tsbuildinfo`（删除）✅ 在白名单内
- `backend/data/quantpilot.duckdb`（删除）✅ 在白名单内
- `backend/data/quantpilot.duckdb.wal`（删除）✅ 在白名单内

补充说明：AC-3 由前置的 checkpoint commit `60fb932` 满足——5 个死组件（AIPanel/AlertsPanel/LLMChat/PluginPanel/SystemPanel）随 checkpoint 一起被删除。这是 plan §4 PR 0 范围中"删除死组件"一项的预先实现，符合 task spec 文件白名单。

**结论**：无超出白名单的改动。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `.gitignore` 含 tsbuildinfo / backend/data/*.duckdb / catboost_info | ✅ PASS | `grep -q "tsconfig.tsbuildinfo" .gitignore` 命中（`**/tsconfig.tsbuildinfo`）；`grep -q "backend/data/.*\.duckdb"` 命中；`grep -q "backend/catboost_info"` 命中 |
| AC-2: `git status --porcelain` 不再显示这些文件 | ✅ PASS | post-commit `git status --short` 输出为空；artifact 模式 grep 无命中 |
| AC-3: 死组件实际不存在 | ✅ PASS | `! test -e` 5 个组件全部 gone（由 checkpoint `60fb932` 删除） |
| AC-4: `cd backend && uv run pytest tests/` 全过 | ✅ PASS | `505 passed, 2 warnings in 21.13s`；含 checkpoint 引入的 5 个新 test 文件（test_ensemble、test_feature_selector、test_pandas_ta_provider、test_quantile_filter、test_walk_forward）全部通过 |
| AC-5: `cd frontend && npm run build` 通过 | ✅ PASS | `✓ built in 339ms`；2984 modules transformed；含 checkpoint 新增的 AutoPilotPanel/QuantResearchPanel/ValidationLab/feature guides 全部成功 bundle |

---

## 测试执行日志摘要

```
=== AC-1: gitignore entries ===
tsbuildinfo: OK
duckdb: OK
catboost: OK

=== AC-2: status clean of artifact patterns ===
OK: gitignore-targeted files no longer in status

=== AC-3: dead frontend components removed ===
AIPanel: gone
AlertsPanel: gone
LLMChat: gone
PluginPanel: gone
SystemPanel: gone

=== AC-1/2/3 ALL PASS ===

=== AC-4: backend pytest ===
... (省略中间)
======================= 505 passed, 2 warnings in 21.13s =======================

=== AC-5: frontend build ===
vite v8.0.7 building client environment for production...
✓ 2984 modules transformed.
✓ built in 339ms
```

---

## 代码 Review 备注

非阻塞性观察：

1. **本 PR 实际上是 3 个 commit**（`60fb932` checkpoint、`1710e2c` 主清理、`4b6b498` gitignore 补丁），不是 1 个。原因：
   - `60fb932` 是为了把 in-flight 工作保存进历史而做的"前置 checkpoint"，包含死组件删除（PR 0 范围）但同时含大量功能代码（用户 in-progress 工作）
   - `1710e2c` 漏 stage 了 `.gitignore`，紧跟 `4b6b498` 补上
   - 这两个问题对 PR 0 整体一致性无伤害；提交历史可读

2. **`frontend/tsconfig.tsbuildinfo`** 在仓库历史里曾经被跟踪过，本次 untrack 后会随 `vite/tsc` 本地构建重新生成但不再进 git。

3. **`backend/data/quantpilot.duckdb`** 物理文件留在用户磁盘上（仅 untrack from git）；这是预期行为——本地数据不进 git 而已。

4. **2 个 sklearn UserWarning**（不阻塞）：`tests/test_ml.py::TestLGBMStrategy::test_fit_and_predict` 和 `test_save_and_load` 提示 LGBMClassifier 的 feature names 不匹配。属于 ML 模块原有 warning，与 PR 0 无关。

5. **新增进 .gitignore 的范围比 spec 略广**：spec 只列了 tsbuildinfo、duckdb*、catboost_info；本 PR 同时加了 `.claude/settings.local.json` 和 `.superpowers/`（实施过程中发现的本地 Claude Code 文件）。这两条属于"PR 0 自然延伸"，不影响 AC，记录在此供 review。

---

## 后续动作

- ✅ 本 PR 可视为已合并（commits 已落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步：进入 PR 1（仓库 layout 骨架），见 `docs/tasks/phaseA/pr-1-skeleton.md`
- 提示：PR 1 之前可以先回答 plan 中仍待确认的"Rhai vs WASM 策略 DSL"和"assistant_frontend / workbench UI 一致性边界"两个开放问题，或留到对应 PR 实施前再答
