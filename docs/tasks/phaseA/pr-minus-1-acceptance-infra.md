# Task phaseA.pr-minus-1-acceptance-infra: 验收基础设施

**Phase**: A
**Status**: passed
**Implementation PR**: <pending commit; see acceptance report>
**Acceptance**: [docs/acceptance/phaseA/pr-minus-1-acceptance-infra.md](../../acceptance/phaseA/pr-minus-1-acceptance-infra.md) — ✅ PASS (2026-04-27)
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 创建 acceptance-agent 定义文件
- 创建验收流程文档
- 创建任务规格模板
- 创建验收记录索引
- 预写 Phase A 全部 8 个 PR（含本 PR）的 task spec
- 创建 `docs/acceptance/{phaseA,phaseB,phaseC,step4}/` 目录结构（空，含 .gitkeep）

### 不做什么
- 不动现有代码
- 不创建 Phase B/C/Step 4 的 task spec（按需后写）
- 不实现自动化 CI 集成（先用本地手动调用）
- 不写 `tools/acceptance-indexer/`（INDEX.md 初期手动维护）

---

## 验收标准（acceptance-agent 逐条核对）

- [ ] **AC-1**: 文件 `.claude/agents/acceptance-agent.md` 存在，含 frontmatter 字段 `name: acceptance-agent`、`tools: Read, Grep, Glob, Bash, ToolSearch`
- [ ] **AC-2**: 文件 `docs/conventions/acceptance-process.md` 存在
- [ ] **AC-3**: 文件 `docs/tasks/_template.md` 存在
- [ ] **AC-4**: 文件 `docs/acceptance/INDEX.md` 存在
- [ ] **AC-5**: 目录 `docs/tasks/phaseA/` 下存在以下 8 个 task spec 文件：`pr-minus-1-acceptance-infra.md`、`pr-0-cleanup.md`、`pr-1-skeleton.md`、`pr-2-schemas-codegen.md`、`pr-3-common-py.md`、`pr-4-stock-assistant.md`、`pr-5-quant-assistant-py.md`、`pr-6-frontend-split.md`、`pr-7-scripts-ci-docs.md`
- [ ] **AC-6**: 目录 `docs/acceptance/{phaseA,phaseB,phaseC,step4}/` 都存在（可含 `.gitkeep`）
- [ ] **AC-7**: 每个 Phase A task spec 都有 `验收标准` 区块且至少含 1 条 AC
- [ ] **AC-8**: 每个 Phase A task spec 都有 `测试集合` 和 `文件影响范围` 区块

---

## 测试集合

```bash
# AC-1: agent 定义文件存在且 frontmatter 正确
test -f .claude/agents/acceptance-agent.md && \
  grep -q "^name: acceptance-agent$" .claude/agents/acceptance-agent.md && \
  grep -q "^tools:" .claude/agents/acceptance-agent.md

# AC-2,3,4: 核心文档存在
test -f docs/conventions/acceptance-process.md
test -f docs/tasks/_template.md
test -f docs/acceptance/INDEX.md

# AC-5: 8 个 Phase A task spec 都在
ls docs/tasks/phaseA/pr-minus-1-acceptance-infra.md \
   docs/tasks/phaseA/pr-0-cleanup.md \
   docs/tasks/phaseA/pr-1-skeleton.md \
   docs/tasks/phaseA/pr-2-schemas-codegen.md \
   docs/tasks/phaseA/pr-3-common-py.md \
   docs/tasks/phaseA/pr-4-stock-assistant.md \
   docs/tasks/phaseA/pr-5-quant-assistant-py.md \
   docs/tasks/phaseA/pr-6-frontend-split.md \
   docs/tasks/phaseA/pr-7-scripts-ci-docs.md

# AC-6: 验收记录目录就位
test -d docs/acceptance/phaseA && \
  test -d docs/acceptance/phaseB && \
  test -d docs/acceptance/phaseC && \
  test -d docs/acceptance/step4

# AC-7: 每个 task spec 都有 AC 标题
for f in docs/tasks/phaseA/*.md; do
  grep -q "^## 验收标准" "$f" || (echo "MISSING ACs: $f" && exit 1)
done

# AC-8: 每个 task spec 都有"测试集合"和"文件影响范围"
for f in docs/tasks/phaseA/*.md; do
  grep -q "^## 测试集合" "$f" || (echo "MISSING tests: $f" && exit 1)
  grep -q "^## 文件影响范围" "$f" || (echo "MISSING file scope: $f" && exit 1)
done
```

---

## 文件影响范围（白名单）

```
- .claude/agents/acceptance-agent.md
- docs/conventions/acceptance-process.md
- docs/tasks/_template.md
- docs/tasks/phaseA/**
- docs/acceptance/INDEX.md
- docs/acceptance/{phaseA,phaseB,phaseC,step4}/.gitkeep
```

**不允许**改动现有代码、CLAUDE.md、README.md、其他 docs 文件。

---

## 引用

- **设计来源**：plan §9
- **上游依赖**：无（这是第一个 PR）
- **下游依赖**：所有后续 PR 都依赖本 PR 提供的验收基础设施
- **相关文档**：`/Users/bytedance/.claude/plans/python-rust-common-wiggly-river.md` §9
