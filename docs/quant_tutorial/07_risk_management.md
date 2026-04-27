# 模块 7：风险管理与资金管理

> 策略决定你想赚什么，风险管理决定你能不能活到赚到那一天。

## 前置知识

- 建议完成 [回测系统](./05_backtesting.md)
- 建议完成 [策略开发](./06_strategy_development.md)

## 学习目标

学完本模块你将能够：

1. 根据策略特征选择合适的仓位控制方法。
2. 用固定止损、追踪止损、ATR 止损等方法限制单笔风险。
3. 在组合层面使用 VaR、CVaR、相关性监控做风险度量。
4. 设计一套可配置、可审计的风控规则引擎。
5. 理解“赚钱快”和“死得快”往往只隔着一个错误杠杆倍数。

## 正文内容

### 7.1 仓位管理

仓位管理的核心问题不是“能买多少”，而是：

> 这笔交易如果错了，我最多愿意承受多大代价？

#### 7.1.1 固定比例法

最常见，也最适合入门：

- 每次只投入总资金的固定比例，例如 5%、10%、20%

优点：

- 简单
- 易于执行
- 不容易一把梭导致账户大幅回撤

缺点：

- 不考虑不同资产波动差异
- 对高波动资产可能仍然过大

#### 7.1.2 凯利公式（Kelly Criterion）

##### 公式

$$f^* = \frac{bp - q}{b}$$

其中：

- $f^*$：理论最优资金占比
- $b$：赔率
- $p$：胜率
- $q = 1-p$

##### 直觉解释

凯利想解决的问题是：  
如果一个机会长期重复出现，我每次押多少，账户长期增长率最大？

这很像一个长期资源分配优化问题。

##### 半凯利（Half-Kelly）

实务里更常用：

$$f_{half} = \frac{1}{2}f^*$$

原因很简单：  
凯利对参数误差极其敏感，而胜率和盈亏比本来就只是估计值。半凯利更稳健。

##### 前提假设与偏差

凯利依赖这些理想前提：

- 胜率和赔率可稳定估计
- 各次交易相互独立
- 资金可连续分割

现实里这些条件经常不成立，所以不要把凯利当成魔法公式。

#### 7.1.3 风险预算法

做法：

1. 先决定每笔交易最大可承受亏损，例如总资金的 `1%`
2. 再根据止损距离反推仓位大小

公式：

$$Position\ Size = \frac{Risk\ Budget}{Entry\ Price - Stop\ Price}$$

这是非常实用的思路，因为它把“仓位”绑定到了“止损距离”。

#### 7.1.4 风险平价（Risk Parity）

思想：

> 不是每个策略或资产分一样多的钱，而是让每个部分承担大致相近的风险贡献。

最简单近似：

$$w_i \propto \frac{1}{\sigma_i}$$

波动率越高，权重越低；波动率越低，权重越高。

### 7.2 止损止盈

#### 7.2.1 固定止损（Fixed Stop Loss）

例子：

- 下跌 5% 就止损
- 跌破前低止损

优点：

- 简单
- 易于实现

缺点：

- 不考虑当前市场波动环境
- 在高波动资产上可能过紧，在低波动资产上可能过松

#### 7.2.2 追踪止损（Trailing Stop）

逻辑：

- 当价格朝有利方向移动时，止损线跟着上移
- 当价格反向波动时，止损线不放宽

示例：

```python
def trailing_stop(highest_price: float, trail_pct: float) -> float:
    """Return trailing stop price for a long position."""
    return highest_price * (1 - trail_pct)
```

优点：

- 能保护已有利润
- 适合趋势策略

缺点：

- 波动稍大的趋势中可能被“正常回撤”扫掉

#### 7.2.3 ATR 自适应止损

思路：

- 波动大时，止损给得更宽
- 波动小时，止损更紧

示例：

$$Stop = Entry - k \times ATR$$

这是把止损距离和市场真实波动绑定，非常适合跨资产系统。

#### 7.2.4 止盈策略

常见类型：

- 固定止盈：涨到 `+10%` 卖
- 移动止盈：跟随趋势抬高保护线
- 分批止盈：先卖一部分锁利润，剩余让利润奔跑

#### 7.2.5 止损止盈对回测指标的影响

- 止损更紧：
  - 回撤可能下降
  - 但胜率和趋势利润可能也下降
- 止盈过早：
  - 盈亏比会被压缩
  - 趋势策略尤其容易“赚小赔大”

所以止损止盈不是越多越好，而是要和策略逻辑一致。

### 7.3 组合层面风控

#### 7.3.1 VaR（Value at Risk）

##### 定义

在给定置信水平下，一定时间窗口内可能遭遇的最大损失阈值。

##### 历史模拟法

直接看历史收益分布分位数。

##### 参数法

假设收益服从某种分布，常见为正态分布，计算近似 VaR。

