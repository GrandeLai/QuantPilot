# Task phaseF2.form4-cluster: Form 4 集群信号引擎

**Phase**: Phase F.2
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py`。

### 核心逻辑

从 `Form4Transaction` 列表中，检测**集群买入信号**（内部人集体买入 → 历史超额 6-10%/180日）：

#### 过滤规则

1. 仅保留 `transaction_type == "P"` (Purchase)，排除行权/赠予/计划卖出
2. 排除 `is_10b5_1_plan == True`（预设计划单，预测性差）
3. 仅保留关键职位：`CEO|CFO|President|Chairman|Director|VP|EVP|SVP|COO|CTO|CLO`（正则匹配，不区分大小写）

#### 集群定义

- **窗口**：90 天滚动
- **人数阈值**：≥ 2 个不同 insider（按 `insider_name` 去重）
- **金额阈值**：单笔 ≥ $10,000（过滤噪音小额）

#### 输出

```python
@dataclass
class InsiderCluster:
    ticker: str
    window_start: date
    window_end: date
    insider_count: int                    # 涉及几位 insider
    total_value: float                    # 窗口内所有买入总金额
    avg_price: float                      # OI-加权平均买入价
    transactions: list[Form4Transaction]  # 原始明细
    signal_strength: float                # 0-1（人数/金额综合，见公式）
    key_roles: list[str]                  # 涉及职位列表（CEO/CFO 等）

def detect_clusters(
    transactions: list[Form4Transaction],
    *,
    window_days: int = 90,
    min_insiders: int = 2,
    min_single_value: float = 10_000.0,
) -> list[InsiderCluster]:
    """从 Form4Transaction 列表中检测集群买入信号."""
```

#### signal_strength 公式

```
role_bonus = 0.3 if CEO or CFO in key_roles else 0.0
count_score = min(1.0, (insider_count - 1) / 4)   # 1→0, 5+→1
value_score = min(1.0, log10(total_value / 10_000) / 3)  # $10k→0, $10M→1
signal_strength = 0.4 * count_score + 0.3 * value_score + 0.3 * role_bonus
```

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "InsiderCluster\|detect_clusters" apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py`

- [ ] **AC-3**: 10b5-1 过滤存在
  - `grep -q "10b5_1\|is_10b5_1" apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py`

- [ ] **AC-4**: 单元测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_form4_cluster.py -v)` 退出码 0
  - 至少 8 个测试（集群检测、10b5-1 过滤、单 insider 不算集群、90 日窗口边界、职位过滤、signal_strength 值域）

- [ ] **AC-5**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/form4_engine.py)` 退出码 0

---

## 文件影响范围

新建（本任务核心文件）：
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py`
- `apps/stock-assistant/backend/tests/test_form4_cluster.py`

依赖（由 F.2.1 edgar-fetcher 提供，批次共同提交）：
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py`（Form4Transaction 定义在此）
