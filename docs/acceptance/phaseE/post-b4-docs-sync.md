# Acceptance Report: phaseE.post-b4-docs-sync

**Run at**: 2026-04-28T15:50:00Z
**Implementation PR**: commit 644a860
**Diff range**: `644a860^ .. 644a860`
**Acceptance-agent invocation**: claude-sonnet-4-6 (session 2026-04-28)
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：4
- 在白名单内：4
- 超出白名单：0

实际改动文件与白名单对照：

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/frontends/workbench/vite.config.ts` | 在白名单 |
| `docs/DESIGN.md` | 在白名单 |
| `docs/MIGRATION.md` | 在白名单 |
| `docs/architecture/frontend-routing.md` | 在白名单 |

注：`docs/tasks/phaseE/post-b4-docs-sync.md` 已在前一次提交中创建，不在本次 diff 内；验收记录文件 `docs/acceptance/phaseE/post-b4-docs-sync.md` 由 acceptance-agent 生成，白名单中已声明。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `grep "8000" apps/stock-assistant/frontends/workbench/vite.config.ts` 无输出 | PASS | 命令无输出，退出码 1（grep 无匹配），符合期望 |
| AC-2: `grep "8001" apps/stock-assistant/frontends/workbench/vite.config.ts` 有输出 | PASS | 输出：`target: "http://127.0.0.1:8001"` |
| AC-3: `grep "api/ml" docs/architecture/frontend-routing.md` 有输出 | PASS | 输出：`\| \`/api/ml/*\` \| \`http://localhost:8002\` \| ONNX model inference (\`/api/ml/predict\`) \|` |
| AC-4: `grep -E "B4\|mypy" docs/DESIGN.md` 有输出 | PASS | 输出 2 行：依赖列表中的 `mypy` 和新增的 B4 路线图条目 |
| AC-5: `grep -E "B4\|mypy" docs/MIGRATION.md` 有输出 | PASS | 输出：Phase E 后续段落中的 B4/mypy 相关行 |
| AC-6: `(cd apps/stock-assistant/frontends/workbench && npm run build)` 无错误退出 | PASS | 退出码 0；2996 modules transformed，dist 生成成功 |

---

## 测试执行日志摘要

### `grep "8000" apps/stock-assistant/frontends/workbench/vite.config.ts`
- 退出码：1（无匹配）
- 关键输出：（无输出）

### `grep "8001" apps/stock-assistant/frontends/workbench/vite.config.ts`
- 退出码：0
- 关键输出：`        target: "http://127.0.0.1:8001",`

### `grep "api/ml" docs/architecture/frontend-routing.md`
- 退出码：0
- 关键输出：`| \`/api/ml/*\` | \`http://localhost:8002\` | ONNX model inference (\`/api/ml/predict\`) |`

### `grep -E "B4|mypy" docs/DESIGN.md`
- 退出码：0
- 关键输出：
  ```
  FastAPI，Polars，LiteLLM，pluggy（插件系统），pytest，ruff / mypy
  | B4 | ✅ 2026-04-28 | mypy 类型覆盖：common/python + stock-assistant 各 0 错误 |
  ```

### `grep -E "B4|mypy" docs/MIGRATION.md`
- 退出码：0
- 关键输出：（B4/mypy 段落标题及正文，多行匹配）

### `(cd apps/stock-assistant/frontends/workbench && npm run build)`
- 退出码：0
- 关键输出：`tsc -b && vite build`；`✓ 2996 modules transformed.`；`✓ built in 380ms`

---

## 代码 Review 备注

1. **vite.config.ts**：单行改动，`8000` → `8001`，精确且最小化。
2. **frontend-routing.md**：新增 `/api/ml/*` 行，同时移除了过时的"Warning: stale port"注释——符合 task spec "移除 Warning 注释"的要求。workbench proxy 表端口同步更新为 8001。
3. **DESIGN.md**：仅追加 B4 一行，不影响既有内容。
4. **MIGRATION.md**：新增 47 行的 A1–A3 + B1 + B4 迁移记录段，内容与各任务实际 acceptance 报告一致，叙述清晰。
5. 无跨 app import，无范围外改动，无测试跳过，无新增依赖。

---

## 后续动作

- PR 可合并，无阻塞项。
- 建议用户在合 PR 后更新 `docs/acceptance/INDEX.md`，添加本任务记录行。
