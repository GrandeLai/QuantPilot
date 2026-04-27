# 模块 4：技术指标与特征工程

> 技术指标不是神秘信号发生器，而是对价格与成交量时间序列做特定聚合、平滑和比较之后得到的派生特征。

## 前置知识

- 建议先完成 [数据工程](./03_data_engineering.md)
- 建议完成 [量化交易核心概念](./02_quant_trading_core_concepts.md)

## 学习目标

学完本模块你将能够：

1. 理解常见技术指标到底在度量什么，而不是只会调用库函数。
2. 用 pandas/numpy 从零实现一组核心指标。
3. 把原始行情数据加工成适合回测与机器学习的特征矩阵。
4. 正确构造标签，避免前视偏差和信息泄露。
5. 在时间序列语境下做特征筛选，而不是机械复用普通表格任务套路。

## 正文内容

### 4.1 常用技术指标

下面所有示例默认输入 DataFrame `df` 至少包含这些列：

```python
import numpy as np
import pandas as pd

# columns: open, high, low, close, volume
```

#### 4.1.1 SMA（简单移动平均线）

**直觉解释**  
SMA 是最近一段价格的简单平均值，用于平滑掉短期噪声，观察更慢的趋势。它像给日志吞吐做固定窗口均值，让你先看大趋势，再看瞬时尖峰。

**数学公式**

$$SMA_n(t) = \frac{1}{n}\sum_{i=0}^{n-1} C_{t-i}$$

**Python 实现**

```python
def sma(series: pd.Series, window: int) -> pd.Series:
    """Return the simple moving average."""
    return series.rolling(window=window, min_periods=window).mean()
```

**参数选择建议**

- `5-20`：短线节奏
- `20-60`：中短期趋势
- `100-200`：长周期趋势判断

**常见用法与信号解读**

- 价格上穿 SMA：可能进入偏强阶段
- 价格下穿 SMA：可能进入偏弱阶段
- 多条均线排列：判断多空结构

**局限性**

- 响应慢
- 震荡市中容易频繁假突破
- 不考虑成交量和波动状态

#### 4.1.2 EMA（指数移动平均线）

**直觉解释**  
EMA 给新数据更高权重，比 SMA 更灵敏，适合希望更快跟踪趋势变化的场景。

**数学公式**

$$EMA_t = \alpha C_t + (1-\alpha)EMA_{t-1}, \quad \alpha = \frac{2}{n+1}$$

**Python 实现**

```python
def ema(series: pd.Series, span: int) -> pd.Series:
    """Return the exponential moving average."""
    return series.ewm(span=span, adjust=False, min_periods=span).mean()
```

**参数选择建议**

- `12`、`26`：MACD 经典参数
- `9-20`：更关注拐点的短线系统
- `50+`：中期趋势跟踪

**常见用法与信号解读**

- EMA 上穿长期均线：趋势增强
- 快速 EMA 与慢速 EMA 的差值扩大：趋势正在加速

**局限性**

- 比 SMA 更容易被短期噪声扰动
- 在剧烈震荡中同样会制造假信号

#### 4.1.3 RSI（相对强弱指数）

**直觉解释**  
RSI 比较一段时间内上涨力量和下跌力量的相对强弱，用来判断“涨太快”或“跌太狠”。

**数学公式**

$$RS = \frac{\text{Avg Gain}}{\text{Avg Loss}}$$

$$RSI = 100 - \frac{100}{1 + RS}$$

**Python 实现**

```python
def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Return RSI based on Wilder smoothing."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
```

**参数选择建议**

- `14`：经典参数
- `6-9`：更敏感，适合短线
- `21+`：更平滑，减少噪声

**常见用法与信号解读**

- `RSI < 30`：常被视为超卖
- `RSI > 70`：常被视为超买
- 背离：价格创新高但 RSI 没创新高，可能提示动能减弱

**局限性**

- 强趋势里 RSI 可以长时间“超买”或“超卖”而不反转
- 单独使用很容易抄底抄在半山腰

#### 4.1.4 MACD（指数平滑异同移动平均线）

**直觉解释**  
MACD 通过比较快慢两条 EMA 的差值，观察趋势方向和趋势强度是否在变化。

**数学公式**

$$DIF = EMA_{12}(C) - EMA_{26}(C)$$

