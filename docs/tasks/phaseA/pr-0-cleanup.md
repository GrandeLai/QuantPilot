# Task phaseA.pr-0-cleanup: 仓库清理预备

**Phase**: A
**Status**: passed
**Implementation PR**: commits `60fb932`, `1710e2c`, `4b6b498`
**Acceptance**: [docs/acceptance/phaseA/pr-0-cleanup.md](../../acceptance/phaseA/pr-0-cleanup.md) — ✅ PASS (2026-04-27)
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 处理当前 `git status` 中累积的未提交改动：要么完成、要么撤销，进入干净 main
- 把构建产物加进 `.gitignore`：`frontend/tsconfig.tsbuildinfo`、`backend/data/quantpilot.duckdb*`、`backend/catboost_info/` 等
- 删除已确认不再使用的旧 frontend 组件（git status 中显示 deleted 但未提交的：`AIPanel.tsx`、`AlertsPanel.tsx`、`LLMChat.tsx`、`SystemPanel.tsx`、`PluginPanel.tsx`）
- 提交 `.superpowers/` 是否进 `.gitignore`（视为 Claude Code 工作目录残留）的决定

### 不做什么
- 不创建任何新目录结构（PR 1 才做）
- 不动 source code 逻辑（除了删确认死代码）
- 不修复 git status 里现存的功能性 in-progress 工作——那些先各自完成对应任务再做拆分

---

## 验收标准

- [ ] **AC-1**: `.gitignore` 包含 `**/tsconfig.tsbuildinfo`、`backend/data/*.duckdb`、`backend/data/*.duckdb.wal`、`backend/catboost_info/`
- [ ] **AC-2**: `git status --porcelain` 不再显示这些文件作为 modified/deleted（要么进 .gitignore 要么真删了）
- [ ] **AC-3**: 已删除的 frontend 组件文件实际不存在：`! test -e frontend/src/components/AIPanel.tsx && ! test -e frontend/src/components/AlertsPanel.tsx && ! test -e frontend/src/components/LLMChat.tsx && ! test -e frontend/src/components/SystemPanel.tsx && ! test -e frontend/src/components/PluginPanel.tsx`
- [ ] **AC-4**: 现有 `cd backend && uv run pytest` 全过（验证清理没破坏后端）
- [ ] **AC-5**: 现有 `cd frontend && npm run build` 通过（验证清理没破坏前端）

---

## 测试集合

```bash
# AC-1
grep -q "tsconfig.tsbuildinfo" .gitignore
grep -q "backend/data/.*\.duckdb" .gitignore
grep -q "backend/catboost_info" .gitignore

# AC-2: git status 干净（除本 PR 明确改动）
git status --porcelain | grep -E "tsbuildinfo|duckdb|catboost_info" && echo "STILL DIRTY" && exit 1
echo "OK: gitignore-targeted files no longer in status"

# AC-3: 旧组件确实删除
! test -e frontend/src/components/AIPanel.tsx
! test -e frontend/src/components/AlertsPanel.tsx
! test -e frontend/src/components/LLMChat.tsx
! test -e frontend/src/components/SystemPanel.tsx
! test -e frontend/src/components/PluginPanel.tsx

# AC-4
cd backend && uv run pytest tests/ -x

# AC-5
cd frontend && npm run build
```

---

## 文件影响范围（白名单）

```
- .gitignore
- frontend/src/components/{AIPanel,AlertsPanel,LLMChat,SystemPanel,PluginPanel}.tsx (删除)
- backend/data/quantpilot.duckdb* (删除或保留进 gitignore，不在仓库里)
- backend/catboost_info/ (删除目录或保留进 gitignore)
- frontend/tsconfig.tsbuildinfo (删除或保留进 gitignore)
```

---

## 引用

- **设计来源**：plan §4 PR 0
- **上游依赖**：phaseA.pr-minus-1-acceptance-infra
- **下游依赖**：phaseA.pr-1-skeleton
