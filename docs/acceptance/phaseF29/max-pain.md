# Acceptance Report: F.29 — 期权最大痛苦值面板 (Max Pain Calculator)

**Run at**: 2026-04-30T00:00:00Z
**Implementation PR**: commit d7545e6 (feat(F.29): options max pain calculator with pin zone, directional pull signals)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-30
**Verdict**: FAIL

---

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

所有改动文件均在 task spec 白名单内：
- `apps/stock-assistant/backend/src/quantpilot_stock/max_pain/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/max_pain/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/max_pain.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_max_pain.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/MaxPainPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF29/max-pain.md`

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: MaxPainSignal enum + ExpiryMaxPain + MaxPainData dataclasses | ❌ FAIL | Task spec AC-1 定义的 `MaxPainSignal = Literal["pin_zone","near_pin","bullish_pull","bearish_pull","unknown"]`，但实现使用 `"weak_pull"` 而非 `"near_pin"`（engine.py:30-36, client.ts:1998-2003）。ExpiryMaxPain 和 MaxPainData 字段完整，符合要求。 |
| AC-2: 计算逻辑（Max Pain strike、distance_pct、信号分类） | ❌ FAIL | Task spec AC-2 明确：`\|distance\| >= 5% → near_pin`。实现返回 `"weak_pull"`（engine.py:150）。distance_pct 公式正确；pin_zone/bullish_pull/bearish_pull 阈值正确（<2%, 2-5%）。唯独 >=5% 的信号名与 spec 不符。 |
| AC-3: 降级策略（无数据 data_available=True; yfinance 失败 data_available=False） | ✅ PASS | `test_no_options_returns_empty_expiries`（data_available=True, expiries=[]）通过；`test_yfinance_exception_data_unavailable`（data_available=False）通过；engine.py:222-232 及 :204-209 实现正确。 |
| AC-4: ≥16 tests，全 mocked | ✅ PASS | 28 tests collected，28 passed。所有网络调用通过 `@patch("quantpilot_stock.max_pain.engine.yf.Ticker")` mock。覆盖 _compute_max_pain / _classify_signal 所有分支 / DTE 过滤 / API 端点。 |
| AC-5: GET /api/max-pain?ticker=，无 ticker 422，有 ticker 200，include_with_api_alias 注册 | ✅ PASS | `test_no_ticker_returns_422` 通过；`test_with_ticker_returns_200` 通过；main.py:155-156 通过 `include_with_api_alias(max_pain_router)` 注册。 |
| AC-6: client.ts 类型 + MaxPainPanel.tsx + RiskReviewCenter 渲染 + TypeScript/Vite 通过 | ✅ PASS | client.ts 定义 MaxPainSignal/ExpiryMaxPain/MaxPainData/fetchMaxPain（行 1998-2039）；MaxPainPanel.tsx 含 ticker 输入框、分析按钮、ExpiryRow（DTE/MaxPain/距离/信号）、PriceVsMaxPainBar 可视化、信号徽章（pin_zone 金色/bullish_pull 绿/bearish_pull 红）；RiskReviewCenter.tsx:32,59 引入并渲染 `<MaxPainPanel />`；Vite build 退出码 0，tsc -b 通过（2996 modules transformed）。 |

---

## 测试执行日志摘要

### `uv run pytest tests/test_max_pain.py -v`
- 退出码：0
- 关键输出：28 passed in 5.96s
- 所有 28 个测试通过，含 `TestComputeMaxPain`（5）、`TestClassifySignal`（8）、`TestGetDte`（3）、`TestComputeMaxPainIntegration`（8）、`TestMaxPainAPI`（4）

### `uv run ruff check src/quantpilot_stock/max_pain/ src/quantpilot_stock/api/max_pain.py tests/test_max_pain.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/max_pain/ src/quantpilot_stock/api/max_pain.py`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `npm run build` (workbench)
- 退出码：0
- 关键输出：`tsc -b && vite build`；2996 modules transformed；built in 407ms

---

## 代码 Review 备注

1. **模块级 docstring**：engine.py 有完整模块 docstring；api/max_pain.py 有模块 docstring；`__init__.py` 为空（单行包标识），符合惯例。
2. **Type hints**：全文件使用 type hints，Pydantic/dataclass 结合正确，mypy clean。
3. **跨 app import**：无违规，仅 quantpilot_stock 内部 import。
4. **`common/` 反向 import**：无。
5. **AC-4 测试 note**：Task spec 要求覆盖 `_classify_signal` 所有档位包括 `near_pin`，但因实现使用 `weak_pull`，测试断言的是 `"weak_pull"`（通过，但与 spec enum 不一致）。

---

## 后续动作

**FAIL 原因（需 implementation agent 修复）**：

1. **AC-1 / AC-2 信号枚举名不符**：
   - Task spec 要求：`MaxPainSignal` 含 `"near_pin"`，`|distance| >= 5%` → `"near_pin"`
   - 实现使用：`"weak_pull"`（engine.py:34,150；client.ts:2002；MaxPainPanel.tsx:30,38）
   - 修复方案 A（推荐）：将 `"weak_pull"` 全部改为 `"near_pin"`，相应更新 engine.py、client.ts、MaxPainPanel.tsx、tests/test_max_pain.py
   - 修复方案 B：如用户认为 `"weak_pull"` 比 `"near_pin"` 语义更准确，则先修 task spec AC-1/AC-2，再重验（NEEDS-REVISION 路径）

**注意**：除信号名不一致外，其余实现质量良好——计算逻辑正确、测试充分（28 tests）、lint/mypy/build 全绿。修复仅需机械替换信号名字符串。
