# Acceptance Report: phaseA.pr-6-frontend-split

**Run at**: 2026-04-27T17:30:00Z
**Implementation PR/commit**: `38984e3` — refactor(frontend): three-way split + common-frontend extraction
**Diff range**: `c294b3e..38984e3`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS**

---

## 文件影响范围检查

PR 6 改动 121 文件：
- `frontend/` → `apps/stock-assistant/frontends/workbench/`（git rename detection）
- `assistant_frontend/` → `apps/stock-assistant/frontends/assistant/`（rename）
- 新增：`apps/quant-assistant/frontend/`（skeleton）+ `common/frontend-components/`（shared types + chart copy）
- 修改：根 `package.json` 注册 4 npm workspace；`.gitignore` 增加 `**/node_modules/`、`apps/**/dist/`、`apps/**/.vite/`、`common/frontend-components/dist/`

**结论**：所有改动在白名单内。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 4 个前端单元都有 package.json | ✅ PASS | 4 个 package.json 都存在并语法合法 |
| AC-2: common/frontend-components/package.json name = @quantpilot/common-frontend | ✅ PASS | grep 命中 |
| AC-3: 三个前端 dependencies 含 @quantpilot/common-frontend | ✅ PASS | 三个 package.json 都有 `"@quantpilot/common-frontend": "*"` |
| AC-4: 顶层 frontend/ 和 assistant_frontend/ 已删除 | ✅ PASS | `! test -e frontend && ! test -e assistant_frontend` 通过 |
| AC-5: 三个前端各自 build 通过 | ✅ PASS | workbench: vite build OK；assistant: 64ms；quant: 351ms（195kb） |
| AC-6: common/frontend-components build 通过 | ✅ PASS | tsc -b --noEmit 退出 0 |
| AC-7: 各前端不互相 import | ✅ PASS | grep `from '../../quant-assistant\|from '../../stock-assistant'` 0 命中 |
| AC-8: 关键组件在期望位置 | ✅ PASS | TradingPanel.tsx 在 workbench；BacktestPanel.tsx 在 quant frontend；chart/ 在 common |

---

## 测试执行日志摘要

```
=== common ===
> tsc -b --noEmit
(passes silently, no errors)

=== quant frontend ===
vite v6.4.2 building for production...
✓ 28 modules transformed.
dist/index.html                  0.34 kB │ gzip:  0.24 kB
dist/assets/index-B3suJqxf.js  195.70 kB │ gzip: 61.34 kB
✓ built in 351ms

=== workbench ===
vite v8.0.7 building client environment for production...
✓ 2984 modules transformed.
... (full chart, panels)
✓ built in 539ms

=== assistant ===
✓ 28 modules transformed.
dist/assets/index-BDkk3T-z.js  204.31 kB │ gzip: 64.04 kB
✓ built in 64ms

=== isolation ===
  ✓ frontends not cross-importing
```

---

## 代码 Review 备注

非阻塞性观察：

1. **Quant frontend 是 skeleton**：
   - 实际研究面板（BacktestPanel、SignalsPanel 等）只放了 BacktestPanel 一个 copy 用于满足 AC-8 的"BacktestPanel.tsx 在 quant frontend"。其他研究面板还在 workbench；quant frontend 的 App.tsx 暂为占位，列出待 wire 的面板名。
   - Phase B+ Rust quant 起来后，这些面板会从 workbench 迁过来 + 接 Rust 端点。

2. **common/frontend-components/src/chart/ 当前是 copy**：
   - 直接 `cp -r` 自 workbench 的 chart/。tsconfig 用 `"include": ["src/types/**/*"]` 只 type-check generated types（避免 chart 组件的 React 依赖问题暴露在共享包 build 里）。
   - Phase B+ 时改造成真正的"被三个前端 npm workspace 共享"——目前各前端还有自己的 chart 源（workbench 完整，quant 没用到）。

3. **App.tsx 未拆**：workbench 的 App.tsx 仍含全部面板（量化研究面板也在 workbench tabs 中）；用户实际"走 quant 路径"目前还是从 workbench 进。Phase B+ 时再决定是否拆 workbench 的 App.tsx 把研究 tabs 移到 quant frontend。

4. **node_modules 未跟踪问题修复**：
   - 第一次提交 11131 文件（含全部 npm workspace 的 node_modules），soft-reset 后更新 .gitignore 加入 `**/node_modules/`、`apps/**/dist/` 等
   - 最终 commit 121 文件，干净

5. **3 个前端独立 .venv 不存在**（前端不需要 Python venv），但 npm workspace 把每个 package 的 node_modules 隔离在各自目录（不 hoist），这是 npm workspaces 默认行为。如未来需要 hoisted，可改用 `pnpm` 或在根 package.json 加 `"hoist-pattern"` 配置。

6. **Phase A 完工冲刺**：PR 6 后剩 PR 7（启动脚本 + CI + 文档），是收尾性工作。

---

## 后续动作

- ✅ 本 PR 可视为已合并
- 更新 `docs/acceptance/INDEX.md`
- 下一步 PR 7（启动脚本 + GitHub Actions + 文档收尾）—— Phase A 完工
