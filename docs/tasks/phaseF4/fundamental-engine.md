# Task phaseF4.fundamental-engine: PEAD + Piotroski F-Score 引擎

**Phase**: Phase F.4
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/fundamental/` 模块：

### 数据模型

```python
@dataclass
class EarningsSurprise:
    ticker: str
    quarter: date          # 报告季度
    eps_actual: float
    eps_estimate: float
    eps_difference: float
    surprise_pct: float    # (actual - estimate) / abs(estimate)

@dataclass
class PEADSignal:
    ticker: str
    latest_surprise: EarningsSurprise
    surprise_magnitude: Literal["large_beat", "beat", "inline", "miss", "large_miss"]
    historical_drift_7d: float | None   # 历史同类 surprise 后 7 日平均超额（%）
    historical_drift_30d: float | None
    historical_drift_60d: float | None
    signal_strength: float   # 0-1，基于 surprise_pct 和历史 drift 置信度

@dataclass
class PiotroskiScore:
    ticker: str
    score: int               # 0-9
    grade: Literal["strong", "moderate", "weak"]
    signals: dict[str, bool]  # 9 个子信号的明细
    as_of_date: date
    interpretation: str      # 简短解读
```

### 关键函数

```python
def compute_pead_signal(
    ticker: str,
    *,
    lookback_quarters: int = 8,    # 用于计算历史漂移的历史季度数
    surprise_large_threshold: float = 0.05,   # ≥5% 为 large_beat
) -> PEADSignal | None:
    """获取最新 EPS surprise 并估算历史 PEAD 漂移."""

def compute_piotroski_fscore(
    ticker: str,
) -> PiotroskiScore | None:
    """计算 Piotroski F-Score（9 维财务健康评分）."""
```

### Piotroski 9 信号

**盈利能力（4 个）**
- F1: ROA > 0（净利润 / 总资产 > 0）
- F2: 经营现金流 > 0
- F3: Δ ROA > 0（本年 ROA > 去年 ROA）
- F4: 应计项目（CFO > Net Income，即现金质量好）

**杠杆/流动性（3 个）**
- F5: Δ 长期负债率 < 0（杠杆降低）
- F6: Δ 流动比率 > 0（流动性改善）
- F7: 未新增股份稀释（share count 未增加）

**运营效率（2 个）**
- F8: Δ 毛利率 > 0
- F9: Δ 资产周转率 > 0

---

## 验收标准

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/fundamental/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/fundamental/engine.py`

- [ ] **AC-2**: 关键符号存在
  - `grep -q "EarningsSurprise\|PEADSignal\|PiotroskiScore\|compute_pead_signal\|compute_piotroski_fscore" apps/stock-assistant/backend/src/quantpilot_stock/fundamental/engine.py`

- [ ] **AC-3**: Piotroski 9 信号覆盖
  - `grep -c "F[1-9]\|roa\|cash_flow\|leverage\|current_ratio\|shares\|gross_margin\|asset_turnover" apps/stock-assistant/backend/src/quantpilot_stock/fundamental/engine.py` 输出 ≥ 5

- [ ] **AC-4**: 单元测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_fundamental_engine.py -v)` 退出码 0
  - 至少 12 个测试

- [ ] **AC-5**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/fundamental/)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/fundamental/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/fundamental/engine.py`
- `apps/stock-assistant/backend/tests/test_fundamental_engine.py`

> **批次开发说明**：F.4.1–F.4.3 在同一工作树批量开发并统一提交。验收时须在 clean working tree 下执行。
