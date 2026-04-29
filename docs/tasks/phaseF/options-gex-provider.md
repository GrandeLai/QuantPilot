# Task phaseF.options-gex-provider: 期权链 Provider（yfinance MVP）

**Phase**: Phase F.1  
**Status**: pending  
**Created**: 2026-04-29  
**Owner-agent**: implementation-agent  
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

GEX 计算需要"期权链"数据：每个行权价 × 到期日 的 OI（持仓量）+ IV（隐含波动率）。使用 yfinance（已是 quantpilot-common 依赖）作为免费无需 API key 的 MVP 数据源。

### 做什么

新建 `apps/stock-assistant/backend/src/quantpilot_stock/options/chain_provider.py`：

#### 数据模型

```python
@dataclass
class OptionsContract:
    ticker: str
    expiry: date          # YYYY-MM-DD
    strike: float
    option_type: Literal["call", "put"]
    open_interest: int
    implied_volatility: float    # annualised, e.g. 0.20
    last_price: float
    bid: float
    ask: float
    volume: int
    dte: int              # days to expiry from today
```

#### 接口

```python
def fetch_chain_yfinance(
    ticker: str,
    *,
    max_dte: int = 45,
    min_oi: int = 0,
) -> list[OptionsContract]:
    ...
```

- 拉取 yfinance `ticker.options`（到期日列表）
- 筛选 DTE ≤ max_dte 的到期日（通常 2-4 个到期）
- 对每个到期日拉取 `ticker.option_chain(date)`，分别处理 `.calls` / `.puts`
- 过滤 `openInterest >= min_oi` 且 `impliedVolatility > 0`
- 返回合并后的 `list[OptionsContract]`

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/options/chain_provider.py`
- [ ] **AC-2**: `OptionsContract` 含关键字段
  - `grep -q "open_interest\|implied_volatility\|dte" apps/stock-assistant/backend/src/quantpilot_stock/options/chain_provider.py`
- [ ] **AC-3**: `fetch_chain_yfinance` 函数存在
  - `grep -q "def fetch_chain_yfinance" apps/stock-assistant/backend/src/quantpilot_stock/options/chain_provider.py`
- [ ] **AC-4**: 测试通过（mock yfinance）
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --group dev pytest tests/test_options_chain_provider.py -v)` 退出码 0
- [ ] **AC-5**: mypy clean
  - `uv run --isolated --with mypy python -m mypy src/` in backend dir

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/options/chain_provider.py`
- `apps/stock-assistant/backend/tests/test_options_chain_provider.py`
