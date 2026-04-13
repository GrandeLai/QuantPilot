# 主页面 Tab 功能说明

> 本文档面向所有使用者（包括非金融背景人员），介绍 QuantPilot 主页面各 Tab 页的功能、数据来源和使用场景。
>
> **什么是 QuantPilot？**  
> QuantPilot 是一个运行在本地的量化交易辅助平台。它可以帮助用户查看股票/资产价格走势、编写和测试交易策略、管理模拟交易账户，并借助 AI 辅助分析。所有数据默认存储在本地，不依赖云服务。

---

## 主工作台结构（新版）

- 研究中心：看盘、选股/选币、候选池研究
- 策略库：策略编写、版本、模板、策略资产管理
- 验证中心：回测、样本外验证、参数实验、晋升判断
- 运行中心：模拟盘、实盘、订单、执行状态
- 风险与复盘：组合风险、回撤、熔断、复盘结论

---

## 加密货币在主工作台中的位置（新版）

为了让加密货币和美股遵循同一套赚钱工作流，当前加密能力已经拆分到主工作台的四个中心，而不再作为一个包揽全部功能的独立终端：

- **研究中心**：加密现货行情与图表，负责候选交易对观察。
- **验证中心**：加密货币策略回测与多周期 ML 验证摘要，负责验证历史表现与概率输出。
- **验证中心补充**：加密回测默认优先推荐 `VWAP_EMA_Trend`，并以 `1h` 作为首个验证周期，方便直接承接多周期研究结果。
- **运行中心**：现货交易、永续合约交易、期权交易，负责真实运行与下单；其中内置 `VWAP + EMA` 趋势模板可直接进入加密验证与后续运行链路。
- **风险与复盘**：加密持仓与挂单，负责风险暴露和执行状态观察。

这样做的目的是让用户在股票与加密之间切换时，不必重新理解另一套产品结构。

---

## 目录

