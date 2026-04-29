# Task phaseF.crypto-etf-flow: 加密 ETF 净流入分析引擎

**Phase**: Phase F.1（加密衍生品面板之 3）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景与设计取舍

Brainstorm Top-5 #2 提到现货 ETF flow（IBIT/FBTC/ARKB/BITB 等）作为机构资金 vs 加密原生资金的指示器。**问题**：免费数据源全部是 HTML scrape（Farside Investors / CoinGlass HTML / BlackRock 官网），ToS 风险高、解析脆弱；paid API（Coinglass Pro / Bloomberg）单独开账号成本另算。

**本次决策**：**只做分析层 + 数据模型 + 手动注入接口**，把外部抓取留作单独的"数据 provider"任务（F.2 或 paid-tier 升级时做）。这样：
- 本任务零网络依赖、纯数学，跟 F.1.11 同一模式
- 后续接 Farside/CoinGlass/Bloomberg 任意一个 provider 都能直接喂给本层
- 用户也可手动从 Farside 网页粘贴 CSV 数据（前端文本输入）跑分析

### 做什么

新增模块 `quantpilot_stock.crypto_derivs.etf_flow`：

#### 1. 数据模型（追加到 `models.py`）

```python
class ETFFlowSnapshot(BaseModel):
    date: date          # 交易日
    ticker: str         # IBIT / FBTC / ARKB / BITB / BTCO / HODL / BRRR / EZBC / BTCW / DEFI / ETHA / ETH ...
    net_flow_usd: float # 当日净流入（>0 申购、<0 赎回）
    aum_usd: float | None = None  # 当日 AUM，可选
```

#### 2. `etf_flow.py` 提供 4 个分析函数

```python
BTC_SPOT_ETF_TICKERS = ("IBIT", "FBTC", "ARKB", "BITB", "BTCO", "HODL", "BRRR", "EZBC", "BTCW", "DEFI", "GBTC")
ETH_SPOT_ETF_TICKERS = ("ETHA", "FETH", "ETHV", "ETHE", "ETH", "QETH", "EZET", "CETH")

def aggregate_daily_flows(
    snapshots: list[ETFFlowSnapshot],
    *,
    tickers: tuple[str, ...] | None = None,
) -> dict[str, float]:
    """跨多个 ETF 按日聚合净流入。返回 {YYYY-MM-DD: total_net_flow}.
    tickers=None 时不过滤；不为 None 时只保留 tickers 中的标的（不区分大小写）。"""

def flow_zscore(daily_flows: list[float], *, window: int = 30) -> list[float]:
    """滚动 z-score（前 window-1 个为 NaN）。"""

def flow_extreme_signal(
    current_flow: float,
    history: list[float],
    *,
    z_threshold: float = 2.0,
) -> dict[str, float | str]:
    """与 funding_extreme_signal 同语义但应用于 ETF flow。
    signal: "large_inflow" (z >= +threshold), "large_outflow" (z <= -threshold), "neutral"."""

def flow_aum_velocity(net_flow_usd: float, total_aum_usd: float) -> float:
    """当日净流入占 AUM 的百分比（"velocity"）.
    > 5% = 显著资金事件.  raises ValueError if total_aum_usd <= 0."""
```

#### 3. 包导出

更新 `crypto_derivs/__init__.py` 导出 `ETFFlowSnapshot` + 4 个新函数 + 2 个 ticker 常量。

#### 4. 测试 `tests/test_crypto_derivs_etf_flow.py`

≥ 12 用例。

### 不做什么

- **不做**外部 ETF 数据抓取（Farside/CoinGlass/Bloomberg）— 留单独任务
- 不接 API 路由（F.1.13 时统一接）
- 不动前端
- 不引入新依赖

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/etf_flow.py`
  - `test -f apps/stock-assistant/backend/tests/test_crypto_derivs_etf_flow.py`
- [ ] **AC-2**: 顶层 import 正常
  - `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import ETFFlowSnapshot, aggregate_daily_flows, flow_zscore, flow_extreme_signal, flow_aum_velocity, BTC_SPOT_ETF_TICKERS, ETH_SPOT_ETF_TICKERS")` 退出码 0
- [ ] **AC-3**: 单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_etf_flow.py -v)` 退出码 0；用例数 ≥ 12
- [ ] **AC-4**: ruff 干净 — `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_etf_flow.py)`
- [ ] **AC-5**: mypy 干净 — `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports)`
- [ ] **AC-6**: 不引入新依赖 — `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空
- [ ] **AC-7**: 现有测试无回归 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_etf_flow.py -q)` 退出码 0
- [ ] **AC-8**: 之前任务的导出未破坏 — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import compute_basis, fetch_aggregated_derivs, FundingRate")` 退出码 0

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_etf_flow.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_etf_flow.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import ETFFlowSnapshot, aggregate_daily_flows, flow_zscore, flow_extreme_signal, flow_aum_velocity, BTC_SPOT_ETF_TICKERS, ETH_SPOT_ETF_TICKERS, compute_basis, fetch_aggregated_derivs; print('ok')")
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_etf_flow.py -q)
git diff main -- apps/stock-assistant/backend/pyproject.toml
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/etf_flow.py`
- `apps/stock-assistant/backend/tests/test_crypto_derivs_etf_flow.py`
- `docs/tasks/phaseF/crypto-etf-flow.md`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/models.py`（追加 `ETFFlowSnapshot`）
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py`（追加 export）

不允许改：所有其它路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #2；F.1 README
- **上游依赖**：F.1.10 / F.1.11
- **下游依赖**：F.1.13（前端面板）；外部 provider 单独任务
