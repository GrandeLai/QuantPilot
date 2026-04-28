# QuantPilot 因子体系指南

> **适用版本：** Phase 4（当前）  
> **相关模块：** `quantpilot.factors`、`quantpilot.ml.crypto_features`

---

## 目录

1. [什么是因子](#1-什么是因子)
2. [因子的分类](#2-因子的分类)
3. [QuantPilot 因子架构](#3-quantpilot-因子架构)
4. [当前因子全览](#4-当前因子全览)
   - 4.1 [核心技术因子（CoreCrypto）](#41-核心技术因子-corecrypto)
   - 4.2 [高级加密因子（AdvancedCrypto）](#42-高级加密因子-advancedcrypto)
   - 4.3 [pandas-ta 补充因子（PandasTaCrypto）](#43-pandas-ta-补充因子-pandastatacrypto)
5. [因子在系统中的流转路径](#5-因子在系统中的流转路径)
6. [使用指南：调用因子流水线](#6-使用指南调用因子流水线)
7. [使用指南：评估因子质量](#7-使用指南评估因子质量)
8. [使用指南：新增自定义因子](#8-使用指南新增自定义因子)
9. [常见错误与排查](#9-常见错误与排查)
10. [设计原则与约定](#10-设计原则与约定)

---

## 1 什么是因子

**因子（Factor / Feature）** 是从行情原始数据（OHLCV）衍生出来的、对未来收益有预测能力的数值型变量。

在量化交易中，因子的核心价值是将主观的"这只票看起来要涨"转化为可量化、可回测、可复现的数学表达式。

### 1.1 因子 vs 技术指标

| 维度 | 技术指标 | 量化因子 |
|------|----------|----------|
| 目的 | 辅助人工判断 | 作为模型输入特征 |
| 评价方式 | 看图识形态 | IC/IR、分层收益 |
| 使用方式 | 主观阅读 | 批量计算、标准化 |
| 典型工具 | TradingView | pandas / sklearn |

技术指标和量化因子在计算上往往相同（比如 RSI 的公式），区别在于**使用方式**：量化因子要求可以批量计算整个历史数据集，产生一列数值，再交给统计方法或机器学习模型去判断它是否有预测力。

### 1.2 好因子的特征

- **预测力**：与未来收益有显著相关性（IC 绝对值 > 0.03 即有参考价值）
- **稳定性**：在不同市场环境和时间段的 IC 符号一致（ICIR > 0.5）
- **独立性**：与其他已有因子的相关性低（皮尔逊相关 < 0.7）
- **可计算性**：不依赖未来信息，任意历史截面可独立计算

---

## 2 因子的分类

### 2.1 按信息来源

| 类型 | 说明 | 本系统示例 |
|------|------|-----------|
| 动量因子 | 价格趋势延续性 | `momentum_5`、`roc_10`、`macd_hist` |
| 反转因子 | 短期价格均值回归 | `willr_14`、`cci_20`、`rsi_14` |
| 波动率因子 | 价格波动幅度 | `atr_14`、`bb_width_20`、`skewness_30` |
| 量价因子 | 成交量与价格的关系 | `volume_ratio`、`mfi_14`、`vwap_dev_20` |
| 形态因子 | K 线结构特征 | `pin_score`、`upper_shadow_ratio` |
| 跨周期因子 | 多时间框架信号一致性 | `mtf_resonance`、`close_1h_ratio` |
| 振荡器因子 | 在固定区间内震荡的指标 | `stoch_k`、`stoch_d`、`dpo_20` |

### 2.2 按计算复杂度

- **一阶因子**：直接对 OHLCV 做算术运算（如 `momentum_5 = close / close.shift(5) - 1`）
- **滚动窗口因子**：需要 N 期历史数据（如 RSI、ATR）
- **多信号合成因子**：多个一阶因子加权组合（如 `mtf_resonance`）

---

## 3 QuantPilot 因子架构

```
OHLCV K 线数据
       │
       ▼
MultiTimeframeDatasetBuilder          ← 多周期对齐（15m/1h/4h/1d/1w）
       │
       │  frame: DataFrame（列名如 close_15m, high_1h, ...）
       ▼
CryptoFeaturePipeline.compute()
       │
       ├── FactorProviderRegistry
       │       ├── CoreCryptoFactorProvider      → 23 个核心技术因子
       │       ├── AdvancedCryptoFactorProvider  → 10 个高级因子
       │       └── PandasTaCryptoFactorProvider  → 7 个 pandas-ta 因子
       │
       │  + 跨周期衍生列（close_1h_ratio 等）
       │  + 市场微结构列（funding_rate, open_interest 等）
       │  + 目标变量（target_class, target_reversal）
       ▼
features: DataFrame（~40 列特征 + 标签）
       │
       ├── FeatureSelector      ← 去冗余（皮尔逊 + 互信息）
       │
       ▼
训练数据 → EnsembleStrategy / LGBMStrategy
```

### 3.1 核心接口

```python
class BaseFactorProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        """
        输入：多周期对齐 DataFrame（列名规范：{ohlcv}_{timeframe}）
        输出：与 frame 行索引完全对齐的因子 DataFrame
        """
```

**约定：**
- `compute()` 输入列名格式为 `{field}_{timeframe}`，如 `close_15m`、`high_1h`
- `compute()` 输出不包含原始 OHLCV 列，只包含派生因子
- 前视偏差：绝对禁止在 `compute()` 中使用任何未来信息

---

## 4 当前因子全览

### 4.1 核心技术因子（CoreCrypto）

文件：`src/quantpilot/factors/providers/core_crypto.py`  
数量：**23 个**

| 因子名 | 类型 | 说明 |
|--------|------|------|
| `returns` | 动量 | 1 期简单收益率 `(close - close_prev) / close_prev` |
| `log_returns` | 动量 | 对数收益率 `ln(close / close_prev)`，统计特性更好 |
| `momentum_5` | 动量 | 5 期价格变化率 |
| `momentum_20` | 动量 | 20 期价格变化率 |
| `volume_ratio` | 量价 | 当期成交量 / 20 期均量，衡量成交活跃度 |
| `ema_10` | 趋势 | 10 期指数移动平均 |
| `ema_20` | 趋势 | 20 期指数移动平均 |
| `ema_50` | 趋势 | 50 期指数移动平均 |
| `ema_spread_10_20` | 趋势 | `ema_10 / ema_20 - 1`，快慢线偏离度 |
| `ema_spread_20_50` | 趋势 | `ema_20 / ema_50 - 1`，中长期偏离度 |
| `macd_line` | 趋势 | MACD 主线（EMA12 - EMA26） |
| `macd_signal` | 趋势 | MACD 信号线（主线 9 期 EMA） |
| `macd_hist` | 趋势 | MACD 柱状图（主线 - 信号线） |
| `atr_14` | 波动率 | 14 期平均真实波幅，市场波动强度 |
| `adx_14` | 趋势 | 平均趋向指数，> 25 为趋势行情 |
| `plus_di_14` | 趋势 | +DI，多方向力量 |
| `minus_di_14` | 趋势 | -DI，空方向力量 |
| `rsi_14` | 反转 | 14 期相对强弱指数（0~100） |
| `bb_width_20` | 波动率 | 布林带宽度 = (上轨 - 下轨) / 中轨，量化波动率区间 |
| `donchian_20` | 趋势 | 20 期唐奇安通道宽度（最高 - 最低） |

### 4.2 高级加密因子（AdvancedCrypto）

文件：`src/quantpilot/factors/providers/advanced_crypto.py`  
数量：**10 个**

| 因子名 | 类型 | 说明 |
|--------|------|------|
| `vwap_dev_20` | 量价 | 20 期滚动 VWAP 乖离率（%），正值=价格高于均量均价 |
| `vwap_dev_60` | 量价 | 60 期滚动 VWAP 乖离率 |
| `skewness_20` | 波动率 | 20 期对数收益率分布偏度，捕捉肥尾不对称 |
| `skewness_60` | 波动率 | 60 期偏度 |
| `kurtosis_20` | 波动率 | 20 期超额峰度，> 0 表示肥尾，高波动预警 |
| `kurtosis_60` | 波动率 | 60 期超额峰度 |
| `upper_shadow_ratio` | 形态 | 上影线 / 实体比率，值越大=上方卖压越强 |
| `lower_shadow_ratio` | 形态 | 下影线 / 实体比率，值越大=下方买盘越强 |
| `pin_score` | 形态 | 插针方向得分 ∈ [-1, 1]，+1=锤子线，-1=射击之星 |
| `mtf_resonance` | 跨周期 | 多时间框架动量方向一致性 ∈ [-1, 1] |

### 4.3 pandas-ta 补充因子（PandasTaCrypto）

文件：`src/quantpilot/factors/providers/pandas_ta_crypto.py`  
数量：**7 个**  
依赖：`pandas-ta>=0.3.14b0`（已在 `pyproject.toml` 中）

| 因子名 | 类型 | 范围 | 说明 |
|--------|------|------|------|
| `cci_20` | 反转 | 无界（通常 ±200） | Commodity Channel Index，偏离统计均价的标准化程度 |
| `willr_14` | 反转 | [-100, 0] | Williams %R，< -80 超卖，> -20 超买 |
| `mfi_14` | 量价 | [0, 100] | Money Flow Index，量价加权 RSI，> 80 超买，< 20 超卖 |
| `stoch_k` | 反转 | [0, 100] | 随机振荡器 %K（快线），当前价在 N 期区间的相对位置 |
| `stoch_d` | 反转 | [0, 100] | 随机振荡器 %D（慢线，%K 的 3 期均值） |
| `roc_10` | 动量 | 无界 | Rate of Change（10 期），纯动量，正=上涨趋势 |
| `dpo_20` | 反转 | 无界 | Detrended Price Oscillator，剔除长期趋势，放大短周期波动 |

---

## 5 因子在系统中的流转路径

### 5.1 研究路径（离线训练）

```
CryptoResearchService.train_and_validate(request)
    │
    ├── MultiTimeframeDatasetBuilder.build() → dataset.frame
    │
    ├── CryptoFeaturePipeline.compute(dataset.frame) → features (40列)
    │
    ├── FeatureSelector.fit_transform(features[feature_cols], y)
    │       去除皮尔逊相关 > 0.85 的冗余因子，保留互信息更高的一个
    │
    ├── build_walk_forward_windows() → windows
    │
    └── 每个窗口：
            train_df = features.iloc[train_start:train_end+1]
            EnsembleStrategy.fit(train_df, feature_columns)
            EnsembleStrategy.predict(test_df) → [-1, 0, 1] 信号
```

### 5.2 信号路径（实时交易）

```
实时行情推送
    │
    CryptoFeaturePipeline.compute() → 单行因子
    │
    EnsembleStrategy.predict_proba() → [p_short, p_hold, p_long]
    │
    RollingQuantileFilter.filter(confidence=p_long)
    │   滚动分位数门槛，低于历史75%分位数则降级为 hold
    │
    SignalBroadcaster.publish() → TradingSignal
    │
    WebSocket 推送给前端
```

### 5.3 评估路径（因子质量检验）

```python
# 通过 API 调用
GET /factors/ic-analysis?symbol=BTC-USDT&timeframe=1h&limit=1000

# 内部使用 FactorCalculator
FactorCalculator.compute_ic(features, returns)
→ ICReport(ic_per_factor, ir_per_factor, layered_returns)
```

---

## 6 使用指南：调用因子流水线

### 6.1 获取因子数据（Python 代码）

```python
from quantpilot.data.storage import MarketDataStorage
from quantpilot.research.crypto_dataset import MultiTimeframeDatasetBuilder
from quantpilot.ml.crypto_features import CryptoFeaturePipeline

# 初始化
storage = MarketDataStorage()
builder = MultiTimeframeDatasetBuilder(storage)
pipeline = CryptoFeaturePipeline()

# 构建多周期数据集
dataset = builder.build(
    symbol="BTC-USDT",
    base_timeframe="15m",
    higher_timeframes=["1h", "4h", "1d"],
    limit=1000,
)

# 计算全量因子（约 40 列）
features = pipeline.compute(dataset.frame)

print(features.columns.tolist())
print(features.shape)         # (n_rows, ~40)
print(features.tail(3))       # 最新3期因子值
```

### 6.2 通过 HTTP API 调用

```bash
# 查看因子 IC 分析
curl "http://localhost:8000/api/factors/ic-analysis?symbol=BTC-USDT&timeframe=1h&limit=500"

# 触发研究训练（包含因子计算 + 模型训练）
curl -X POST "http://localhost:8000/api/research/train" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USDT",
    "base_timeframe": "15m",
    "higher_timeframes": ["1h", "4h", "1d"],
    "limit": 2000,
    "validation": {
      "train_size": 400,
      "test_size": 100,
      "step_size": 100,
      "embargo_size": 5
    }
  }'
```

### 6.3 只使用特定 Provider

```python
from quantpilot.factors.providers import (
    PandasTaCryptoFactorProvider,
    FactorProviderRegistry,
)
from quantpilot.ml.crypto_features import CryptoFeaturePipeline

# 只用 pandas-ta 因子
registry = FactorProviderRegistry(providers=[PandasTaCryptoFactorProvider()])
pipeline = CryptoFeaturePipeline(provider_registry=registry)
features = pipeline.compute(dataset.frame)
```

### 6.4 查看当前激活的 Provider

```python
from quantpilot.ml.crypto_features import CryptoFeaturePipeline

pipeline = CryptoFeaturePipeline()
print(pipeline._provider_registry.provider_names())
# ['core_crypto', 'advanced_crypto', 'pandas_ta_crypto']
```

---

## 7 使用指南：评估因子质量

### 7.1 信息系数（IC）

IC（Information Coefficient）是因子值与下一期收益率的截面相关系数，衡量因子的预测能力。

```python
from quantpilot.factors.calculator import FactorCalculator
import pandas as pd

calc = FactorCalculator()

# 假设已有 features DataFrame（含 target_class 列）
returns = features["forward_return_1d"]
factor_cols = [c for c in features.columns
               if c not in {"target_class", "target_reversal", "forward_return_1d"}]

ic_report = calc.compute_ic(features[factor_cols], returns)

# 按 IC 绝对值排序，看哪些因子最有效
for factor, ic in sorted(ic_report.ic_per_factor.items(),
                          key=lambda x: abs(x[1]), reverse=True)[:10]:
    print(f"{factor:30s}  IC={ic:.4f}  IR={ic_report.ir_per_factor[factor]:.2f}")
```

**IC 解读：**

| IC 绝对值 | 评价 |
|-----------|------|
| < 0.02 | 无效因子，噪声 |
| 0.02 ~ 0.05 | 弱信号，可配合其他因子使用 |
| 0.05 ~ 0.10 | 中等，具备独立使用价值 |
| > 0.10 | 强因子（加密市场中较少见） |

### 7.2 ICIR（IC 信息比）

```
ICIR = mean(IC) / std(IC)
```

ICIR > 0.5 表示因子在不同时间段的预测方向稳定，可信度较高。

### 7.3 FeatureSelector 自动筛选

```python
from quantpilot.ml.feature_selector import FeatureSelector

selector = FeatureSelector(corr_threshold=0.85)
selected_features, report = selector.fit_transform(
    X=features[factor_cols],
    y=features["target_class"],
    target_type="classification",
)

print(f"原始因子数: {report.n_original}")
print(f"保留因子数: {report.n_selected}")
print(f"被移除: {report.removed_features}")
print(f"移除原因: {report.removal_reasons}")
```

---

## 8 使用指南：新增自定义因子

### 8.1 创建新的 Provider

在 `src/quantpilot/factors/providers/` 下新建文件，例如 `my_factor.py`：

```python
"""自定义因子示例 Provider."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantpilot.factors.providers.base import BaseFactorProvider


class MyFactorProvider(BaseFactorProvider):
    """自定义因子集合."""

    @property
    def name(self) -> str:
        return "my_factors"

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(index=frame.index)

        close = frame["close_15m"]
        volume = frame["volume_15m"]
        features = pd.DataFrame(index=frame.index)

        # 示例：量价背离因子
        # 价格 20 期动量为正但成交量萎缩，视为潜在反转信号
        price_mom = close.pct_change(20)
        vol_ma = volume.rolling(20, min_periods=20).mean()
        vol_current = volume.rolling(5, min_periods=5).mean()
        features["vol_divergence"] = np.where(
            price_mom > 0,
            1 - vol_current / vol_ma.replace(0, np.nan),  # 正动量 + 量减
            vol_current / vol_ma.replace(0, np.nan) - 1,  # 负动量 + 量增
        )

        return features
```

### 8.2 注册到流水线

**方式 A：加入默认注册表（永久生效）**

修改 `src/quantpilot/ml/crypto_features.py`：

```python
# 在 __init__ 中
from quantpilot.factors.providers.my_factor import MyFactorProvider

self._provider_registry = provider_registry or FactorProviderRegistry(
    providers=[
        CoreCryptoFactorProvider(),
        AdvancedCryptoFactorProvider(),
        PandasTaCryptoFactorProvider(),
        MyFactorProvider(),          # 新增
    ]
)
```

**方式 B：按需传入（临时使用）**

```python
from quantpilot.factors.providers import FactorProviderRegistry
from quantpilot.factors.providers.core_crypto import CoreCryptoFactorProvider
from my_factor import MyFactorProvider
from quantpilot.ml.crypto_features import CryptoFeaturePipeline

registry = FactorProviderRegistry(providers=[
    CoreCryptoFactorProvider(),
    MyFactorProvider(),
])
pipeline = CryptoFeaturePipeline(provider_registry=registry)
```

### 8.3 编写测试

```python
# tests/test_my_factor.py
import numpy as np
import pandas as pd
from my_factor import MyFactorProvider


def make_frame(n=100):
    close = pd.Series(30000.0 + np.random.randn(n).cumsum())
    volume = pd.Series(np.random.uniform(500, 2000, n))
    high = close * 1.005
    low = close * 0.995
    return pd.DataFrame({
        "open_15m": close.shift(1).fillna(close),
        "high_15m": high,
        "low_15m": low,
        "close_15m": close,
        "volume_15m": volume,
    })


def test_output_columns():
    provider = MyFactorProvider()
    result = provider.compute(make_frame())
    assert "vol_divergence" in result.columns


def test_no_lookahead():
    # 前 20 行应为 NaN（rolling(20) 窗口期）
    provider = MyFactorProvider()
    result = provider.compute(make_frame(50))
    assert result["vol_divergence"].iloc[:20].isna().all()
```

### 8.4 检查前视偏差

**最常见的前视偏差来源：**

```python
# ❌ 错误：用未来数据标准化
features["close_norm"] = (close - close.mean()) / close.std()  # 用了全局统计量

# ✅ 正确：用滚动统计量
rolling_mean = close.rolling(window, min_periods=window).mean()
rolling_std = close.rolling(window, min_periods=window).std()
features["close_norm"] = (close - rolling_mean) / rolling_std.replace(0, 1)

# ❌ 错误：shift 用错方向
features["target"] = close.shift(-1) / close - 1  # 这是标签，不是特征！

# ✅ 正确：因子只用过去数据
features["momentum"] = close / close.shift(5) - 1  # shift 正数 = 用过去数据
```

---

## 9 常见错误与排查

### 9.1 `KeyError: 'close_15m'`

**原因：** `compute()` 的输入 DataFrame 列名不符合规范。

```python
# 检查输入列名
print(frame.columns.tolist())
# 期望包含：open_15m, high_15m, low_15m, close_15m, volume_15m
```

**解决：** 确保通过 `MultiTimeframeDatasetBuilder.build()` 生成数据集，而不是直接传入原始 K 线 DataFrame。

### 9.2 因子值全为 NaN

**原因：** 数据太少，不满足最小窗口期。例如 `atr_14` 需要至少 14 行，`skewness_60` 需要至少 60 行。

```python
# 检查最早的有效行
for col in features.columns:
    first_valid = features[col].first_valid_index()
    print(f"{col}: 首个有效行 = {first_valid}")
```

**解决：** 增加 `limit` 参数（建议至少 500 根 K 线）。

### 9.3 前视偏差检测

```python
# 在回测前检查：任何因子不应与 index 之后的价格有因果关系
# 方法：打乱时间顺序后的 IC 应接近 0
import numpy as np
shuffled_returns = features["forward_return_1d"].sample(frac=1).values
for col in factor_cols:
    ic_shuffled = np.corrcoef(features[col].dropna(), shuffled_returns[:len(features[col].dropna())])[0, 1]
    assert abs(ic_shuffled) < 0.05, f"{col} 可能有前视偏差"
```

### 9.4 FeatureSelector 报 `ValueError: 数据不足`

**原因：** `FeatureSelector` 要求至少 10 行数据。

**解决：** 在 `CryptoResearchService` 中已有 `if len(features) >= 10` 的保护，通常由数据量不足引起，增加 `limit` 即可。

---

## 10 设计原则与约定

### 10.1 无状态计算

每个 Provider 的 `compute()` 必须是无状态的——相同输入产生相同输出，不依赖实例变量缓存历史数据。  
（RobustScaler 这类有状态的对象属于 `EnsembleStrategy`，不属于 Provider。）

### 10.2 行索引对齐

`compute()` 的输出行数和行索引必须与输入 `frame` 完全一致。使用 `pd.DataFrame(index=frame.index)` 作为初始 DataFrame，确保 NaN 行被保留。

### 10.3 列名命名规范

- 全部小写，单词间用下划线
- 包含参数时跟在名称后，如 `rsi_14`、`ema_20`、`vwap_dev_60`
- 不得与 OHLCV 原始列名（`open_15m` 等）或标签列（`target_class`）重名

### 10.4 Provider 列名不重叠

多个 Provider 的输出列名不得重叠。`FactorProviderRegistry.compute()` 用 `pd.concat(axis=1)` 合并，重名列会导致 DataFrame 出现重复列。

测试覆盖：`test_pandas_ta_provider.py::TestNoColumnOverlap` 验证了与 CoreCrypto 无重叠。

### 10.5 滚动计算的最小周期

使用 `rolling(window, min_periods=window)` 而非 `min_periods=1`，确保窗口期不足时输出 NaN 而非用更少数据计算的噪声值。

---

*文档生成时间：2026-04-14*  
*当前因子总数：40 个（23 核心 + 10 高级 + 7 pandas-ta）*
