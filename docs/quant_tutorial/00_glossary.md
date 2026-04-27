# 量化交易术语速查表

> 按英文术语字母排序。第一次见到陌生词时，把它当作“系统里的概念模型”来看，而不是纯金融黑话。

## A

### Alpha（阿尔法，超额收益）

相对于基准市场获得的“多出来的收益”。如果把指数涨跌理解为操作系统提供的公共能力，那么 Alpha 更像你自己的业务逻辑带来的额外价值。  
常见表达式：$r_p = \alpha + \beta r_m + \epsilon$。

### AMM（Automated Market Maker，自动做市商）

不依赖传统订单簿，而是依赖流动性池和定价公式完成交易撮合的机制，常见于 DEX。你可以把 AMM 想成“没有人工排队、只有一条定价函数的数据库索引”。  
经典常数乘积模型：$x \cdot y = k$。

### ATR（Average True Range，平均真实波幅）

用于度量市场波动程度的指标，不告诉你方向，只告诉你“价格一天能晃多大”。  
真实波幅：$TR_t = \max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)$；  
平均真实波幅：$ATR_n = \frac{1}{n}\sum_{i=0}^{n-1} TR_{t-i}$。

## B

### Basis（基差）

现货价格和衍生品价格之间的差异。对永续合约和期货策略来说，基差就像缓存值与真实数据之间的偏移量，偏离过大时常伴随套利机会或风险。  
常见定义：$\text{Basis} = P_{\text{futures}} - P_{\text{spot}}$。

### Beta（贝塔，市场暴露）

衡量某资产或组合跟随市场波动的敏感程度。Beta 高说明“跟大盘走”的成分更大。  
$\beta = \frac{\operatorname{Cov}(r_p, r_m)}{\operatorname{Var}(r_m)}$。

### Bid-Ask Spread（买卖价差）

买一价和卖一价之间的差距。它是最直接的交易摩擦之一，像数据库里读写锁竞争带来的额外成本。  
$\text{Spread} = Ask - Bid$。

### Bollinger Bands（布林带）

用均线作为中轨，再上下各加减若干倍标准差形成“价格通道”。价格贴近上轨不一定意味着该做空，但说明它相对最近波动区间已经偏高。  
中轨：$MB = SMA_n(C)$；上轨：$UB = MB + k\sigma_n$；下轨：$LB = MB - k\sigma_n$。

## C

### Calmar Ratio（卡玛比率）

用年化收益率除以最大回撤，衡量“每承受一单位最坏回撤，你换来了多少收益”。  
$\text{Calmar} = \frac{\text{Annualized Return}}{\text{Max Drawdown}}$。

### CEX（Centralized Exchange，中心化交易所）

由中心化平台托管账户、订单簿和撮合系统的交易所，例如 Binance、OKX。体验上更像传统互联网服务，由平台维护状态和权限。

### CCXT（CryptoCurrency eXchange Trading Library）

一个统一封装多家加密交易所 API 的开源库。你可以把它理解成“交易所 API 的 ORM/SDK 适配层”，用一套接口访问多家交易所。

### CVaR（Conditional Value at Risk，条件在险价值）

表示“当损失已经超过 VaR 阈值之后，平均还会亏多少”。比 VaR 更保守，因为它关注尾部更深处的损失。  
$CVaR_\alpha = \mathbb{E}[L \mid L \ge VaR_\alpha]$。

## D

### DEX（Decentralized Exchange，去中心化交易所）

通过链上智能合约完成交易的交易所，用户通常自己保管钱包私钥。它更像一个开放协议，而不是一个传统中心化服务端。

### Drawdown（回撤）

净值从历史高点回落的幅度。工程上可以把它看成“服务从峰值容量跌落后的退化比例”。  
$DD_t = \frac{Peak_t - Equity_t}{Peak_t}$。

## E

### EMA（Exponential Moving Average，指数移动平均线）

对新数据赋予更大权重的移动平均，响应速度比 SMA 更快。  
$EMA_t = \alpha C_t + (1-\alpha) EMA_{t-1}$，其中 $\alpha = \frac{2}{n+1}$。

