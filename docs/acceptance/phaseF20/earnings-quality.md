# Acceptance Report: F.20 — 盈利质量三件套 (Earnings Quality Scoring)

**Run at**: 2026-04-30T00:00:00+08:00
**Implementation PR**: commit 402a2f2
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-30
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

全部改动文件均在 task spec 白名单内：

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/backend/src/quantpilot_stock/earnings_quality/__init__.py` | ✅ |
| `apps/stock-assistant/backend/src/quantpilot_stock/earnings_quality/engine.py` | ✅ |
| `apps/stock-assistant/backend/src/quantpilot_stock/api/earnings_quality.py` | ✅ |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | ✅ |
| `apps/stock-assistant/backend/tests/test_earnings_quality.py` | ✅ |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | ✅ |
| `apps/stock-assistant/frontends/workbench/src/components/EarningsQualityPanel.tsx` | ✅ |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | ✅ |
| `docs/tasks/phaseF20/earnings-quality.md` | ✅ |

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 数据模型（EarningsQualityGrade/FScoreGrade/AccrualQuality/EarningsQualityData） | ✅ PASS | `engine.py` L30-52：三个 Literal 类型均正确定义；`EarningsQualityData` dataclass 包含 spec 要求的全部12个字段（ticker/f_score/f_score_grade/f_score_components/m_score/manipulation_risk/accrual_ratio/accrual_quality/quality_grade/interpretation/as_of_date/data_available） |
| AC-2: Piotroski F-Score 9 分项计算 + 等级映射 | ✅ PASS | `engine.py` L84-180 实现9项：Profitability 4项(ROA>0/CFO>0/ΔROA>0/CFO/Assets>NI/Assets)、Leverage 3项(ΔLeverage↓/ΔCurrentRatio↑/NoNewShares)、Efficiency 2项(ΔGrossMargin↑/ΔAssetTurnover↑)；等级：≥8=very_strong/≥6=strong/≥3=average/else=weak；测试 `test_all_pass_gives_9` / `test_grade_weak_for_score_below_3` 均 PASS |
| AC-3: Beneish M-Score 8因子 + 阈值 -2.22 | ✅ PASS | `engine.py` L187-296：DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA 8因子，截距 -4.84，系数与 Beneish 1999 对齐；`manipulation_risk = m_score > -2.22`；测试 `test_manipulation_flag_when_m_above_threshold` PASS |
| AC-4: Sloan 应计比率公式 + 三档质量 | ✅ PASS | `engine.py` L303-330：`(NI - CFO) / AvgTotalAssets`；\|ratio\| ≤ 5% = high；5%-10% = medium；> 10% = low（负值也触发 low）；测试 high/medium/low/missing 4个分支全 PASS |
| AC-5: 测试总数 ≥ 16（实际 44），覆盖全部指定场景 | ✅ PASS | `uv run pytest tests/test_earnings_quality.py -v` 输出 `44 passed in 6.79s`；覆盖：_safe_get(6)、F-Score(8)、M-Score(4)、Accrual(4)、OverallGrade(6)、ComputeEarningsQuality(6)、GracefulDegradation(6)、API(4)；全部 mock yfinance，无真实网络请求 |
| AC-6: API GET /api/earnings-quality + 注册 | ✅ PASS | `api/earnings_quality.py` L37：`GET /` with `ticker: str = Query(...)`（无ticker=422）；`main.py` L137-138: `include_with_api_alias(earnings_quality_router)`；API测试 `test_missing_ticker_returns_422` 和 `test_always_200_even_when_degraded` 均 PASS |
| AC-7: 前端组件（client.ts类型/EarningsQualityPanel/RiskReviewCenter引入） | ✅ PASS | `client.ts` L1630-1669：三类型+接口+fetchEarningsQuality 函数均正确定义；`EarningsQualityPanel.tsx` 实现综合评级badge/F-Score条形图+9分项列表/M-Score指示器(含-2.22阈值)/Sloan应计比率+等级/降级banner；`RiskReviewCenter.tsx` L23/41 import + 渲染 `<EarningsQualityPanel />`；Vite生产构建成功 `✓ built in 602ms` |

---

## 测试执行日志摘要

### `uv run pytest tests/test_earnings_quality.py -v`
- 退出码：0
- 关键输出：
  ```
  collected 44 items
  ...（44条 PASSED）...
  44 passed in 6.79s
  ```

### `uv run ruff check src/quantpilot_stock/earnings_quality/ src/quantpilot_stock/api/earnings_quality.py tests/test_earnings_quality.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/earnings_quality/ src/quantpilot_stock/api/earnings_quality.py`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `npm run build --workspace=apps/stock-assistant/frontends/workbench`
- 退出码：0
- 关键输出：`✓ built in 602ms`（无 TypeScript 报错，无警告）

---

## 代码 Review 备注

1. **`__init__.py` 仅导出部分类型**：`FScoreGrade` 和 `AccrualQuality` 未在 `__init__.py` 中 re-export，但 `api/earnings_quality.py` 直接从 `engine` 导入，无问题。如果将来其他模块需要这两个类型，建议补全 `__all__`。属于建议项，不阻塞 PASS。

2. **M-Score 最少非默认指标阈值为 3**（`engine.py` L292）：原始论文没有明确规定，实现选择 3/8 作为最低可用性门槛，属于合理工程决策。

3. **F-Score 等级边界**：spec 说 8-9=very_strong，实现写 `score >= 8`，正确。spec 说 0-2=weak，实现写 `else`（score < 3），正确。

4. **`engine.py` 模块级 docstring** 存在（L1-15），符合 CLAUDE.md 要求。

5. 无跨 app import，无反向 import common，无 scope creep。

---

## 后续动作

- PASS：PR 可合并，无前置依赖。
- 建议在 `docs/acceptance/INDEX.md` 中新增本条记录。