- [看盘 — 价格走势图](#看盘--价格走势图)
- [策略 — 策略代码管理](#策略--策略代码管理)
- [模拟盘 — 虚拟资金交易](#模拟盘--虚拟资金交易)
- [回测 — 历史验证](#回测--历史验证)
- [告警 — 价格提醒](#告警--价格提醒)
- [AI助手 — 智能问答](#ai助手--智能问答)
- [策略生成 — AI 自动写策略](#策略生成--ai-自动写策略)
- [期权 — 衍生品定价工具](#期权--衍生品定价工具)
- [优化 — 参数网格搜索](#优化--参数网格搜索)
- [组合 — 多策略管理](#组合--多策略管理)
- [插件 — 扩展模块管理](#插件--扩展模块管理)
- [ML — 机器学习策略](#ml--机器学习策略)
- [情绪 — 新闻情绪分析](#情绪--新闻情绪分析)
- [信号 — 交易信号广播](#信号--交易信号广播)
- [实时 — WebSocket 实时推送](#实时--websocket-实时推送)

---

## 看盘 — 价格走势图

### 功能概述

显示指定股票或资产的 K 线图（candlestick chart，即每段时间内的开盘价、最高价、最低价、收盘价组成的蜡烛图）和技术指标（如均线、布林带），是查看价格历史走势的主界面。

### 数据来源

- **历史价格数据**：存储在本地 DuckDB 数据库中，通过 `GET /api/chart/bars` 接口读取。数据最初由 `yfinance`（雅虎财经）或 `AKShare`（A 股数据源）拉取并写入本地。
- **技术指标**：在后端实时计算后返回，接口为 `POST /api/chart/batch-indicators`，计算模块位于 `backend/src/quantpilot/indicators/`。
- **数据拉取触发**：用户可点击"获取数据"按钮，调用 `POST /api/chart/trigger-fetch`，后台异步从网络拉取最新价格。
- 前端组件：`frontend/src/components/ChartPanel.tsx`

### 使用目的

用户想了解某支股票（如 AAPL、比亚迪 002594）过去一段时间的价格变化趋势时使用。可以叠加均线（EMA，指数移动平均线，用于平滑价格波动、识别趋势方向）或布林带（Bollinger Bands，用于衡量价格波动范围），辅助判断当前价格处于高位还是低位。

---

## 策略 — 策略代码管理

### 功能概述

提供一个代码编辑器，用于创建、编辑和保存交易策略的 Python 代码。策略是一段描述"在什么条件下买入或卖出"的程序逻辑。

### 数据来源

- **策略列表**：从本地文件系统读取（`data/strategies/` 目录），通过 `GET /api/strategy/list` 获取。
- **内置模板**：`GET /api/strategy/templates` 返回预设的策略示例，帮助用户快速上手。
- **保存/更新**：`POST /api/strategy/create`、`PUT /api/strategy/{id}/update` 将代码写回本地文件。
- 前端组件：`frontend/src/components/StrategyPanel.tsx`  
- 后端模块：`backend/src/quantpilot/api/strategy.py`

### 使用目的

当用户想自定义交易逻辑（例如"当股价突破 20 日均线时买入"），可以在这里写 Python 代码并保存。内置模板可以作为起点，避免从零编写。保存后的策略可在"回测"页面进行历史验证。

---

## 模拟盘 — 虚拟资金交易

### 功能概述

创建虚拟交易账户（使用模拟资金，不涉及真实金钱），用真实历史价格数据模拟买卖操作，查看账户的盈亏和持仓情况。

> **持仓**：指当前持有的股票数量和成本价。例如"持有 100 股苹果，均价 150 美元"。

### 数据来源

- **会话（session）列表和详情**：`GET /api/paper/sessions`、`GET /api/paper/sessions/{id}`，数据保存在本地内存（服务重启后清空）。
- **订单队列（可选，需 Redis）**：`POST /api/paper/sessions/{id}/orders/enqueue` 将订单写入 Redis Streams，实现可靠的订单排队。
- 前端组件：`frontend/src/components/PaperTradingPanel.tsx`  
- 后端模块：`backend/src/quantpilot/paper/`、`backend/src/quantpilot/api/paper.py`

### 使用目的

在投入真实资金之前，用模拟账户验证策略是否可行。用户可以设置初始资金金额、手续费（交易成本）和滑点（买卖价格与预期价格的微小偏差），观察策略在历史行情下的表现，确认盈亏合理后再考虑实盘。

---

## 回测 — 历史验证

### 功能概述

将写好的交易策略放到过去某段时间的历史数据中"跑一遍"，计算如果当时按这个策略操作，最终盈亏如何，从而评估策略的有效性。

### 数据来源

- 后端 API 已就绪：`POST /backtest/run`、`GET /backtest/results`，位于 `backend/src/quantpilot/api/backtest.py`。
- 历史 K 线数据来自本地 DuckDB 数据库（与"看盘"页面共用同一数据源）。
- ⚠️ 前端界面尚在开发中，当前页面为占位符。
- 后端回测引擎：`backend/src/quantpilot/backtest/engine.py`

### 使用目的

策略编写完成后，在此对其进行历史验证。通过夏普比率（Sharpe Ratio，衡量每承担一单位风险能获得多少超额收益，越高越好）、最大回撤（最坏情况下账户从最高点下跌的幅度）等指标，量化评估策略的风险收益特征，排除"看起来好但实际不可行"的策略。

---

## 告警 — 价格提醒

### 功能概述

设置价格监控规则，当某支股票或资产的价格满足特定条件（如超过某个价格、跌破某个价格）时，自动触发提醒事件并记录。

### 数据来源

- **告警规则**：`GET /api/alerts/rules`、`POST /api/alerts/rules`，存储在本地 SQLite 数据库中。
- **触发事件历史**：`GET /api/alerts/events?limit=20`，读取最近 20 条触发记录。
- 前端组件：`frontend/src/components/AlertsPanel.tsx`  
- 后端模块：`backend/src/quantpilot/api/alerts.py`

### 使用目的

用户不必时刻盯着价格走势。设置好"AAPL 超过 200 美元时提醒我"之类的规则后，系统会在价格满足条件时自动记录事件。适合做中长线关注时的价格监控，避免手动反复查看。

---

## AI助手 — 智能问答

### 功能概述

内嵌的 AI 聊天界面，支持与大语言模型（LLM，如 GPT-4o、Claude、DeepSeek）对话，提问任意金融或编程相关的问题，获得解释或建议。

### 数据来源

- **AI 接口**：`POST /api/llm/stream`，使用 SSE（Server-Sent Events，服务器持续推送文字流）的方式实时返回 AI 回复，避免长时间等待。
- AI 调用通过 `litellm` 库统一接入多个模型提供商，配置位于 `backend/src/quantpilot/api/llm.py`。
- 前端组件：`frontend/src/components/LLMChat.tsx`

### 使用目的

遇到不熟悉的金融概念（如"什么是布林带？"）或策略代码有疑问时，可直接在这里提问。也可以粘贴自己写的策略代码，请 AI 分析潜在问题或改进建议，无需切换到其他工具。

---

## 策略生成 — AI 自动写策略

### 功能概述

用自然语言（白话文）描述想要的交易策略，AI 自动生成完整的 Python 策略代码，并给出解释说明。

### 数据来源

- **代码生成接口**：`POST /api/llm/generate-strategy`，将用户输入的策略描述发送给 LLM，返回策略名称、代码和解释。
- 前端组件：`frontend/src/components/StrategyGeneratorPanel.tsx`  
- 后端模块：`backend/src/quantpilot/api/llm.py`

### 使用目的

不会写 Python 代码或不熟悉策略框架的用户，可以在这里用一句话描述自己的想法（例如"当 5 日均线从下方穿越 20 日均线时买入，从上方穿越时卖出"），让 AI 生成完整代码，再复制到"策略"页保存和使用，大幅降低策略开发门槛。

---

## 期权 — 衍生品定价工具

### 功能概述

计算期权（一种金融衍生品，赋予持有者在特定价格买入或卖出资产的权利）的理论价格和风险指标（Greeks），也支持从当前市场价格反推隐含波动率。

> **期权 Greeks**：衡量期权价格对各种因素变化的敏感度，包括：
> - **Delta（δ）**：股价变动 1 元时，期权价格的变动量
> - **Gamma（γ）**：Delta 本身的变动速度
> - **Theta（θ）**：时间流逝对期权价格的影响（每天减少多少）
> - **Vega（ν）**：波动率变化对期权价格的影响
> - **Rho（ρ）**：利率变化对期权价格的影响
>
> **隐含波动率（Implied Volatility）**：市场认为未来价格波动幅度有多大，由当前期权市场价格反推得出。

### 数据来源

- **Greeks 计算**：`POST /api/options/greeks`，输入参数（标的价格 S、行权价 K、到期时间 T、无风险利率 r、波动率 σ），后端用 Black-Scholes 模型计算，代码位于 `backend/src/quantpilot/options/`。
- **隐含波动率**：`POST /api/options/implied-vol`，由市场期权价格反向求解。
- 前端组件：`frontend/src/components/OptionsGreeksPanel.tsx`

### 使用目的

交易期权（股票期权、ETF 期权等）时，用于快速估算特定合约的理论价值和风险敞口，帮助判断当前市场价格是否合理，以及持有该期权在价格或时间变化时的盈亏情况。

---

## 优化 — 参数网格搜索

### 功能概述

对一个交易策略，枚举多组不同的参数组合，分别进行回测，自动找出表现最好（夏普比率最高）的参数配置。

> **网格搜索（Grid Search）**：系统地尝试所有参数组合，类似于穷举法。例如对"均线周期"尝试 5、10、20 三个值，对"止损比例"尝试 1%、2%、3%，共 9 种组合全部测试一遍。
>
> **夏普比率**：策略的综合评分，同时考虑收益和风险，值越高代表"用更小的风险换取了更多的收益"。

### 数据来源

- **优化接口**：`POST /api/optimize/grid-search`，提交策略名称和参数网格（JSON 格式），后端遍历所有参数组合进行回测，返回排序后的结果。
- 后端模块：`backend/src/quantpilot/api/optimize.py`，依赖 `optuna`（开源超参数优化库）和本地回测引擎。
- 前端组件：`frontend/src/components/OptimizationPanel.tsx`

### 使用目的

策略写好后，不确定使用哪组参数最合适时使用。将待测试的参数范围输入，系统自动穷举并返回排名，省去手动逐一调参的繁琐工作，找到历史表现最佳的参数配置。

---

## 组合 — 多策略管理

### 功能概述

汇总查看所有已激活策略的整体资金情况，并显示各策略之间的相关性（即它们的盈亏是否会同涨同跌）。

> **相关性（Correlation）**：取值在 -1 到 1 之间。接近 1 表示两个策略同步涨跌（分散风险效果差）；接近 0 表示无关联（组合效果好）；接近 -1 表示反向运动（天然对冲）。

### 数据来源

- **组合汇总**：`GET /api/portfolio/summary`，返回总资金、各策略分配资金、盈亏数据。
- **相关性矩阵**：`GET /api/portfolio/correlation`，计算各策略历史收益的两两相关系数。
- 后端模块：`backend/src/quantpilot/api/portfolio.py`、`backend/src/quantpilot/portfolio/`（使用 `scipy` 计算相关性）。
- 前端组件：`frontend/src/components/PortfolioPanel.tsx`

### 使用目的

同时运行多个策略时，用于监控整体账户健康状况。通过相关性矩阵，可以发现哪些策略过于相似（遇到市场波动时会同时亏损），从而调整策略组合，达到分散风险的目的，避免"把鸡蛋放在同一个篮子里"。

---

## 插件 — 扩展模块管理

### 功能概述

管理系统的插件（Plugin），查看当前已注册的扩展模块，并支持热更新（不重启服务的情况下重新加载最新代码）。

### 数据来源

- **插件列表**：`GET /api/plugins`，返回所有已注册插件的名称和类型。
- **热加载**：`POST /api/plugins/reload`，指定模块路径后，系统动态重新导入该模块并注册新的钩子（hook，即在特定事件发生时自动执行的函数）。
- 后端模块：`backend/src/quantpilot/plugins/`，基于 `pluggy` 库实现，支持三类钩子：`on_bar`（新价格到来时）、`on_signal`（信号发出时）、`on_alert`（告警触发时）。
- 前端组件：`frontend/src/components/PluginPanel.tsx`

### 使用目的

开发者可以将自定义逻辑写成插件（如"收到新价格时自动发 Telegram 通知"），在不重启后端服务的情况下动态加载生效，方便快速迭代和调试扩展功能。

---

## ML — 机器学习策略

### 功能概述

使用机器学习模型（LightGBM，一种基于决策树的高效分类/回归模型）训练价格方向预测器，并对新数据进行预测（买入/持有/卖出信号）。

### 数据来源

- **模型列表**：`GET /api/ml/models`，读取本地保存的模型文件（`data/ml_models/` 目录）。
- **训练**：`POST /api/ml/train`，用户提供 K 线数据（JSON 格式），后端提取特征（如价格变化率、动量、波动率、均线比例等）并训练 LightGBM 分类器，将模型保存到本地。
- **预测**：`POST /api/ml/predict`，对新一批数据运行已训练的模型，输出每根 K 线对应的信号（+1 买入、0 持有、-1 卖出）。
- 后端模块：`backend/src/quantpilot/ml/`（`features.py` 特征工程、`strategy.py` 模型封装、`registry.py` 模型管理）。
- 前端组件：`frontend/src/components/MLStrategyPanel.tsx`

### 使用目的

相比规则写死的传统策略，ML 策略从历史数据中自动学习规律。用户无需手动设计指标组合，只需提供足够的历史数据，模型会尝试捕捉价格方向的统计规律，适合探索非线性、复杂的市场模式。

---

## 情绪 — 新闻情绪分析

### 功能概述

抓取指定股票的相关新闻标题，用情绪分析算法（VADER，基于词典的规则方法）为每条新闻打分，判断当前市场对该股票的整体情绪是乐观还是悲观。

> **情绪分数（Compound Score）**：综合正面/负面/中性词汇的加权分数，范围 -1（极度负面）到 +1（极度正面）。

### 数据来源

- **新闻 + 情绪**：`GET /api/sentiment/news?symbol=AAPL&max_items=10`，后端通过 Yahoo Finance RSS 订阅拉取最新标题，用 `vaderSentiment` 库打分后返回。
- 后端模块：`backend/src/quantpilot/sentiment/provider.py`（`NewsSentimentProvider`）。
- 前端组件：`frontend/src/components/SentimentPanel.tsx`

### 使用目的

在查看价格走势之外，了解市场当前对某支股票"感觉如何"。如果价格下跌但新闻情绪偏正面，可能是短期恐慌性抛售；如果价格上涨但情绪偏负面，可能存在风险。情绪指标与价格走势结合使用，辅助判断趋势是否可持续。

---

## 信号 — 交易信号广播

### 功能概述

发布和查看交易信号（即策略或用户手动发出的"现在应该买入/卖出"指令），所有信号持久化存储，支持按股票代码过滤查看历史信号。

### 数据来源

- **发布信号**：`POST /api/signals/publish`，将信号（来源、股票代码、动作、价格、置信度、原因）写入本地 SQLite 数据库，并同步推送到 Redis pub/sub 频道（格式：`signals:{symbol}`），供实时订阅者接收。
- **信号列表**：`GET /api/signals/feed?symbol=AAPL`，从 SQLite 读取历史信号。
- 后端模块：`backend/src/quantpilot/signals/broadcaster.py`、`backend/src/quantpilot/api/signals.py`。
- 前端组件：`frontend/src/components/SignalsPanel.tsx`

### 使用目的

在策略系统和实际操作之间建立一个信号层，所有买卖建议统一在此记录和查阅。策略可以自动发布信号，用户也可以手动记录决策理由，方便事后复盘"当时为什么做出这个操作"。

---

## 实时 — WebSocket 实时推送

### 功能概述

通过 WebSocket 长连接（一种保持持续通信的网络协议）实时接收最新 K 线数据和交易信号推送，数据到达时立即在界面上显示，无需手动刷新。

### 数据来源

- **实时行情**：`WebSocket /ws/bars/{symbol}/{timeframe}`，后端订阅 Redis pub/sub 频道 `bars:{symbol}:{timeframe}`，有新 K 线时转发给前端。行情由数据调度器（`backend/src/quantpilot/data/scheduler.py`）在定时拉取数据后发布。
- **实时信号**：`WebSocket /ws/signals`，订阅 Redis 频道 `signals:*`（通配符，接收所有股票的信号），有新信号发布时立即转发。
- 后端模块：`backend/src/quantpilot/api/ws.py`、`backend/src/quantpilot/redis/pubsub.py`。
- 前端组件：`frontend/src/components/LiveDataPanel.tsx`（内置 `useWebSocket<T>` 自定义 Hook，自动管理连接生命周期）。

### 使用目的

需要监控实时行情或等待策略信号时使用。相比每隔几秒手动刷新页面，WebSocket 连接让数据"主动推送"到界面，延迟更低，也更省网络资源。连接状态（connected / connecting / error）实时显示，方便判断数据链路是否正常。

---

*文档生成时间：2026-04-09 | QuantPilot v0.1.0*