## F

### Factor（因子）

能够解释或预测未来收益的可量化特征。对工程师来说，因子和机器学习里的 feature 非常接近，只不过它必须严格遵守时间顺序。

### Funding Rate（资金费率）

永续合约市场中，多空双方为使合约价格贴近现货而定期支付的费用。它像一个定时对账任务，用费用把偏离过大的价格往现货拉。  
常见近似：$\text{Funding Payment} = Position\ Value \times Funding\ Rate$。

## H

### HODL（长期持有）

源于社区梗，意思是“即使短期波动很大也继续持有”。策略上通常和高频或择时形成对照。

## K

### Kelly Criterion（凯利公式）

根据胜率和盈亏比计算理论最优下注比例的公式。它像一个资源调度算法，目标是长期增长率最大化，但对参数误差非常敏感。  
$f^* = \frac{bp-q}{b}$，其中 $b$ 为赔率，$p$ 为胜率，$q = 1-p$。

## L

### Leverage（杠杆）

用借来的资金放大头寸。收益和亏损都会被等比例放大，所以它不是“更快赚钱”，而是“更快接近风险边界”。  
名义杠杆：$\text{Leverage} = \frac{\text{Position Value}}{\text{Equity}}$。

### Limit Order（限价单）

指定“最多买到多少”或“至少卖到多少”的订单。它像带条件的数据库写入，价格不满足时不会立刻执行。

### Liquidity（流动性）

资产在不显著影响价格的前提下完成买卖的容易程度。流动性差时，大额交易会像对热点表做全表更新一样，引发明显冲击。

### Long（做多）

押注价格上涨而买入资产或建立多头头寸。盈利来自“卖出价高于买入价”。

## M

### MACD（Moving Average Convergence Divergence，指数平滑异同移动平均线）

比较快慢两条 EMA 的差值，观察趋势强化或减弱。  
$DIF = EMA_{12} - EMA_{26}$；$DEA = EMA_9(DIF)$；$MACD = 2(DIF - DEA)$。

### Margin（保证金）

开杠杆仓位时必须占用的自有资金。它是你对系统提交的“风险押金”，不足时会被强平。  
保证金率：$\text{Margin Ratio} = \frac{\text{Equity}}{\text{Borrowed Exposure}}$。

### Market Order（市价单）

以当前市场最优可得价格立即成交的订单。它像“优先成功，不保证成本”的写操作。

### Max Drawdown（最大回撤）

整个回测或持仓期间出现过的最大净值回撤。它是很多策略筛选时的硬门槛。  
$MDD = \max_t \left(\frac{Peak_t - Equity_t}{Peak_t}\right)$。

## O

### OBV（On-Balance Volume，能量潮）

根据收盘价涨跌将成交量加总或减总，试图观察“量能是否支持价格方向”。  
$OBV_t = OBV_{t-1} + \begin{cases}
V_t, & C_t > C_{t-1}\\
0, & C_t = C_{t-1}\\
-V_t, & C_t < C_{t-1}
\end{cases}$

### OHLCV（Open High Low Close Volume，开高低收量）

K 线数据的五个基础字段：开盘价、最高价、最低价、收盘价、成交量。它像一个时间窗口聚合后的结构化记录。

### Order Book（订单簿）

记录不同价格档位买卖挂单的有序集合。它可以理解成一个按价格排序的双边优先队列。

### Overfitting（过拟合）

模型或策略把历史噪声当成规律，导致样本内表现漂亮、样本外失效。和软件中过度针对测试数据写特殊分支很像。

## P

### Pairs Trading（配对交易）

同时交易两个相关资产的相对价格关系，而不是单独押方向。核心思想是“交易价差是否回归均值”。

### Perpetual Contract（永续合约）

没有固定到期日的衍生品合约，主要依靠资金费率让价格贴近现货。它不像传统期货那样必须在到期时交割。

### Profit Factor（盈亏比因子）

