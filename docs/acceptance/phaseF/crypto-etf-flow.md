# Acceptance Report: phaseF.crypto-etf-flow

**Run at**: 2026-04-28T00:00:00Z
**Implementation commit**: `35272d4`
**Diff range**: `35272d4^..35272d4`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：5
- 在白名单内：5
- 超出白名单：0

明细：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py` — 白名单（修改）
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/etf_flow.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/models.py` — 白名单（修改）
- `apps/stock-assistant/backend/tests/test_crypto_derivs_etf_flow.py` — 白名单（新建）
- `docs/tasks/phaseF/crypto-etf-flow.md` — 白名单（本 spec）

`pyproject.toml` 未出现在 diff 中，满足"不允许改"约束。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 两个文件存在 | PASS | `test -f etf_flow.py` 和 `test -f test_crypto_derivs_etf_flow.py` 均返回 0 |
| AC-2: 顶层 import 正常 | PASS | `uv run python -c "from quantpilot_stock.crypto_derivs import ETFFlowSnapshot, aggregate_daily_flows, flow_zscore, flow_extreme_signal, flow_aum_velocity, BTC_SPOT_ETF_TICKERS, ETH_SPOT_ETF_TICKERS"` 退出码 0 |
| AC-3: 单测全过，数量 ≥ 12 | PASS | 20 collected, 20 passed in 0.28s，退出码 0；远超 ≥ 12 下限 |
| AC-4: ruff 干净 | PASS | `All checks passed!`，退出码 0 |
| AC-5: mypy 干净 | PASS | `Success: no issues found in 5 source files`，退出码 0 |
| AC-6: pyproject.toml 未改 | PASS | `git diff main -- .../pyproject.toml` 无输出，退出码 0 |
| AC-7: 现有测试无回归 | PASS | 283 passed in 9.09s，退出码 0（--ignore=test_crypto_derivs_etf_flow.py） |
| AC-8: 之前任务的导出未破坏 | PASS | `from quantpilot_stock.crypto_derivs import compute_basis, fetch_aggregated_derivs, FundingRate` 退出码 0 |

## 测试执行日志摘要

### 1. 单测全过（AC-3）
```
pytest tests/test_crypto_derivs_etf_flow.py -v
20 collected, 20 passed in 0.28s
EXIT: 0
```

### 2. ruff（AC-4）
```
uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_etf_flow.py
All checks passed!
EXIT: 0
```

### 3. mypy（AC-5）
```
uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports
Success: no issues found in 5 source files
EXIT: 0
```

### 4. 顶层 import 烟雾测试（AC-2）
```
uv run python -c "from quantpilot_stock.crypto_derivs import ETFFlowSnapshot, aggregate_daily_flows, flow_zscore, flow_extreme_signal, flow_aum_velocity, BTC_SPOT_ETF_TICKERS, ETH_SPOT_ETF_TICKERS"
EXIT: 0
```

### 5. 合并 import 测试（AC-2 + AC-8）
```
uv run python -c "from quantpilot_stock.crypto_derivs import ETFFlowSnapshot, aggregate_daily_flows, flow_zscore, flow_extreme_signal, flow_aum_velocity, BTC_SPOT_ETF_TICKERS, ETH_SPOT_ETF_TICKERS, compute_basis, fetch_aggregated_derivs; print('ok')"
ok
EXIT: 0
```

### 6. 现有测试无回归（AC-7）
```
pytest tests/ -x --ignore=tests/test_crypto_derivs_etf_flow.py -q
283 passed in 9.09s
EXIT: 0
```

### 7. pyproject.toml 未改（AC-6）
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

### 8. 之前导出（AC-8）
```
uv run python -c "from quantpilot_stock.crypto_derivs import compute_basis, fetch_aggregated_derivs, FundingRate"
EXIT: 0
```

## 代码 Review 备注

1. `etf_flow.py` 有模块级 docstring，`models.py` 追加的 `ETFFlowSnapshot` 有内联 Field 描述；测试文件有模块级 docstring——均符合 CLAUDE.md Python 规范。
2. 所有公共函数带完整 type hints（`list[ETFFlowSnapshot]`、`dict[str, float]`、`list[float]`、`dict[str, float | str]`、`float`），满足项目规范。
3. 无跨 app import：`etf_flow.py` 仅 import `numpy`（已有依赖）和同包 `models`；`__init__.py` 仅 re-export 同包符号；`common/` 未被反向 import。
4. `aggregate_daily_flows` 的大小写不敏感过滤（`.upper()` 双向规范化）与 spec 约定一致。
5. `flow_zscore` 与 `flow_extreme_signal` 的参数验证（`window < 5`、`arr.size < window`、`arr.size < 30`、`z_threshold <= 0`）使用明确的 `ValueError`，与同包 funding 系列函数风格一致。
6. `flow_aum_velocity` 在 `total_aum_usd <= 0` 时正确抛 `ValueError`，而非返回 inf/nan。
7. `BTC_SPOT_ETF_TICKERS` 和 `ETH_SPOT_ETF_TICKERS` 均为 `tuple[str, ...]`，集合不重叠（`test_no_overlap_between_btc_and_eth` 验证）。
8. 测试覆盖 4 个功能域：constants × 3、aggregate_daily_flows × 4、flow_zscore × 5、flow_extreme_signal × 5、flow_aum_velocity × 3 = 共 20 用例，远超 spec 要求的 ≥ 12。
9. 未引入任何新依赖（`numpy` 已是项目已有依赖），满足 AC-6 / spec 约束。
10. 实现严格限定在 `quantpilot_stock.crypto_derivs` 子包，无顺带重构，无外部数据抓取，与 spec "不做什么" 完全对齐。

## 后续动作

PASS — PR 可合。本任务为 F.1.12 ETF flow 分析层，下游 F.1.13（前端面板统一接入）可直接消费本包；外部 provider 抓取留待 F.2 或 paid-tier 升级时独立任务处理。