$$DEA = EMA_9(DIF)$$

$$MACD = 2 \times (DIF - DEA)$$

**Python 实现**

```python
def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Return MACD components."""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = 2 * (dif - dea)
    return pd.DataFrame({"dif": dif, "dea": dea, "hist": hist})
```

**参数选择建议**

- `12, 26, 9`：默认经典配置
- 更短参数更敏感，但噪声更多

**常见用法与信号解读**

- `DIF` 上穿 `DEA`：常称“金叉”
- `DIF` 下穿 `DEA`：常称“死叉”
- 柱状图扩大：趋势动能增强

**局限性**

- 滞后
- 震荡市误报较多
- 对极端波动的适应性有限

#### 4.1.5 布林带（Bollinger Bands）

**直觉解释**  
布林带用均线加减标准差构造价格通道，试图衡量当前价格是否偏离近期常态区间。

**数学公式**

$$MB = SMA_n(C)$$

$$UB = MB + k \sigma_n(C), \quad LB = MB - k \sigma_n(C)$$

**Python 实现**

```python
def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Return Bollinger Bands."""
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"mid": mid, "upper": upper, "lower": lower})
```

**参数选择建议**

- `20, 2`：最经典
- 波动大资产可适当放宽倍数

**常见用法与信号解读**

- 贴近上轨：价格偏强，但不一定该做空
- 跌破下轨：价格偏弱，但不一定该做多
- 带宽收窄：可能预示波动压缩后即将放大

**局限性**

- 标准差并不天然等于可交易边界
- 趋势市中价格会“沿轨运行”，逆向操作容易吃亏

#### 4.1.6 ATR（平均真实波幅）

**直觉解释**  
ATR 不预测方向，只回答“这段时间价格通常能晃多大”，非常适合做仓位和止损距离的尺度尺。

**数学公式**

$$TR_t = \max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)$$

$$ATR_n = EMA_n(TR) \text{ 或 } \frac{1}{n}\sum TR$$

**Python 实现**

```python
def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Return Average True Range."""
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
```

**参数选择建议**

- `14`：默认
- 日线策略可用 `14-20`
- 短线系统可用更短窗口快速感知波动变化

**常见用法与信号解读**

- 用 `2 x ATR` 设止损
- 用 ATR 缩放仓位，波动大时自动降杠杆

**局限性**

- 只度量幅度，不告诉你方向
- 遇到跳空或极端行情时会突然放大

#### 4.1.7 OBV（能量潮）

**直觉解释**  
OBV 试图回答“成交量是否在支持当前价格方向”。

**数学公式**

$$OBV_t = OBV_{t-1} + s_t \cdot V_t$$

其中：

- $s_t = 1$，若 $C_t > C_{t-1}$
- $s_t = -1$，若 $C_t < C_{t-1}$
- $s_t = 0$，若相等

**Python 实现**

```python
def obv(df: pd.DataFrame) -> pd.Series:
    """Return On-Balance Volume."""
    direction = np.sign(df["close"].diff()).fillna(0)
    signed_volume = direction * df["volume"]
    return signed_volume.cumsum()
```

**参数选择建议**

- OBV 常看趋势和背离，本身不是窗口型指标
- 可叠加均线对 OBV 再做平滑

**常见用法与信号解读**

- 价格创新高而 OBV 不创新高：警惕量价背离
- OBV 持续抬升：可能说明买盘在累积

**局限性**

- 对异常大成交量敏感
- 在噪声市场中容易被“无意义放量”误导

#### 4.1.8 VWAP（成交量加权平均价）

**直觉解释**  
VWAP 衡量“按成交量加权后，市场今天平均以什么价格成交”，常用来评估执行好坏。

**数学公式**

$$VWAP_t = \frac{\sum_{i=1}^{t} P_i V_i}{\sum_{i=1}^{t} V_i}$$

实务中常用典型价格：

$$P_i = \frac{H_i + L_i + C_i}{3}$$

**Python 实现**

```python
def vwap(df: pd.DataFrame) -> pd.Series:
    """Return VWAP for an intraday window."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cum_pv = (typical_price * df["volume"]).cumsum()
    cum_v = df["volume"].cumsum()
    return cum_pv / cum_v.replace(0, np.nan)
```

