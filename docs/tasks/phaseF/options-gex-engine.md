# Task phaseF.options-gex-engine: GEX / VEX 计算引擎

**Phase**: Phase F.1  
**Status**: pending  
**Created**: 2026-04-29

---

## 范围

### 背景

GEX（Gamma Exposure）= 做市商（Dealer）净 Gamma 敞口，单位：dollar-gamma。
公式：`GEX_per_strike = (call_OI - put_OI) × BSM_gamma × 100 × S²`
- Positive GEX → Dealer 净 long gamma → 价格被钉（mean-reversion）
- Negative GEX → Dealer 净 short gamma → 价格加速（trending）

关键衍生指标：
- **Gamma Flip Level**：距当前价最近的 GEX 从正转负的行权价
- **Major Magnet**：`|GEX|` 最大的行权价（Dealer 会 delta-hedge，该价格有吸附力）
- **Net GEX Total**：所有行权价的 GEX 求和

### 做什么

新建 `apps/stock-assistant/backend/src/quantpilot_stock/options/gex_engine.py`：

```python
@dataclass
class GEXByStrike:
    strike: float
    call_oi: int
    put_oi: int
    call_gex: float     # call_OI × gamma × 100 × S²
    put_gex: float      # put_OI × gamma × 100 × S²
    net_gex: float      # call_gex - put_gex
    gamma: float        # BSM gamma (call = put for same strike)

@dataclass
class GEXSnapshot:
    ticker: str
    spot: float
    snapshot_time: str          # ISO
    gex_by_strike: list[GEXByStrike]
    net_gex_total: float
    gamma_flip_level: float | None
    major_magnet: float | None
    high_vol_trigger: float | None   # highest strike below spot where net_gex < 0

def compute_gex_snapshot(
    ticker: str,
    spot: float,
    chain: list[OptionsContract],
    *,
    r: float = 0.05,
) -> GEXSnapshot:
    ...
```

BSM gamma 来自已有的 `quantpilot_stock.options.greeks.BlackScholes`。

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/options/gex_engine.py`
- [ ] **AC-2**: 关键函数/类存在
  - `grep -q "GEXSnapshot\|GEXByStrike\|compute_gex_snapshot" apps/stock-assistant/backend/src/quantpilot_stock/options/gex_engine.py`
- [ ] **AC-3**: gamma_flip_level 字段存在
  - `grep -q "gamma_flip_level\|major_magnet" apps/stock-assistant/backend/src/quantpilot_stock/options/gex_engine.py`
- [ ] **AC-4**: 测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --group dev pytest tests/test_options_gex_engine.py -v)` 退出码 0
- [ ] **AC-5**: mypy clean

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/options/gex_engine.py`
- `apps/stock-assistant/backend/tests/test_options_gex_engine.py`
