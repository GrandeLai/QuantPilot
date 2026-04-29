# Task phaseF3.execution-engine: TWAP/VWAP 分单引擎 + TCA

**Phase**: Phase F.3
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/execution/` 模块：

### 数据模型

```python
@dataclass
class ChildOrder:
    order_id: str
    parent_order_id: str
    ticker: str
    quantity: float
    scheduled_time: datetime
    algo: Literal["TWAP", "VWAP"]
    slice_index: int
    total_slices: int

@dataclass
class ExecutionReport:
    parent_order_id: str
    ticker: str
    total_quantity: float
    algo: Literal["TWAP", "VWAP"]
    child_orders: list[ChildOrder]
    estimated_avg_price: float | None   # 用于 TCA 对比
    created_at: datetime

@dataclass
class TCARecord:
    parent_order_id: str
    ticker: str
    algo: str
    arrival_price: float        # 下单时刻现价
    executed_avg_price: float   # 实际成交均价（手动录入）
    vwap_price: float | None    # 区间 VWAP（可选）
    close_price: float | None   # 收盘价
    slippage_bps: float         # (executed - arrival) / arrival * 10000
    total_quantity: float
    execution_date: date
```

### 关键函数

```python
def create_twap_slices(
    ticker: str,
    total_quantity: float,
    start_time: datetime,
    end_time: datetime,
    *,
    num_slices: int | None = None,          # None → 按 time_interval 切
    time_interval_minutes: int = 15,        # 每片间隔（分钟）
    parent_order_id: str | None = None,
) -> ExecutionReport:
    """生成 TWAP 子单列表（等量均分）."""

def create_vwap_slices(
    ticker: str,
    total_quantity: float,
    start_time: datetime,
    end_time: datetime,
    *,
    volume_profile: list[float] | None = None,  # 每时段 ADV 权重（None → 用均匀 fallback）
    num_slices: int = 10,
    parent_order_id: str | None = None,
) -> ExecutionReport:
    """生成 VWAP 子单列表（按 volume profile 加权切分）."""

def compute_tca(
    arrival_price: float,
    executed_avg_price: float,
    *,
    vwap_price: float | None = None,
    close_price: float | None = None,
    total_quantity: float = 1.0,
    ticker: str = "",
    parent_order_id: str = "",
    algo: str = "",
    execution_date: date | None = None,
) -> TCARecord:
    """计算交易成本分析（滑点 bps）."""

def adv_check(
    total_quantity: float,
    avg_daily_volume: float,
    *,
    threshold_pct: float = 0.005,   # 默认 ADV 0.5%
) -> bool:
    """判断订单量是否超过 ADV 阈值（需要分单）."""
```

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/execution/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/execution/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "ChildOrder\|ExecutionReport\|TCARecord\|create_twap_slices\|create_vwap_slices\|compute_tca" apps/stock-assistant/backend/src/quantpilot_stock/execution/engine.py`

- [ ] **AC-3**: TWAP 等量切分
  - `grep -q "TWAP\|twap\|time_interval" apps/stock-assistant/backend/src/quantpilot_stock/execution/engine.py`

- [ ] **AC-4**: TCA 滑点计算
  - `grep -q "slippage_bps\|arrival_price\|10000" apps/stock-assistant/backend/src/quantpilot_stock/execution/engine.py`

- [ ] **AC-5**: 单元测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_execution_engine.py -v)` 退出码 0
  - 至少 10 个测试（TWAP 切分、VWAP 权重、TCA 计算、ADV 检查、边界情况）

- [ ] **AC-6**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/execution/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/execution/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/execution/engine.py`
- `apps/stock-assistant/backend/tests/test_execution_engine.py`
