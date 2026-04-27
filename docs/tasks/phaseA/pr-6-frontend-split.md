# Task phaseA.pr-6-frontend-split: 前端三拆 + 共享组件抽出

**Phase**: A
**Status**: passed
**Implementation PR**: commit `38984e3`
**Acceptance**: [docs/acceptance/phaseA/pr-6-frontend-split.md](../../acceptance/phaseA/pr-6-frontend-split.md) — ✅ PASS (2026-04-27)
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 创建三个独立前端 + 一个共享组件包：
  - `apps/stock-assistant/frontends/workbench/`（接收现 frontend/ 中的人决策面板）
  - `apps/stock-assistant/frontends/assistant/`（接收现 assistant_frontend/ 整体）
  - `apps/quant-assistant/frontend/`（接收现 frontend/ 中的研究面板）
  - `common/frontend-components/`（接收 chart、Monaco 封装、API client base、布局壳；含 PR 2 已生成的 types/）

- 移动现 `frontend/src/components/` 各组件到对应位置（详见 plan §1 归属表）：
  - 股票/期权/加密 + LLM 面板 → workbench
  - 研究面板（Backtest/MLStrategy/Signals/Optimization/QuantResearch/ValidationLab/StrategyWorkshop/StrategyEditor/StrategyGenerator/StrategyPanel）→ quant-assistant/frontend
  - 共享组件（chart/、IndicatorSelector、TimeframeSelector）→ common/frontend-components
  - 整体：`assistant_frontend/` → `apps/stock-assistant/frontends/assistant/`

- 各前端的 `package.json` 注册 npm workspace 并依赖 `@quantpilot/common-frontend`（即 `common/frontend-components`）
- 用 PR 2 codegen 生成的 TS 类型替换各前端中的手写 API 类型
- 现 `frontend/`、`assistant_frontend/` 顶层目录删除

### 不做什么
- 不重构组件内部逻辑——只搬+改 import + 切类型
- 不写启动脚本（PR 7）
- 不动后端

---

## 验收标准

- [ ] **AC-1**: 4 个前端单元都有 `package.json`：`apps/stock-assistant/frontends/workbench/package.json`、`apps/stock-assistant/frontends/assistant/package.json`、`apps/quant-assistant/frontend/package.json`、`common/frontend-components/package.json`
- [ ] **AC-2**: `common/frontend-components/package.json` 的 `name` 是 `@quantpilot/common-frontend` 或类似
- [ ] **AC-3**: 三个前端 `package.json` 的 `dependencies` 都含 `@quantpilot/common-frontend`
- [ ] **AC-4**: 顶层 `frontend/` 和 `assistant_frontend/` 目录都已删除
- [ ] **AC-5**: 三个前端各自 build 通过：
  - `cd apps/stock-assistant/frontends/workbench && npm run build` 退出码 0
  - `cd apps/stock-assistant/frontends/assistant && npm run build` 退出码 0
  - `cd apps/quant-assistant/frontend && npm run build` 退出码 0
- [ ] **AC-6**: `common/frontend-components` build 通过：`cd common/frontend-components && npm run build` 退出码 0
- [ ] **AC-7**: 各前端不互相 import：`! grep -r "from '\.\.\/\.\.\/quant-assistant\|from '\.\.\/\.\.\/stock-assistant" apps/`
- [ ] **AC-8**: 关键组件确实在期望位置：
  - `apps/stock-assistant/frontends/workbench/src/components/TradingPanel.tsx` 存在
  - `apps/quant-assistant/frontend/src/components/BacktestPanel.tsx` 存在
  - `common/frontend-components/src/chart/` 目录存在

---

## 测试集合

```bash
# AC-1
test -f apps/stock-assistant/frontends/workbench/package.json
test -f apps/stock-assistant/frontends/assistant/package.json
test -f apps/quant-assistant/frontend/package.json
test -f common/frontend-components/package.json

# AC-2
grep -q '"name":.*"@quantpilot/common-frontend"' common/frontend-components/package.json

# AC-3
for f in apps/stock-assistant/frontends/workbench/package.json \
         apps/stock-assistant/frontends/assistant/package.json \
         apps/quant-assistant/frontend/package.json; do
  grep -q '@quantpilot/common-frontend' "$f" || (echo "MISSING dep: $f" && exit 1)
done

# AC-4
! test -e frontend
! test -e assistant_frontend

# AC-5
npm install
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)

# AC-6
(cd common/frontend-components && npm run build)

# AC-7: 任意前端不直接 import 另外的前端
! grep -rE "from ['\"]\.\.\/\.\.\/quant-assistant|from ['\"]\.\.\/\.\.\/stock-assistant" apps/

# AC-8
test -f apps/stock-assistant/frontends/workbench/src/components/TradingPanel.tsx
test -f apps/quant-assistant/frontend/src/components/BacktestPanel.tsx
test -d common/frontend-components/src/chart
```

---

## 文件影响范围（白名单）

```
- apps/stock-assistant/frontends/workbench/**
- apps/stock-assistant/frontends/assistant/**
- apps/quant-assistant/frontend/**
- common/frontend-components/**
- frontend/** (整体删除)
- assistant_frontend/** (整体删除)
- package.json (顶层；npm workspaces 调整)
- package-lock.json (重生成)
```

---

## 引用

- **设计来源**：plan §1 模块归属表、§4 PR 6
- **上游依赖**：phaseA.pr-5-quant-assistant-py
- **下游依赖**：phaseA.pr-7-scripts-ci-docs