**参数选择建议**

- 日内交易常按“单个交易日”重置
- 多日 VWAP 需明确重置边界，否则解释会混乱

**常见用法与信号解读**

- 价格高于 VWAP：当日偏强
- 做执行评估：买入低于 VWAP、卖出高于 VWAP 通常更理想

**局限性**

- 对日内使用最自然，跨多日意义会变弱
- 不是独立择时圣杯

#### 4.1.9 KDJ（随机指标）

**直觉解释**  
KDJ 关注当前收盘价在最近一段时间高低区间中的相对位置，类似问“现在收在区间的哪个百分位”。

**数学公式**

先计算 RSV：

$$RSV_t = \frac{C_t - LL_n}{HH_n - LL_n} \times 100$$

再递推：

$$K_t = \frac{2}{3}K_{t-1} + \frac{1}{3}RSV_t$$

$$D_t = \frac{2}{3}D_{t-1} + \frac{1}{3}K_t$$

$$J_t = 3K_t - 2D_t$$

**Python 实现**

```python
def kdj(df: pd.DataFrame, window: int = 9) -> pd.DataFrame:
    """Return K, D, J values."""
    low_n = df["low"].rolling(window=window, min_periods=window).min()
    high_n = df["high"].rolling(window=window, min_periods=window).max()
    rsv = ((df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100).fillna(50)
    k = rsv.ewm(alpha=1 / 3, adjust=False).mean()
    d = k.ewm(alpha=1 / 3, adjust=False).mean()
    j = 3 * k - 2 * d
    return pd.DataFrame({"k": k, "d": d, "j": j})
```

**参数选择建议**

- `9`：常见默认值
- 窗口越短越敏感，适合短线

**常见用法与信号解读**

- K 上穿 D：偏强
- J 值极端：表示波动非常剧烈

**局限性**

- 在震荡市中容易来回打脸
- J 值可能超出 `0-100`，要理解其含义而不是机械套阈值

#### 4.1.10 成交量相关指标

成交量不只是一列 `volume`，它常常是价格信号的“可信度修正项”。

**直觉解释**  
如果价格上涨同时放量，说明这次上涨更可能被更多资金参与；如果价格上涨却缩量，就像 API QPS 提升但用户量并没上来，可能不够扎实。

**常见公式**

- 成交量均线：

$$VMA_n = SMA_n(V)$$

- 成交量比率：

$$Volume\ Ratio = \frac{VMA_{short}}{VMA_{long}}$$

- Chaikin Money Flow（资金流量）：

$$MFM = \frac{(C-L) - (H-C)}{H-L}$$

$$CMF_n = \frac{\sum_{i=1}^n MFM_i \cdot V_i}{\sum_{i=1}^n V_i}$$

**Python 实现**

```python
def volume_features(df: pd.DataFrame, short: int = 5, long: int = 20, cmf_window: int = 20) -> pd.DataFrame:
    """Return common volume-derived indicators."""
    vma_short = df["volume"].rolling(short, min_periods=short).mean()
    vma_long = df["volume"].rolling(long, min_periods=long).mean()
    volume_ratio = vma_short / vma_long.replace(0, np.nan)

    mfm = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (
        (df["high"] - df["low"]).replace(0, np.nan)
    )
    cmf = (mfm * df["volume"]).rolling(cmf_window, min_periods=cmf_window).sum() / (
        df["volume"].rolling(cmf_window, min_periods=cmf_window).sum().replace(0, np.nan)
    )
    return pd.DataFrame({"vma_short": vma_short, "vma_long": vma_long, "volume_ratio": volume_ratio, "cmf": cmf})
```

**参数选择建议**

- `5/20` 常用于短长对比
- CMF 常见 `20`

**常见用法与信号解读**

- 放量突破：趋势确认力度增强
- 缩量上涨：趋势可持续性存疑
- CMF 为正：资金流入占优

**局限性**

- 成交量在不同市场意义不同，美股与加密不能简单套同一阈值
- 某些交易所的成交量质量和清洗口径并不一致

### 4.2 特征工程

技术指标只是特征工程的一部分。真正可用的特征体系，通常会把价格、成交量、时间、波动率和状态切换一起考虑。

#### 4.2.1 滞后特征（Lag Features）

