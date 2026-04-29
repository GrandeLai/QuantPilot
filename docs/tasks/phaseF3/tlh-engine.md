# Task phaseF3.tlh-engine: 税务亏损收割引擎

**Phase**: Phase F.3
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/tlh/` 模块：

### 数据模型

```python
@dataclass
class TaxLot:
    ticker: str
    quantity: float          # 持仓数量（股）
    cost_basis: float        # 每股成本（$）
    acquisition_date: date   # 买入日期
    lot_id: str              # 唯一 ID（broker 端）

@dataclass
class TLHCandidate:
    lot: TaxLot
    current_price: float
    unrealized_pnl: float         # current_price × qty - cost_basis × qty
    unrealized_pnl_pct: float     # unrealized_pnl / (cost_basis × qty)
    holding_days: int
    is_long_term: bool            # holding_days >= 365
    replacement_tickers: list[str]  # 推荐替代 ETF
    wash_sale_risk: bool          # True → 近 30 天内有同票买入记录

@dataclass
class WashSaleWarning:
    ticker: str
    last_purchase_date: date
    days_since_purchase: int      # 如果 < 30 → wash sale 风险
```

### ETF 替代表（硬编码）

```python
_REPLACEMENT_MAP = {
    "SPY":  ["VOO", "IVV", "SPLG"],
    "VOO":  ["SPY", "IVV", "SPLG"],
    "IVV":  ["SPY", "VOO", "SPLG"],
    "QQQ":  ["QQQM", "ONEQ"],
    "QQQM": ["QQQ", "ONEQ"],
    "IWM":  ["VTWO", "SCHA"],
    "VTWO": ["IWM", "SCHA"],
    "VTI":  ["ITOT", "SCHB"],
    "ITOT": ["VTI", "SCHB"],
    "AGG":  ["BND", "SCHZ"],
    "BND":  ["AGG", "SCHZ"],
    # 个股 → 对应行业 ETF（保守推荐，相关性高但非 substantially identical）
    "AAPL": ["XLK", "VGT"],
    "MSFT": ["XLK", "VGT"],
    "NVDA": ["SOXX", "SMH"],
    "TSLA": ["XLY", "CARZ"],
    "META": ["XLC", "SNAP"],  # SNAP 仅示例，用户自行确认
    "GOOGL":["XLC", "IYC"],
    "AMZN": ["XLY", "IBUY"],
}
```

### 关键函数

```python
def scan_tlh_candidates(
    lots: list[TaxLot],
    current_prices: dict[str, float],
    recent_purchases: dict[str, date],  # ticker → 最近买入日期（wash sale 检查）
    *,
    min_loss_pct: float = -0.05,   # 只推荐跌幅 >= 5% 的
    min_loss_usd: float = 500.0,   # 只推荐亏损 >= $500 的
) -> list[TLHCandidate]:

def estimate_tax_saving(
    candidates: list[TLHCandidate],
    *,
    short_term_rate: float = 0.37,   # 短期税率（用户可调）
    long_term_rate: float = 0.20,    # 长期税率
) -> float:
    """估算通过 harvest 这些亏损可节约的税额（$）."""
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/tlh/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/tlh/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "TaxLot\|TLHCandidate\|scan_tlh_candidates\|estimate_tax_saving" apps/stock-assistant/backend/src/quantpilot_stock/tlh/engine.py`

- [ ] **AC-3**: Wash sale 逻辑
  - `grep -q "wash_sale\|30\|days" apps/stock-assistant/backend/src/quantpilot_stock/tlh/engine.py`

- [ ] **AC-4**: ETF 替代表
  - `grep -q "REPLACEMENT_MAP\|replacement_tickers\|VOO\|QQQM" apps/stock-assistant/backend/src/quantpilot_stock/tlh/engine.py`

- [ ] **AC-5**: 单元测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_tlh_engine.py -v)` 退出码 0
  - 至少 10 个测试（候选扫描、wash sale 过滤、最小亏损过滤、税额估算、替代 ETF 查询）

- [ ] **AC-6**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/tlh/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/tlh/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/tlh/engine.py`
- `apps/stock-assistant/backend/tests/test_tlh_engine.py`

> **批次开发说明**：F.3.1–F.3.5 在同一工作树批量开发并统一提交。验收时须在 clean working tree（`git diff HEAD` 为空）下执行。
