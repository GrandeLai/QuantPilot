# Task phaseF.risk-metrics-panel: 前端 RiskMetricsPanel

**Phase**: Phase F.1（风控三件套之 5 — 收尾任务）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

F.1.4 已暴露 `/api/risk/*` 5 个端点。本任务为 workbench 前端添加可视化面板，把风控三件套整合进 `RiskReviewCenter`，让用户能直接看到 Vol Target / Sharpe Decay / VaR / Kelly 4 类指标。

### 做什么

#### 1. 扩展 `src/api/client.ts`

新增 5 个函数 + 对应类型：

```ts
export interface VolTargetResult { realized_vol: number; target_vol: number; scale_factor: number; regime: "low"|"normal"|"high"|"crisis"; }
export interface SharpeDecayResult { recent_sharpe: number; baseline_mean: number; baseline_std: number; z_score: number; alert_level: "green"|"yellow"|"red"; n_baseline_samples: number; }
export interface VarResult { n_samples: number; worst_loss: number; method: string; var_95?: number; var_99?: number; cvar_95?: number; cvar_99?: number; parametric_var_95?: number; parametric_var_99?: number; }
export interface RiskSummaryResult { n_samples: number; vol_target: VolTargetResult; sharpe_decay: SharpeDecayResult | null; var: VarResult; }
export interface KellyResult { full_kelly: number; fractional_kelly: number; capped_kelly: number; mode: "binary" | "returns"; fraction: number; cap: number; }

export async function fetchRiskSummary(returns: number[]): Promise<RiskSummaryResult>
export async function fetchRiskKellyBinary(winRate: number, payoffRatio: number, fraction?: number, cap?: number): Promise<KellyResult>
export async function fetchRiskKellyFromReturns(returns: number[], fraction?: number, cap?: number): Promise<KellyResult>
```

错误处理：HTTP 4xx/5xx 抛 `Error(detail)`；网络错误抛原始 Error。

#### 2. 新建 `src/components/RiskMetricsPanel.tsx`

布局（沿用 PortfolioPanel/SentimentPanel 设计语言，使用现有 MetricCard）：

- 顶部：标题 "Risk Metrics" + 数据输入区
  - Textarea：粘贴 simple return 序列（每行一个数字 或 逗号分隔）
  - 按钮：「Load Demo Returns」生成 500 个 N(0.0005, 0.012) 样本
  - 按钮：「Analyze Risk」调 `fetchRiskSummary`
- 4 个区块（垂直堆叠或 2×2 grid，按屏幕宽度）：
  1. **Vol Target** — 4 个 MetricCard：Realized Vol / Target Vol / Scale Factor / Regime（用 badge 配合颜色：low=blue, normal=green, high=orange, crisis=red）
  2. **Sharpe Decay** — 4 个 MetricCard：Recent Sharpe / Baseline Mean ± Std / Z-Score / Alert Level（badge：green/yellow/red）。当 sharpe_decay=null 显示 "Not enough history"。
  3. **VaR / CVaR** — 5 个 MetricCard：Worst Loss / VaR 95 / CVaR 95 / VaR 99 / CVaR 99
  4. **Kelly Calculator**（独立子表单）— 输入 win_rate + payoff_ratio + 可选 fraction/cap → 调 `fetchRiskKellyBinary`，显示 full / fractional / capped 三档

错误：失败时在面板顶部红条显示 error message。
Loading：按钮 disable + spinner。

#### 3. 修改 `src/components/workbench/RiskReviewCenter.tsx`

把 `<RiskMetricsPanel />` 加在 `<PortfolioPanel />` 之上（最上面），让用户进入 Risk Review Center 第一眼看到整体风控指标。

#### 4. 测试 `src/components/RiskMetricsPanel.test.tsx`（或 .ts utility）

由于本仓库前端用 node:test 而不是 React Testing Library，本任务**不写组件渲染测试**；改为：

- 在 `src/api/client.risk.test.ts` 用 node:test 测试 4 个新 API 函数：mock fetch、验证 URL/body/响应解析（≥ 6 个用例，参考 `client.crypto.test.ts` 风格）

### 不做什么

- 不接入 portfolio 自动拉取持仓收益（留到下一任务，本期手动粘贴/Demo）
- 不做 Vol Skew Radar / EVT 尾部（不在 MVP 范围）
- 不做 i18n
- 不引入新 npm 依赖
- 不动其它 panel 文件

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/RiskMetricsPanel.tsx`
  - `test -f apps/stock-assistant/frontends/workbench/src/api/client.risk.test.ts`
- [ ] **AC-2**: client.ts 扩展
  - `grep -c "fetchRiskSummary\|fetchRiskKellyBinary\|fetchRiskKellyFromReturns" apps/stock-assistant/frontends/workbench/src/api/client.ts` ≥ 3
  - `grep -q "RiskSummaryResult" apps/stock-assistant/frontends/workbench/src/api/client.ts`
- [ ] **AC-3**: RiskReviewCenter 已挂载
  - `grep -q "RiskMetricsPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- [ ] **AC-4**: TypeScript 类型检查
  - `(cd apps/stock-assistant/frontends/workbench && npm run type-check)` 退出码 0
- [ ] **AC-5**: 前端 build 通过
  - `(cd apps/stock-assistant/frontends/workbench && npm run build)` 退出码 0，无 error 输出
- [ ] **AC-6**: 节点测试全过
  - `(cd apps/stock-assistant/frontends/workbench && node --test --experimental-strip-types src/api/client.risk.test.ts)` 退出码 0
  - 用例数 ≥ 6
- [ ] **AC-7**: 不引入新 npm 依赖
  - `git diff main -- apps/stock-assistant/frontends/workbench/package.json apps/stock-assistant/frontends/workbench/package-lock.json` 输出为空
- [ ] **AC-8**: 不动后端
  - `git diff main -- apps/stock-assistant/backend/` 输出为空
- [ ] **AC-9**: 不动其它 frontend panel 文件（除挂载点）
  - `git diff main --name-only -- 'apps/stock-assistant/frontends/workbench/src/components/*Panel.tsx'` 仅列出 `RiskMetricsPanel.tsx`

---

## 测试集合

```bash
(cd apps/stock-assistant/frontends/workbench && npm run type-check)
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/workbench && node --test --experimental-strip-types src/api/client.risk.test.ts)
git diff main -- apps/stock-assistant/frontends/workbench/package.json
git diff main -- apps/stock-assistant/backend/
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/RiskMetricsPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/api/client.risk.test.ts`
- `docs/tasks/phaseF/risk-metrics-panel.md`

修改：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`（追加风控类型 + 函数，文件末尾）
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`（挂 RiskMetricsPanel）

不允许改：所有其它路径（含后端、其它 panel、package.json/lock）。

---

## 引用

- **设计来源**：plan §2 Top-5 #5；F.1 README
- **上游依赖**：F.1.4 risk-api-endpoints
- **下游依赖**：完成后即 Phase F.1 风控三件套全部 ship；下批 GEX/加密面板独立开