常见形式：

- `close_lag_1`
- `close_lag_5`
- `volume_lag_3`

用途：

- 给模型提供“过去发生了什么”
- 构造自回归类信息

```python
def add_lag_features(df: pd.DataFrame, columns: list[str], lags: list[int]) -> pd.DataFrame:
    """Add lag features for selected columns."""
    result = df.copy()
    for col in columns:
        for lag in lags:
            result[f"{col}_lag_{lag}"] = result[col].shift(lag)
    return result
```

#### 4.2.2 滚动窗口统计

常见统计：

- rolling mean
- rolling std
- rolling skew

```python
def add_rolling_stats(df: pd.DataFrame, column: str, window: int = 20) -> pd.DataFrame:
    """Add rolling statistics."""
    result = df.copy()
    result[f"{column}_mean_{window}"] = result[column].rolling(window).mean()
    result[f"{column}_std_{window}"] = result[column].rolling(window).std()
    result[f"{column}_skew_{window}"] = result[column].rolling(window).skew()
    return result
```

#### 4.2.3 收益率特征

##### 简单收益率

$$r_t = \frac{C_t}{C_{t-1}} - 1$$

##### 对数收益率

$$\ell_t = \ln\left(\frac{C_t}{C_{t-1}}\right)$$

区别：

- 简单收益率更直观
- 对数收益率更适合连续复利和某些统计建模

```python
def add_return_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add simple and log returns."""
    result = df.copy()
    result["ret_1"] = result["close"].pct_change()
    result["log_ret_1"] = np.log(result["close"] / result["close"].shift(1))
    return result
```

#### 4.2.4 交叉特征

典型例子是“金叉/死叉”布尔编码：

```python
def add_cross_features(df: pd.DataFrame, fast_col: str, slow_col: str) -> pd.DataFrame:
    """Add crossover boolean features."""
    result = df.copy()
    result["golden_cross"] = (result[fast_col] > result[slow_col]) & (
        result[fast_col].shift(1) <= result[slow_col].shift(1)
    )
    result["death_cross"] = (result[fast_col] < result[slow_col]) & (
        result[fast_col].shift(1) >= result[slow_col].shift(1)
    )
    return result
```

#### 4.2.5 时间特征

常见时间特征：

- 小时
- 星期几
- 月份
- 是否接近收盘

如果做模型训练，最好做周期编码：

```python
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add cyclical time features from a DatetimeIndex."""
    result = df.copy()
    hour = result.index.hour
    weekday = result.index.weekday
    result["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    result["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    result["weekday_sin"] = np.sin(2 * np.pi * weekday / 7)
    result["weekday_cos"] = np.cos(2 * np.pi * weekday / 7)
    return result
```

#### 4.2.6 波动率特征

##### 历史波动率

$$\sigma_n = std(r_t) \times \sqrt{annualization\ factor}$$

##### Parkinson 波动率

利用日内高低价估计波动：

$$\sigma_P = \sqrt{\frac{1}{4n\ln 2} \sum_{t=1}^n \left(\ln \frac{H_t}{L_t}\right)^2}$$

```python
def add_volatility_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add volatility-related features."""
    result = df.copy()
    log_ret = np.log(result["close"] / result["close"].shift(1))
    result[f"hist_vol_{window}"] = log_ret.rolling(window).std() * np.sqrt(252)
    parkinson = ((np.log(result["high"] / result["low"])) ** 2).rolling(window).mean()
    result[f"parkinson_vol_{window}"] = np.sqrt(parkinson / (4 * np.log(2)))
    return result
```

### 4.3 标签构造

标签（Label）是模型要学习预测的目标。量化里最常见的三类标签如下。

#### 4.3.1 未来 N 根 K 线收益率（回归标签）

$$y_t = \frac{C_{t+N}}{C_t} - 1$$

```python
def make_forward_return_label(df: pd.DataFrame, horizon: int = 5) -> pd.Series:
    """Return forward return labels."""
    return df["close"].shift(-horizon) / df["close"] - 1
```

#### 4.3.2 涨跌分类标签（二分类）

```python
def make_binary_label(df: pd.DataFrame, horizon: int = 5) -> pd.Series:
    """Return up/down labels."""
    forward_ret = df["close"].shift(-horizon) / df["close"] - 1
    return (forward_ret > 0).astype("Int64")
```

