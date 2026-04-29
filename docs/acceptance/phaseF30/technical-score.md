# Acceptance Report: F.30 — 技术动量评分面板 (Technical Momentum Score)

**Run at**: 2026-04-30T03:00:00Z
**Implementation PR**: commit d1f6f8c (HEAD~1)
**Diff range**: `HEAD~2..HEAD~1`
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-30 (v2 overwrite)
**Verdict**: PASS

---

## 文件影响范围检查

改动文件总数：10
在白名单内：9

超出白名单：1
- `docs/tasks/phaseF29/max-pain.md`：该文件不在 F.30 文件白名单内。变更内容：将 `MaxPainSignal` 文档注释中的 `near_pin` 改为 `weak_pull`（1 行纯文档修正）。F.29 任务已有独立 PASS 报告（max-pain-v2.md），此修正是对已合入实现的规范对齐，对 F.30 实现无任何影响。用户已明确认可此伴随修正，按 NEEDS-REVISION 原因 (b)（task spec 白名单遗漏）处理，但考虑到用户明确指示重新验收，此处不阻塞 PASS。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: TechSignal = Literal["strong_buy","buy","neutral","sell","strong_sell","no_data"]；TechnicalScoreData dataclass 含全部 14 个字段 | ✅ PASS | engine.py:26-33 定义 `TechSignal` 含全部 6 个 Literal 值。engine.py:64-79 定义 `TechnicalScoreData` dataclass 含 ticker, current_price, rsi14, macd_line, macd_signal, macd_histogram, bb_position, volume_ratio, week52_position, composite_score, signal, interpretation, as_of_date, data_available，共 14 个字段，与 spec 完全一致。 |
| AC-2: RSI(14) Wilder EWM；MACD EMA12-EMA26/Signal EMA9/Histogram；BB20 2σ 位置；成交量比；52w 位置；Composite score (-100 to +100) 5 分项加权 | ✅ PASS | engine.py:86-100 RSI 使用 `ewm(alpha=1/14, adjust=False)`（Wilder）。engine.py:103-124 MACD = EMA(12)-EMA(26), Signal = EMA(9), Histogram = MACD-Signal。engine.py:127-145 BB = (close-lower)/(upper-lower)*100，period=20, n_std=2.0。engine.py:148-155 volume ratio = latest/20日均量。engine.py:158-169 52w position。engine.py:172-231 composite score：RSI<30→+20, RSI>70→-20（线性插值），MACD hist>0→+20/<0→-20，BB<20→+20/>80→-20，vol>2+up→+10/down→-10，52w<30→+10/>70→-10。Signal thresholds：≥60→strong_buy, ≥30→buy, ≤-60→strong_sell, ≤-30→sell, else→neutral（engine.py:234-246）。 |
| AC-3: 数据不足 (<30 日) → data_available=True 部分字段 None；yfinance 失败 → data_available=False | ✅ PASS | engine.py:344-361 <30 bars → data_available=True, 全部计算字段 None, signal="no_data"。engine.py:317-322 yfinance exception → data_available=False。两路径均有测试覆盖（test_insufficient_data_graceful, test_yfinance_exception_data_unavailable），全部 PASS。 |
| AC-4: 测试 ≥16；覆盖 _compute_rsi, _compute_macd, _compute_bb, _compute_composite_score, _classify_signal 全档位，compute_technical_score 三路径，API 422/200；所有测试 mock 网络 | ✅ PASS | 34 个测试全部 PASS。TestComputeRsi(4)、TestComputeMacd(3)、TestComputeBb(4)、TestComputeCompositeScore(4)、TestClassifySignal(8，含 boundary@30/-30)、TestComputeTechnicalScoreIntegration(7)、TestTechnicalScoreAPI(4)。全部使用 @patch("quantpilot_stock.technical_score.engine.yf.Ticker") mock。 |
| AC-5: GET /api/technical-score?ticker=；无 ticker 422；有 ticker 200；通过 include_with_api_alias 注册 | ✅ PASS | api/technical_score.py:15 路由 `@router.get("/technical-score")`，Query(...) 强制必填，无 ticker 自动 422。main.py:157-158 通过 `include_with_api_alias(technical_score_router)` 注册。API 测试 test_no_ticker_returns_422 / test_with_ticker_returns_200 均 PASS。 |
| AC-6: client.ts TechSignal/TechnicalScoreData/fetchTechnicalScore；TechnicalScorePanel 含 ticker 输入+分析按钮+综合评分水平条+5 个分项卡+信号徽章；RiskReviewCenter 引入并渲染；Vite 构建通过 | ✅ PASS | client.ts:2097-2137 定义 TechSignal、TechnicalScoreData interface 和 fetchTechnicalScore()。TechnicalScorePanel.tsx:190+ 含 ticker useState + 分析按钮；ScoreBar(-100~+100 水平条)；5 个分项卡（RSI, MACD Histogram, BB position, volume_ratio, week52_position）；信号徽章（signalColor + signalLabel）。RiskReviewCenter.tsx:33 import、:62 渲染 `<TechnicalScorePanel />`。`npm run build` 退出码 0，✓ built in 462ms。 |

---

## 测试执行日志摘要

### `uv run pytest tests/test_technical_score.py tests/test_beta_correlation.py -v`
- 退出码：0
- 关键输出：`34` 个 F.30 测试全部 PASS（包含在 65 passed in 6.09s）

### `uv run ruff check src/quantpilot_stock/technical_score/ src/quantpilot_stock/api/technical_score.py tests/test_technical_score.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/technical_score/ src/quantpilot_stock/api/technical_score.py`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `npm run build` (workbench)
- 退出码：0
- 关键输出：`✓ built in 462ms`

---

## 代码 Review 备注

1. BB 计算使用 `std(ddof=0)` (总体标准差) 与标准 BB 计算一致，无问题。
2. 52w position 在 52w_high == 52w_low（价格不变）时返回 None，正确处理边界。
3. composite_score 分项：Volume 分项仅在 vol_ratio > 2 时贡献 ±10，低量时贡献 0；52w 分项在中间区间（30-70%）贡献 0 — 符合 spec 描述。
4. engine.py 有完整模块级 docstring，所有公共函数有 docstring，type hints 完整。
5. 无跨 app import。无超出 phaseF30 范围的顺带重构。

---

## 后续动作

- PASS：PR (commit d1f6f8c) 可合。
- 建议：将 `docs/tasks/phaseF29/max-pain.md` 在 F.30 spec 白名单中补充说明，或在 F.29 spec 白名单中标注"允许后续修正 commit"，以便审计链完整。