总盈利与总亏损绝对值之比，用于衡量策略整体赚亏结构。  
$\text{Profit Factor} = \frac{\sum Profits}{|\sum Losses|}$。

## R

### RSI（Relative Strength Index，相对强弱指数）

用一定窗口内平均上涨幅度和平均下跌幅度比较，衡量价格是否“过热”或“过冷”。  
$RSI = 100 - \frac{100}{1 + RS}$，其中 $RS = \frac{\text{Avg Gain}}{\text{Avg Loss}}$。

## S

### Settlement（结算）

交易达成后，资金与证券最终完成交收的过程。成交像“写入请求已接收”，结算像“事务真正提交成功”。

### Sharpe Ratio（夏普比率）

衡量单位总波动所换来的超额收益，是最常见的风险调整后收益指标。  
$\text{Sharpe} = \frac{\mathbb{E}[R_p - R_f]}{\sigma(R_p)}$。

### Short（做空）

先借入资产卖出，等价格下跌后再买回来归还，从差价中获利。风险与做多不同，因为理论上价格上涨没有上限。

### Signal（信号）

因子经过阈值、规则或模型输出后，转化为可执行的交易动作，如“买入”“卖出”“减仓”“观望”。它相当于策略系统对外发出的命令消息。

### Slippage（滑点）

订单预期成交价与实际成交价之间的差异。滑点既来自市场波动，也来自订单簿深度不足和排队位置变化。  
$\text{Slippage} = P_{\text{actual}} - P_{\text{expected}}$。

### SMA（Simple Moving Average，简单移动平均线）

对最近 $n$ 个价格做算术平均，得到最基础的平滑趋势线。  
$SMA_n = \frac{1}{n}\sum_{i=0}^{n-1} C_{t-i}$。

### Sortino Ratio（索提诺比率）

和夏普比率类似，但只把下行波动视为风险，因此更贴近“投资者真正怕的是亏钱而不是上涨太快”。  
$\text{Sortino} = \frac{\mathbb{E}[R_p - R_f]}{\sigma_{\text{downside}}(R_p)}$。

### Stop Loss（止损）

当亏损达到预设阈值时强制退出头寸的规则。它本质上是风险控制逻辑，不是预测逻辑。

## T

### Take Profit（止盈）

当盈利达到目标时锁定收益的规则。止盈不是“卖飞了”，而是把收益兑现机制写进系统。

### Tick Data（逐笔数据）

按每一笔成交或每一个最小市场事件记录的数据，粒度最高、体量最大。适合研究微观结构、短线执行和订单簿行为。

### Trailing Stop（追踪止损）

止损线会随着价格朝有利方向移动，但不会在不利方向放宽。它像一个只允许“单向收紧”的保护阈值。

## V

### VaR（Value at Risk，在险价值）

在给定置信水平下，某段时间内“最多可能亏到什么程度”的估计。  
形式化表达：$P(L > VaR_\alpha) = 1-\alpha$。

### Volatility（波动率）

衡量收益率离散程度的指标，常用标准差表示。波动率高不等于一定亏钱，但意味着结果更不稳定。  
历史波动率常写为：$\sigma = \sqrt{\operatorname{Var}(r)}$。

### VWAP（Volume Weighted Average Price，成交量加权平均价）

按照成交量加权后的平均成交价格，常用于评估执行质量。  
$VWAP = \frac{\sum P_t V_t}{\sum V_t}$。

## W

### Win Rate（胜率）

盈利交易次数占总交易次数的比例。胜率高不一定代表策略好，还要结合盈亏比看。  
$\text{Win Rate} = \frac{\# Winning\ Trades}{\# Total\ Trades}$。

## 延伸补充

如果你读到某个模块时仍然感觉术语很多，不要急着一次记住全部。量化学习最像后端工程里的“读老系统”过程：先知道每个组件的角色，再通过真实数据流把名字和行为绑定起来。建议把本文件与 [金融市场基础](./01_financial_market_basics.md)、[量化交易核心概念](./02_quant_trading_core_concepts.md) 交替阅读。
