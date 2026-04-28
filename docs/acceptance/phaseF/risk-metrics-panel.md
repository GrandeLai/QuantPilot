# Acceptance Report: phaseF.risk-metrics-panel

**Run at**: 2026-04-28T00:00:00Z
**Implementation commit**: `a0c5cb9`
**Diff range**: `a0c5cb9^..a0c5cb9`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

---

## 文件影响范围检查

`git diff --name-only a0c5cb9^..a0c5cb9` 输出共 5 个路径：

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/frontends/workbench/src/api/client.risk.test.ts` | 允许（新建） |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | 允许（修改：追加风控类型 + 函数） |
| `apps/stock-assistant/frontends/workbench/src/components/RiskMetricsPanel.tsx` | 允许（新建） |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | 允许（挂载点） |
| `docs/tasks/phaseF/risk-metrics-panel.md` | 允许（task spec 本身） |

`package.json`、`package-lock.json`、`apps/stock-assistant/backend/` 均未出现在 diff 中（满足 AC-7 / AC-8 硬约束）。

**文件范围结论：全部 5 个路径均在白名单内。无违规。**

---

## 测试执行日志摘要

### 1. TypeScript 类型检查（AC-4）
```
npm run type-check  →  tsc --noEmit
(no errors, no output)
EXIT: 0
```

### 2. 前端 build（AC-5）
```
npm run build  →  tsc -b && vite build
vite v8.0.10  2996 modules transformed
dist/assets/... ✓ built in 342ms
EXIT: 0
```
无 error 输出，仅 GVM shell hook 警告（与构建无关）。

### 3. Node 原生测试（AC-6）
```
node --test --experimental-strip-types src/api/client.risk.test.ts
✔ fetchRiskSummary posts returns array to /api/risk/summary (22.69ms)
✔ fetchRiskKellyBinary builds correct binary-mode body (0.19ms)
✔ fetchRiskKellyBinary respects custom fraction and cap (0.12ms)
✔ fetchRiskKellyFromReturns sends mode=returns body (0.13ms)
✔ postRisk surfaces error detail from FastAPI 400 response (0.25ms)
✔ postRisk surfaces non-JSON error body as plain text (0.13ms)
ℹ tests 6  pass 6  fail 0
EXIT: 0
```

### 4. package.json / lock 未改（AC-7）
```
git diff main -- apps/stock-assistant/frontends/workbench/package.json ...
(no output)
EXIT: 0
```

### 5. 后端未改（AC-8）
```
git diff main -- apps/stock-assistant/backend/
(no output)
EXIT: 0
```

---

## AC 逐条核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 两个新文件存在 | PASS | `RiskMetricsPanel.tsx` 与 `client.risk.test.ts` 均在 diff 中新建，`test -f` 返回 0 |
| AC-2: client.ts 扩展（函数 ≥ 3 + RiskSummaryResult） | PASS | `grep -c` 返回 3；`grep -q "RiskSummaryResult"` 返回 0；client.ts 行 426-512 新增 5 个接口 + 3 个导出函数 |
| AC-3: RiskReviewCenter 挂载 RiskMetricsPanel | PASS | `grep -q "RiskMetricsPanel"` 返回 0 |
| AC-4: TypeScript 类型检查退出码 0 | PASS | `tsc --noEmit` 无错误，退出码 0 |
| AC-5: 前端 build 退出码 0，无 error | PASS | vite build 成功，2996 模块，退出码 0，无 error 行 |
| AC-6: node:test 全过，用例数 ≥ 6 | PASS | 6 tests, 6 pass, 0 fail；退出码 0 |
| AC-7: package.json / lock 无变更 | PASS | `git diff main` 输出为空 |
| AC-8: 后端无变更 | PASS | `git diff main -- apps/stock-assistant/backend/` 输出为空 |
| AC-9: 其它 *Panel.tsx 文件未改 | PASS | `git diff a0c5cb9^..a0c5cb9 --name-only -- '*Panel.tsx'` 仅列出 `RiskMetricsPanel.tsx` |

全部 9 项 AC 均为 PASS，无 PARTIAL，无 FAIL。

---

## 代码 Review 备注

1. `RiskMetricsPanel.tsx` 有模块级 JSDoc（文件头注释说明功能和 API 来源），符合项目规范。
2. 所有 React 状态使用完整 TypeScript 泛型（`useState<string>`、`useState<RiskSummaryResult | null>` 等），type hints 完整。
3. 无跨 app import：所有 import 来自同 workbench 内的 `./ui/MetricCard`、`../lib/utils`、`../api/client`。
4. `client.ts` 新增部分以 `postRisk` 内部工厂函数统一错误处理，4xx/5xx 抛 `Error(detail)`，网络错误透传，与 task spec 一致。
5. 错误提示以红色 banner 展示，加载时按钮 disable + 文字变为 "Analyzing..."，符合 spec 要求。
6. `sharpe_decay === null` 时显示 "Not enough history" 占位文本，符合 spec 要求。
7. Kelly Calculator 使用独立子状态（`kellyLoading`、`kellyError`），与主分析区互不干扰。
8. 测试文件 `client.risk.test.ts` 使用 mock fetch 模式（与现有 `client.crypto.test.ts` 风格一致），覆盖：URL 正确性、请求 body 结构、响应解析、HTTP 4xx/5xx 错误处理，共 6 个用例满足 spec 下限。
9. 无顺带重构；无引入新 npm 依赖；不动其他 panel 文件。

---

## 后续动作

PASS — PR 可合。无修复项。Phase F.1 风控三件套（risk-engine-core + risk-sharpe-decay + risk-var-cvar + risk-api-endpoints + risk-metrics-panel）全部完成。
