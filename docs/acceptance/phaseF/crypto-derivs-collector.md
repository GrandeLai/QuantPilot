# Acceptance Report: phaseF.crypto-derivs-collector

**Run at**: 2026-04-29T00:00:00Z
**Implementation commit**: `d017d06`
**Diff range**: `d017d06^..d017d06`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：5
- 在白名单内：5
- 超出白名单：0

明细：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/models.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/collector.py` — 白名单（新建）
- `apps/stock-assistant/backend/tests/test_crypto_derivs_collector.py` — 白名单（新建）
- `docs/tasks/phaseF/crypto-derivs-collector.md` — 白名单（本 spec）

`pyproject.toml` 未出现在 diff 中，满足"不允许改"约束。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 四个文件存在 | PASS | `__init__.py`、`models.py`、`collector.py`、`test_crypto_derivs_collector.py` 均在 diff 中新建，`test -f` 全部返回 0 |
| AC-2: import 烟雾测试 | PASS | `uv run python -c "from quantpilot_stock.crypto_derivs import ..."` 输出 `ok`，退出码 0 |
| AC-3: 单测全过，数量 ≥ 12 | PASS | 12 collected, 12 passed in 0.25s，退出码 0；恰好满足 ≥ 12 下限 |
| AC-4: ruff 干净 | PASS | `All checks passed!`，退出码 0 |
| AC-5: mypy 干净 | PASS | `Success: no issues found in 3 source files`，退出码 0 |
| AC-6: pyproject.toml 未改 | PASS | `git diff main -- .../pyproject.toml` 无输出，退出码 0 |
| AC-7: 现有测试无回归 | PASS | 252 passed in 9.11s，退出码 0（--ignore=test_crypto_derivs_collector.py） |
| AC-8: 不动其它 app | PASS | `git diff main --name-only -- apps/quant-assistant/ common/ tools/` 无输出 |
| AC-9: 测试不真正发起网络请求 | PASS | `grep -c "MockTransport\|mock_transport"` 返回 4，确认使用 mock |

## 测试执行日志摘要

### 1. 单测全过（AC-3）
```
pytest tests/test_crypto_derivs_collector.py -v
12 collected, 12 passed in 0.25s
EXIT: 0
```

### 2. ruff（AC-4）
```
uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_collector.py
All checks passed!
EXIT: 0
```

### 3. mypy（AC-5）
```
uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports
Success: no issues found in 3 source files
EXIT: 0
```

### 4. import 烟雾测试（AC-2）
```
uv run python -c "from quantpilot_stock.crypto_derivs import fetch_binance_funding, fetch_binance_open_interest, fetch_okx_funding, fetch_okx_open_interest, fetch_aggregated_derivs, FundingRate, OpenInterest; print('ok')"
ok
EXIT: 0
```

### 5. 现有测试无回归（AC-7）
```
pytest tests/ -x --ignore=tests/test_crypto_derivs_collector.py -q
252 passed in 9.11s
EXIT: 0
```

### 6. pyproject.toml 未改（AC-6）
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

## 代码 Review 备注

1. 三个新文件均有模块级 docstring，符合 CLAUDE.md Python 规范。
2. 所有公共函数均带完整 type hints（`str`、`int`、`httpx.AsyncClient | None`、`FundingRate`、`OpenInterest`、`list[FundingRate]`、`dict[str, Any]`），满足项目规范。
3. 无跨 app import：`collector.py` 仅 import `httpx`（已有依赖）和同包 `models`；`__init__.py` 仅 re-export 同包符号。
4. `AsyncExitStack` 模式优雅处理"复用 client 时不关闭，自建时自动关闭"语义，符合 spec "client 参数允许复用同一个 AsyncClient" 约定。
5. `fetch_aggregated_derivs` 正确使用 `asyncio.gather(..., return_exceptions=True)` 并将异常收入 `errors` dict，符合 spec 约定。
6. OKX API 200 OK 但 `code != "0"` 的业务错误被正确识别并 raise `httpx.HTTPStatusError`，Binance 则直接依赖 `raise_for_status()`。
7. 测试文件覆盖：Binance happy path × 3（funding, OI, history）+ 4xx error + lowercase 标准化；OKX happy path × 3 + business error × 2；聚合 all-succeed + partial-failure = 共 12 用例，满足 spec 每类场景要求。
8. 测试全程使用 `httpx.MockTransport` / `monkeypatch`，零网络请求，满足 AC-9。
9. 没有引入任何新依赖（`httpx` 已在项目中），满足"不引入新依赖"约束。
10. 实现严格限定在 `quantpilot_stock.crypto_derivs` 子包内，无"顺带重构"。

## 后续动作

PASS — PR 可合。本任务为 F.1 collector 层基础，下游任务 F.1.11（basis 计算）和 F.1.13（前端面板）可直接消费本包。
