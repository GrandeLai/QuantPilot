# Acceptance Report: phaseF3.tlh-panel

**Run at**: 2026-04-29T09:40:40Z
**Implementation PR**: working tree (uncommitted changes vs HEAD b69856f)
**Diff range**: `HEAD` (git diff HEAD — modified tracked files + untracked new files)
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-29
**Verdict**: NEEDS-REVISION

---

## 文件影响范围检查

- 改动文件总数（tracked, `git diff --name-only HEAD`）：4
- 在白名单内：3
- 超出白名单：1

白名单内文件：
- `apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx` (new, untracked — not in git diff, but is target of AC-1)
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` ✅
- `apps/stock-assistant/frontends/workbench/src/api/client.ts` ✅

超出白名单：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`：添加了 `tlh_router` 和 `execution_router` 注册。**不在 task spec 白名单内。**

判定：此改动属于必要的伴随文件（backend router 注册是让 `/api/tlh/scan` 端点可访问的前提），task spec 白名单漏列。按 `docs/conventions/acceptance-process.md` 规定，这属于 "spec 白名单遗漏必要伴随文件"，对应 **NEEDS-REVISION**（需修 spec 白名单后重验），而非硬 FAIL。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件存在 `TLHPanel.tsx` | ✅ PASS | `test -f` 退出码 0；文件存在于 `apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx` |
| AC-2: API 调用 `tlh/scan` 或 `fetchTLH` | ✅ PASS | `grep -q "fetchTLH"` 匹配成功；TLHPanel.tsx 第 14 行 import `fetchTLHScan`，第 269 行调用；client.ts 实现 `fetchTLHScan` 调用 `${BASE}/tlh/scan` |
| AC-3: 集成进 RiskReviewCenter | ✅ PASS | `grep -q "TLHPanel"` 匹配成功；RiskReviewCenter.tsx 第 8 行 import，第 14 行 `<TLHPanel />` 渲染 |
| AC-4: dark-theme tokens (#0E1014 / #151619 / #00C087) | ✅ PASS | `grep -q "#0E1014\|#151619\|#00C087"` 匹配成功；三个 token 均出现在 TLHPanel.tsx（#0E1014 第 289、299行；#151619 第 72、370、516行；#00C087 第 64、67、128、478、525行等） |
| AC-5: 免责声明存在 | ✅ PASS | `grep -q "不构成税务建议\|CPA\|disclaimer"` 匹配成功；文件顶部 docstring 第 9 行"不构成税务建议"、第 9 行"CPA"、第 51 行"disclaimer"，Disclaimer 组件第 51 行渲染中文免责声明 |
| AC-6: type-check + build 通过 | ✅ PASS | `npm run type-check` 退出码 0（tsc --noEmit 无错误）；`npm run build` 退出码 0（tsc -b + vite build，2996 modules transformed，无警告/错误） |

---

## 测试执行日志摘要

### `test -f apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`
- 退出码：0

### `grep -q "tlh/scan\|fetchTLH" .../TLHPanel.tsx`
- 退出码：0
- 匹配：第 14 行 `import { ..., fetchTLHScan } from "../api/client"`，第 269 行 `fetchTLHScan(lots, prices)`

### `grep -q "TLHPanel" .../RiskReviewCenter.tsx`
- 退出码：0
- 匹配：第 8 行 import，第 14 行 `<TLHPanel />`

### `grep -q "#0E1014\|#151619\|#00C087" .../TLHPanel.tsx`
- 退出码：0
- 多处匹配，三色均存在

### `grep -q "不构成税务建议\|CPA\|disclaimer" .../TLHPanel.tsx`
- 退出码：0
- 多处匹配

### `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run type-check)`
- 退出码：0
- 输出：`tsc --noEmit` 完成，无错误

### `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run build)`
- 退出码：0
- 输出：`vite v8.0.10 building client environment for production...` → `✓ built in 300ms`；2996 modules transformed，无类型错误，无 linting 警告

---

## 代码 Review 备注

1. **实现质量高**：TLHPanel.tsx 包含完整的模块级 JSDoc 注释（第 1-12 行），类型定义完整（接口 LotRow、CandidateCardProps），React 函数组件结构清晰，无跨 app import。

2. **client.ts 增量**：新增 TaxLotInput、TLHCandidate、TLHScanResponse、TLHReplacementResponse 接口及 fetchTLHScan 函数，类型完整，无破坏性改动。

3. **超出白名单的 main.py**：差异仅为添加两行 router import + 两行 include，属于最小必要改动。backend 相关的 untracked 新文件（tlh/、execution/、api/tlh.py、api/execution.py 及测试文件）不在此 task 的 git diff 范围内，超出本 task 规范但属于 backend task 范围，不影响此次前端面板验收。

4. **无顺带重构**：RiskReviewCenter.tsx 仅增加 import 和一个组件标签，未动其他代码。

---

## 后续动作

**NEEDS-REVISION 原因**：task spec 白名单遗漏了 `apps/stock-assistant/backend/src/quantpilot_stock/main.py`，该文件的修改是 TLH API 端点注册所必须的。

**建议**（选一）：

**方案 A（推荐）**：将 `apps/stock-assistant/backend/src/quantpilot_stock/main.py` 加入 task spec 文件白名单，重新验收（结果必为 PASS，因为所有 6 条 AC 均通过）。

**方案 B**：将 main.py 的 router 注册拆分至独立 backend task spec（如 `phaseF3.tlh-backend`），并从本次改动中回滚 main.py 的修改，待 backend task 验收时一并提交。

建议选方案 A，因为 main.py 的改动极小（4 行），且所有 6 条 AC 已全部通过，仅需 spec 白名单补齐即可 PASS。