#### 4.3.3 三分类标签（涨 / 跌 / 横盘）

```python
def make_ternary_label(df: pd.DataFrame, horizon: int = 5, threshold: float = 0.01) -> pd.Series:
    """Return three-class labels: up, flat, down."""
    forward_ret = df["close"].shift(-horizon) / df["close"] - 1
    labels = pd.Series("flat", index=df.index)
    labels[forward_ret > threshold] = "up"
    labels[forward_ret < -threshold] = "down"
    return labels
```

#### 4.3.4 ⚠️ 前视偏差警告

错误示例：

- 今天用未来 5 根 K 线收益率作为标签
- 又不小心让特征里包含了未来 5 根里的价格

正确原则：

1. 特征只能使用当前及过去信息
2. 标签可以来自未来，但训练时必须把未来目标和当前特征严格对齐
3. 删除最后 `N` 行无标签样本

### 4.4 特征选择

#### 4.4.1 相关性过滤

删除高度共线的特征，减少冗余。  
比如 `sma_20` 与 `ema_20` 高度相关时，不一定要都保留。

#### 4.4.2 互信息（Mutual Information）

适合评估非线性关系。  
直觉上，它衡量“知道这个特征后，目标不确定性减少了多少”。

#### 4.4.3 基于树模型的特征重要性

用 Random Forest、LightGBM 等模型的 feature importance 评估哪些特征更有解释力。

#### 4.4.4 递归特征消除（RFE）

逐步删除不重要特征，寻找更精简的组合。

#### 4.4.5 时间序列交叉验证中的注意事项

- 不能在全样本上先选特征，再回头做时间切分
- 每个训练窗口都应在自身内部完成标准化、筛选和训练
- 验证集只能模拟真实未来

## ⚠️ 常见误区与易混淆点

1. **“技术指标本身就是策略。”**  
   错。指标只是特征，策略还需要规则、仓位、风控和执行。

2. **“参数用经典值就一定靠谱。”**  
   错。经典参数只是起点，不同市场、周期和成本结构下效果会差很多。

3. **“特征越复杂越高级。”**  
   错。最有价值的特征经常并不花哨，但解释清楚、实现稳定、样本外稳健。

4. **“标签构造只是几行 shift，不会出问题。”**  
   错。量化项目里很多最致命的 bug 就藏在 `shift` 和对齐里。

5. **“随机切分在 ML 里很常见，所以量化也能用。”**  
   错。时间序列必须尊重先后顺序。

## 📚 推荐资源

- 书籍：《Technical Analysis of the Financial Markets》  
  技术指标百科式参考，适合查定义和经典用法。
- 书籍：《Advances in Financial Machine Learning》  
  对标签、特征和时间序列验证很有启发。
- 在线课程：Coursera《Machine Learning for Trading》  
  特征工程与时间序列建模结合得比较好。
- 开源项目：[vectorbt](https://github.com/polakowo/vectorbt)  
  很适合快速做指标实验和组合测试。
- 官方文档：[pandas Window API](https://pandas.pydata.org/docs/user_guide/window.html)  
  绝大多数指标都离不开 rolling/ewm。

## 💻 实践项目

### 实践 1：搭建一个基础特征工厂

- **任务描述**：针对一份 OHLCV 数据，生成至少 30 个特征列，覆盖趋势、波动、成交量、滞后和时间特征。
- **推荐技术栈**：Python、pandas、numpy
- **预期产出物**：`feature_factory.py`、`feature_sample.parquet`
- **验收标准**：
  - 所有特征都能说明其金融含义
  - 无未来信息泄露
  - 输出文件可直接供模型或回测读取

### 实践 2：为一个二分类模型构造标签并做时间切分

- **任务描述**：基于 BTC 或 AAPL 数据，构造未来 5 根 K 线上涨/下跌标签，并完成时间序列训练集/验证集切分。
- **推荐技术栈**：Python、pandas、scikit-learn
- **预期产出物**：`labeling_pipeline.ipynb`
- **验收标准**：
  - 能清晰展示特征与标签对齐过程
  - 至少说明 2 种可能导致信息泄露的错误写法
  - 训练与验证切分严格按时间顺序进行