##### 直觉

VaR 回答的是：

> 在“通常情况下”，亏损大约会坏到什么程度？

但它不告诉你“更糟时会多糟”。

#### 7.3.2 CVaR / Expected Shortfall

当损失已经超过 VaR 时，平均还会亏多少：

$$CVaR_\alpha = \mathbb{E}[L \mid L \ge VaR_\alpha]$$

它比 VaR 更保守，也更适合看尾部风险。

#### 7.3.3 相关性矩阵监控

组合风控不能只看单个策略，而要看：

- 资产之间是否突然一起动
- 策略之间是否从“互补”变成“同涨同跌”

当相关性在危机时刻突然上升，你以为自己很分散，实际上可能在同一个风险因子上满仓。

### 7.4 风控规则引擎

#### 7.4.1 设计思路

把风控想成后端业务规则引擎：

- 输入：账户状态、市场状态、订单请求、持仓信息
- 输出：允许 / 拒绝 / 降级 / 强平 / 熔断

关键是：

- 规则独立
- 优先级明确
- 决策有审计记录

#### 7.4.2 常见规则

- 单笔最大亏损 ≤ `X%` 总资金
- 日最大亏损 ≤ `Y%` 总资金
- 最大同时持仓数量
- 连续亏损 `N` 次自动熔断
- 单资产最大持仓占比

#### 7.4.3 规则优先级与冲突处理

建议采用“硬规则优先于软规则”：

1. 法规与账户约束
2. 资金安全约束
3. 组合风控约束
4. 策略偏好约束

例如：

- 如果策略说“可以买”
- 但账户日亏损已超阈值

那么最终结果必须是“拒绝”，而不是“看策略多有信心”。

#### 7.4.4 一个最小风控规则引擎示例

```python
from dataclasses import dataclass


@dataclass
class RiskDecision:
    allowed: bool
    reason: str


def evaluate_risk(
    proposed_notional: float,
    account_equity: float,
    daily_loss_ratio: float,
    open_positions: int,
    max_position_ratio: float = 0.1,
    max_daily_loss_ratio: float = 0.03,
    max_open_positions: int = 10,
) -> RiskDecision:
    """Return a risk decision for a proposed order."""
    if proposed_notional / account_equity > max_position_ratio:
        return RiskDecision(False, "single-position-limit-exceeded")
    if daily_loss_ratio > max_daily_loss_ratio:
        return RiskDecision(False, "daily-loss-limit-exceeded")
    if open_positions >= max_open_positions:
        return RiskDecision(False, "too-many-open-positions")
    return RiskDecision(True, "ok")
```

## ⚠️ 常见误区与易混淆点

1. **“只要策略胜率高，就可以放大仓位。”**  
   错。胜率并不等于风险低，盈亏比和尾部风险一样重要。

2. **“凯利公式算出来多少就该押多少。”**  
   错。实盘里参数有误差，半凯利甚至更低才更常见。

3. **“止损会影响收益，所以少设一点更好。”**  
   错。没有止损不是提高收益，而是把风险暴露推迟到未来爆发。

4. **“组合里有很多资产，所以天然分散。”**  
   错。高度相关的十个头寸，本质上可能只是一种风险。

5. **“风控只是执行层的事情。”**  
   错。风控应该从策略设计阶段就开始，而不是上线前才临时补。

## 📚 推荐资源

- 书籍：《Trading Risk》  
  很适合建立风险视角。
- 书籍：《Position Sizing》  
  专门讨论资金管理和仓位控制。
- 在线课程：CME 或各券商风险管理入门材料  
  有助于理解保证金和衍生品风控。
- 开源项目：[PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt)  
  适合理解组合优化和风险预算。
- 官方文档：[FINRA Day Trading](https://www.finra.org/investors/investing/investment-products/stocks/day-trading)  
  了解 PDT 风险与保证金要求。

## 💻 实践项目

### 实践 1：为一个策略加入完整风险控制

- **任务描述**：给你已经实现的任一策略加入仓位控制、固定止损、ATR 止损和日亏损熔断。
- **推荐技术栈**：Python、pandas
- **预期产出物**：`risk_rules.py`、`risk_backtest_report.md`
- **验收标准**：
  - 至少包含 3 条硬风控规则
  - 回测报告中对比加入风控前后的收益与回撤
  - 能解释为什么某条风控提高了生存率

### 实践 2：实现一个组合风险面板

- **任务描述**：对多资产或多策略组合计算波动率、VaR、CVaR、相关性矩阵与风险预算占比。
- **推荐技术栈**：Python、pandas、numpy、seaborn
- **预期产出物**：`portfolio_risk_dashboard.ipynb`
- **验收标准**：
  - 至少包含 4 个风险指标
  - 输出相关性热力图
  - 能发现至少一个“看起来分散，实际高度相关”的例子
