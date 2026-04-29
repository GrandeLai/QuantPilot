# Task phaseF2.sec-events-panel: SEC 事件流前端面板

**Phase**: Phase F.2
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`，集成到 `RiskReviewCenter.tsx`（GEXPanel 下方）。

### UI 结构

```
[ Ticker 输入 ] [ 查询 ]

─── 最新 8-K 变化 ──────────────────────────────────────
[ 日期 ] [ Item 5.02 - Director Changes ]  [change_score: 0.72]
  • ＋ 新增段落（绿色高亮）
  • ✎ 修改段落（黄色高亮）
  • － 删除段落（红色高亮）

─── 内部人集群买入 ────────────────────────────────────
Signal: 0.72 ████████░░  
3 insiders (CEO + CFO + Director) bought $2.5M in 90 days
[ 明细展开 ]

─── 交易解读 ─────────────────────────────────────────
• 8-K material change + insider cluster → 双重看涨信号
• 无信号时显示"暂无事件信号，正常持仓"
```

### 组件实现要求

- 调用 `GET /api/sec/summary?ticker=...`
- 8-K diff 段落：按 `diff_type` 着色（added→绿/removed→红/modified→黄）
- insider cluster：`signal_strength` 进度条（0-1）
- 加载/错误状态处理
- dark-theme tokens：`#0E1014`、`#151619`、`#00C087`

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`

- [ ] **AC-2**: API 调用存在
  - `grep -q "sec/summary\|fetchSECSummary" apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`

- [ ] **AC-3**: 集成进 RiskReviewCenter
  - `grep -q "SECEventsPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

- [ ] **AC-4**: dark-theme tokens
  - `grep -q "#0E1014\|#151619\|#00C087" apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`

- [ ] **AC-5**: 差分着色（added/removed/modified 颜色类）
  - `grep -q "added\|removed\|modified" apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`

- [ ] **AC-6**: type-check + build 通过
  - `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run type-check)` 退出码 0
  - `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run build)` 退出码 0

---

## 文件影响范围

新建（本任务核心文件）：
- `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`（新增 SEC 类型和 fetchSECSummary）

依赖（由 F.2.1–F.2.4 提供，批次共同提交）：
- `edgar/` 模块所有文件（F.2.1–F.2.3）
- `api/sec.py`、`main.py`（F.2.4）
- `pyproject.toml`（rapidfuzz）
