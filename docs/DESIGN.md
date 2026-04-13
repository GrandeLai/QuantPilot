# QuantPilot — 个人量化交易平台设计文档

> **文档版本**：v0.1.0  
> **创建日期**：2026-04-07  
> **最后更新**：2026-04-07  
> **作者**：赖俊金  
> **状态**：Draft  

---

## 更新日志（Changelog）

| 版本 | 日期 | 更新内容 | 作者 |
|---|---|---|---|
| v0.1.0 | 2026-04-07 | 初始版本，完成全功能规划与技术架构设计 | 赖俊金 |

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 设计原则](#2-设计原则)
- [3. 功能模块总览](#3-功能模块总览)
- [4. 模块详细设计](#4-模块详细设计)
  - [4.1 多资产私人理财助理](#41-多资产私人理财助理)
  - [4.2 量化策略管理](#42-量化策略管理)
  - [4.3 回测与模拟/实盘](#43-回测与模拟实盘)
  - [4.4 数据与可视化看盘](#44-数据与可视化看盘)
  - [4.5 策略复盘与知识管理](#45-策略复盘与知识管理)
  - [4.6 LLM 智能分析](#46-llm-智能分析)
  - [4.7 因子研究平台（Alpha Factory）](#47-因子研究平台alpha-factory)
  - [4.8 机器学习 / AI 策略模块](#48-机器学习--ai-策略模块)
  - [4.9 多策略组合与资金管理](#49-多策略组合与资金管理)
  - [4.10 实时告警与通知系统](#410-实时告警与通知系统)
  - [4.11 链上数据分析（加密货币专属）](#411-链上数据分析加密货币专属)
  - [4.12 期权专属分析模块](#412-期权专属分析模块)
  - [4.13 社交交易与信号跟单](#413-社交交易与信号跟单)
  - [4.14 数据仓库与 ETL 管道](#414-数据仓库与-etl-管道)
  - [4.15 插件与扩展生态](#415-插件与扩展生态)
  - [4.16 安全与合规](#416-安全与合规)
- [5. 技术架构设计](#5-技术架构设计)
  - [5.1 系统架构总览](#51-系统架构总览)
  - [5.2 技术栈选型](#52-技术栈选型)
  - [5.3 数据库设计](#53-数据库设计)
  - [5.4 核心模块技术方案](#54-核心模块技术方案)
  - [5.5 部署架构](#55-部署架构)
- [6. 开发路线图](#6-开发路线图)
- [7. 竞品对标分析](#7-竞品对标分析)
- [8. 关键差异化策略](#8-关键差异化策略)
- [9. 待决事项（Open Questions）](#9-待决事项open-questions)
- [10. 参考资料](#10-参考资料)

---

## 1. 项目概述

### 1.1 愿景

打造一款 **本地优先、LLM 原生、多资产覆盖** 的个人量化交易平台，兼具专业量化工具的深度和私人银行理财助理的易用性。

### 1.2 核心目标

- **全资产覆盖**：股票（A/港/美）、期货、期权、加密货币、基金/ETF、外汇、债券
- **端到端工作流**：从数据获取 → 因子研究 → 策略编写 → 回测验证 → 模拟/实盘 → 复盘总结，全链路闭环
- **LLM 深度集成**：AI 不是附加功能，而是贯穿策略生成、风险分析、复盘解读的核心能力
- **隐私与安全**：数据和策略默认本地加密存储，策略不上云、不泄露
- **可扩展性**：插件化架构，支持社区生态

### 1.3 目标用户

| 用户类型 | 典型场景 |
|---|---|
| 个人量化交易者 | 编写策略、回测、实盘交易 |
| 半量化散户投资者 | 借助 LLM 分析、指标看盘、跟单信号 |
| 加密货币交易者 | 链上分析、7×24 自动化交易 |
| 期权交易者 | 希腊字母监控、组合策略构建 |

---

## 2. 设计原则

| 编号 | 原则 | 说明 |
|---|---|---|
| P1 | **Local-First** | 核心数据与策略本地存储，云端为可选增强 |
| P2 | **LLM-Native** | LLM 贯穿全链路，非独立模块 |
| P3 | **Plugin-Driven** | 核心精简，功能通过插件扩展 |
| P4 | **Broker-Agnostic** | 券商/交易所接入层抽象化，一套策略多处运行 |
| P5 | **Data-Intensive** | 数据第一，支持 Tick 级高频到日线级低频全频谱 |
| P6 | **Knowledge-Centric** | 交易是知识积累过程，复盘和知识管理是一等公民 |

---

## 3. 功能模块总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        QuantPilot                               │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ 理财助理  │ 策略管理  │ 回测实盘  │ 可视化   │ 复盘知识  │ LLM分析  │
│ (4.1)    │ (4.2)    │ (4.3)    │ (4.4)    │ (4.5)    │ (4.6)    │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 因子研究  │ ML策略   │ 组合管理  │ 告警通知  │ 链上分析  │ 期权模块  │
│ (4.7)    │ (4.8)    │ (4.9)    │ (4.10)   │ (4.11)   │ (4.12)   │
├──────────┼──────────┼──────────┼──────────┴──────────┴──────────┤
│ 社交跟单  │ 数据ETL  │ 插件生态  │         安全与合规              │
│ (4.13)   │ (4.14)   │ (4.15)   │         (4.16)                 │
└──────────┴──────────┴──────────┴────────────────────────────────┘
```

---

## 4. 模块详细设计

### 4.1 多资产私人理财助理

**定位**：类似私人银行理财顾问，为用户提供综合资产增值建议。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 多资产覆盖 | 股票（A股/港股/美股）、期货（商品/金融）、期权（个股/ETF/指数）、加密货币（现货/合约）、基金/ETF、债券、外汇 | P0 |
| 资产配置建议 | 基于风险偏好+投资目标，给出大类资产配比（Black-Litterman / 风险平价模型） | P1 |
| 智能再平衡 | 定期或触发式检测组合偏离度，自动/手动再平衡 | P2 |
| 税务与费率计算 | 不同市场佣金、印花税、资本利得税自动纳入净收益计算 | P2 |
| 宏观经济日历 | 非农、CPI、央行利率决议、财报日等事件集成提醒 | P1 |
| 持仓全景仪表盘 | 统一展示所有资产持仓、盈亏、占比、风险敞口 | P0 |
| 收益归因分析 | 按资产类别/行业/策略维度拆解收益来源 | P2 |

#### 技术要点

- 统一资产数据模型（Asset / Position / Order 三层抽象）
- 多币种支持，汇率实时换算
- 投资组合优化器基于 `scipy.optimize` / `cvxpy`

---

### 4.2 量化策略管理

**定位**：策略的全生命周期管理，从编写到分享到归档。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 策略编辑器 | 支持 Python / Pine Script 双模式，内置代码补全、语法高亮、实时错误检查 | P0 |
| 导入/导出 | 支持 `.py`、`.json`、`.yaml`、`.pine` 等格式 | P0 |
| 版本控制 | 内置 Git 级策略版本管理，diff 对比，分支管理 | P1 |
| 策略市场/分享 | 社区分享、私密链接分享、策略加密分发（保护核心逻辑） | P2 |
| 本地加密存储 | AES-256 加密策略文件，支持备份至云端（S3/NAS/WebDAV） | P0 |
| 策略模板库 | 内置 50+ 经典策略模板（均线交叉、网格、动量、配对交易等） | P1 |
| LLM 辅助编写 | 用自然语言描述策略逻辑，LLM 自动生成代码框架 | P1 |

#### 技术要点

- 策略抽象基类（`BaseStrategy`），统一接口：`on_init`, `on_bar`, `on_tick`, `on_order`, `on_trade`
- Pine Script 通过 AST 解析转译为 Python 执行
- 策略序列化为 JSON Schema，便于版本对比

---

### 4.3 回测与模拟/实盘

**定位**：从历史验证到实盘执行的完整链路。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 高精度回测引擎 | Tick / 分钟 / 日线级回测，支持滑点、手续费、涨跌停、熔断等真实约束 | P0 |
| 多因子组合回测 | 多策略组合同时回测，计算组合夏普比、最大回撤、卡玛比等 | P1 |
| Walk-Forward 分析 | 滚动窗口前向回测，避免过拟合 | P2 |
| 参数优化 | 网格搜索 / 贝叶斯优化策略参数，输出热力图 | P1 |
| 模拟盘（Paper Trading） | 实时行情驱动虚拟交易，逻辑与实盘完全一致 | P0 |
| 券商 API 接入 | 富途 OpenAPI、长桥 OpenAPI、IB TWS、Alpaca、Binance/OKX/Bybit | P0 |
| 实盘风控 | 单笔止损、日亏损上限、持仓集中度限制、异常波动熔断、最大持仓数量 | P0 |
| 订单管理 | 限价/市价/止损/追踪止损/冰山/TWAP/VWAP 订单类型 | P1 |
| 执行报告 | 每笔交易的滑点分析、成交延迟统计 | P2 |

#### 技术要点

- 回测引擎：事件驱动架构（Event-Driven），核心循环解耦为 DataHandler → Strategy → Portfolio → ExecutionHandler
- Tick 级回测热路径考虑 Rust/C++ 实现，通过 PyO3 / pybind11 暴露给 Python
- 券商适配层（`BrokerAdapter`）抽象接口，屏蔽不同 API 差异

```python
# 券商适配器抽象
class BrokerAdapter(ABC):
    @abstractmethod
    async def connect(self) -> None: ...
    @abstractmethod
    async def submit_order(self, order: Order) -> OrderResult: ...
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool: ...
    @abstractmethod
    async def get_positions(self) -> list[Position]: ...
    @abstractmethod
    async def subscribe_market_data(self, symbols: list[str], callback: Callable) -> None: ...
```

---

### 4.4 数据与可视化看盘

**定位**：对标 TradingView 的专业看盘能力，同时具备更强的数据自定义能力。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 多数据源聚合 | Tushare、AKShare、Yahoo Finance、Binance WS、富途/长桥行情 API、CoinGecko | P0 |
| 专业 K 线图 | 1s/1m/5m/15m/1h/4h/1D/1W/1M 多周期，自由缩放、十字光标 | P0 |
| 全量技术指标 | 见下方指标分类表 | P0 |
| 自定义指标 | Python 编写自定义指标，实时叠加至图表 | P1 |
| 多图联动 | 多标的、多周期联动对比 | P1 |
| 画线工具 | 趋势线、水平线、斐波那契、矩形、通道等 | P1 |
| 深度图 / 订单簿 | 实时 Level 2 深度图（加密货币/美股） | P2 |
| 热力图 / 板块轮动 | 行业/板块涨跌热力图，资金流向可视化 | P2 |
| 多屏布局 | 自定义工作区布局，支持保存/加载 | P1 |
| 回测结果叠加 | 将回测交易信号叠加到 K 线图上 | P1 |

#### 技术指标分类表

| 分类 | 指标 |
|---|---|
| **趋势指标** | MA / EMA / WMA / DEMA / TEMA / MACD / 一目均衡表 / 抛物线 SAR / ADX / Aroon / SuperTrend |
| **震荡指标** | RSI / KDJ / CCI / Williams %R / Stochastic / MFI / ROC / Momentum |
| **成交量指标** | OBV / VWAP / A/D Line / CMF / Volume Profile / Force Index |
| **波动率指标** | 布林带 / ATR / 历史波动率 / Keltner Channel / Donchian Channel |
| **压力支撑** | 斐波那契回撤/扩展 / 枢轴点(Standard/Fibonacci/Woodie) / 通道线 |
| **形态识别** | 头肩顶/底 / 双顶/底 / 三角形 / 旗形 / 楔形（LLM 辅助识别） |

#### 技术要点

- 前端图表：TradingView Lightweight Charts（开源版）作为基础，配合 D3.js 做高级可视化
- WebSocket 实时数据推送
- Web Worker 处理指标计算，避免阻塞 UI
- 指标注册器模式，支持热加载自定义指标

---

### 4.5 策略复盘与知识管理

**定位**：交易不只是执行，知识积累才是长期 Alpha 的来源。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 自动复盘报告 | 每笔/每日/每周/每月自动生成复盘报告 | P0 |
| 关键指标仪表盘 | 胜率、盈亏比、夏普比、最大回撤、持仓时间分布、收益归因 | P0 |
| Markdown 导出 | 一键生成 `.md` 复盘文档，图表嵌入 | P0 |
| 飞书文档输出 | 飞书 Open API 自动创建文档，图文排版 | P1 |
| 交易日志 | 每笔自动记录：开仓理由、平仓理由、情绪标签、市场环境 | P1 |
| 知识图谱 | 策略 × 市场环境 × 收益的关联分析 | P3 |
| LLM 复盘助手 | AI 自动分析亏损原因、总结盈利模式、给出改进建议 | P1 |

#### 技术要点

- 报告模板引擎：Jinja2 渲染 Markdown，matplotlib/Plotly 生成图表
- 飞书 Open API：`POST /open-apis/docx/v1/documents` 创建文档，Block 粒度写入
- 交易日志存储于 SQLite，支持全文检索

---

### 4.6 LLM 智能分析

**定位**：LLM 是贯穿全平台的智能层，非独立功能。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 多模型接入 | OpenAI GPT-4o / Claude / DeepSeek / Gemini / 本地 Ollama，统一 API 层 | P0 |
| 基本面分析 | 财报解读、行业对比、管理层评估、估值模型 | P1 |
| 技术面分析 | 图表模式识别（传截图给多模态 LLM）、关键位标注 | P1 |
| 情绪面分析 | 新闻/社交媒体/链上数据情绪打分 | P2 |
| 买卖信号生成 | 综合多维度分析输出操作建议 + 置信度 | P1 |
| 对话式研究 | 自然语言提问，LLM 实时查数据、画图、回答 | P0 |
| 策略代码生成 | 描述策略逻辑 → LLM 生成可执行 Python 代码 | P1 |
| 异常解释 | 策略出现异常亏损时，LLM 自动分析归因 | P2 |
| Prompt 管理 | 预置分析 Prompt 模板库，支持自定义 | P1 |

#### 技术要点

- 统一网关层使用 LiteLLM，屏蔽不同模型 API 差异
- Function Calling / Tool Use 让 LLM 调用内部数据查询接口
- 上下文管理：RAG 模式，将相关行情数据 + 策略逻辑注入 Context
- 流式输出（SSE）提升交互体验

```python
# LLM 网关抽象
class LLMGateway:
    def __init__(self, config: LLMConfig):
        self.client = litellm  # 统一路由

    async def analyze(self, prompt: str, context: AnalysisContext,
                      model: str = "gpt-4o", stream: bool = True):
        messages = self._build_messages(prompt, context)
        response = await self.client.acompletion(
            model=model, messages=messages, stream=stream,
            tools=self._get_available_tools()
        )
        return response
```

---

### 4.7 因子研究平台（Alpha Factory）

**定位**：系统化因子挖掘与检验，参考 WorldQuant Brain / Alphalens。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 因子表达式引擎 | 自定义因子表达式（类 WorldQuant 101 Alphas），批量生成候选因子 | P2 |
| 因子检验 | IC / IR 分析、分层回测、因子衰减分析、共线性检测 | P2 |
| 因子组合优化 | 基于 ML 的因子加权、正交化处理 | P3 |
| 因子库 | 预置 200+ 经典因子，分类检索 | P2 |

#### 技术要点

- 因子表达式 DSL → AST 解析 → 向量化计算（NumPy / Polars）
- Alphalens 集成做因子绩效分析
- 因子计算结果缓存至 DuckDB

---

### 4.8 机器学习 / AI 策略模块

**定位**：让 ML/DL 策略开发门槛降到最低。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 特征工程流水线 | 自动 TA 特征 + 时序特征 + 基本面特征标准化 | P2 |
| 内置 ML 模型 | XGBoost / LightGBM / LSTM / Transformer 模板策略 | P2 |
| AutoML | 自动超参搜索（Optuna）、模型选择、时序交叉验证 | P3 |
| 模型可解释性 | SHAP / LIME 特征重要性可视化 | P3 |
| 模型注册表 | 模型版本管理、A/B 测试、自动退役 | P3 |

#### 技术要点

- 特征工程：`ta-lib` + `pandas-ta` 自动生成 200+ 技术特征
- 训练框架：scikit-learn / PyTorch / TensorFlow 按需选择
- 模型服务化：ONNX Runtime 部署推理

---

### 4.9 多策略组合与资金管理

**定位**：从"单策略"走向"策略组合"，科学化资金管理。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 策略组合管理器 | 同时运行 N 个策略，独立核算 + 统一风控 | P1 |
| 凯利公式 / 风险预算 | 动态资金分配 | P2 |
| 相关性监控 | 策略间收益相关性矩阵，避免集中暴露 | P2 |
| 策略权重调优 | 均值-方差优化、风险平价、最大分散化 | P2 |
| 策略生命周期 | 策略自动评估 → 降权 → 退役机制 | P3 |

---

### 4.10 实时告警与通知系统

**定位**：交易者不必时刻盯盘，关键事件实时推送。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 价格告警 | 突破/跌破某价位、百分比变动、成交量异动 | P0 |
| 策略信号告警 | 开仓/平仓信号实时推送 | P0 |
| 风控告警 | 达到止损线、日亏损上限、保证金不足 | P0 |
| 异常告警 | 策略异常、数据断流、API 连接异常 | P1 |
| 多渠道推送 | 飞书机器人、Telegram Bot、邮件、Webhook、桌面通知、Discord | P0 |

#### 技术要点

- 告警规则引擎：条件表达式 DSL，支持 AND/OR 组合
- 推送通道抽象层，通过配置切换渠道
- 告警去重与静默期设置，避免告警风暴

```yaml
# 告警规则示例
alert:
  name: "BTC 突破关键阻力位"
  conditions:
    - symbol: BTC/USDT
      type: price_cross_above
      value: 75000
      timeframe: 1h
  channels:
    - type: feishu_bot
      webhook: "${FEISHU_WEBHOOK_URL}"
    - type: telegram
      chat_id: "${TELEGRAM_CHAT_ID}"
  cooldown: 3600  # 静默1小时
```

---

### 4.11 链上数据分析（加密货币专属）

**定位**：加密货币独有的链上 Alpha 来源。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 链上指标 | 巨鲸钱包追踪、交易所净流入/出、NUPL、SOPR、MVRV | P2 |
| DeFi 数据 | TVL 变化、LP 收益追踪、清算风险监控 | P2 |
| NFT / Memecoin 监控 | 交易量、持仓集中度、Smart Money 跟踪 | P3 |
| MEV 分析 | 三明治攻击检测、Gas 费优化建议 | P3 |
| 链上与价格联动 | 链上指标与价格数据在同一图表联动展示 | P2 |

#### 技术要点

- 数据源：Glassnode API / Dune Analytics / Nansen / DefiLlama
- 链上数据索引：直接查询 RPC 或使用 The Graph subgraph

---

### 4.12 期权专属分析模块

**定位**：期权交易者的专业工具箱。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 期权定价模型 | Black-Scholes、二叉树、Monte Carlo | P2 |
| 希腊字母仪表盘 | Delta / Gamma / Theta / Vega / Rho 实时展示 | P2 |
| 波动率曲面 | IV Smile / 期限结构 3D 可视化 | P2 |
| 策略构建器 | 可视化拖拽构建 Spread / Straddle / Iron Condor 等 | P2 |
| 损益分析图 | 到期日 P&L 曲线 + 时间维度动态演变 | P2 |
| 期权链展示 | 全链行情 + Greeks 一览 | P2 |

#### 技术要点

- 定价库：`QuantLib-Python` 或自研轻量实现
- 波动率曲面：SVI 参数化拟合
- 3D 可视化：Plotly.js / Three.js

---

### 4.13 社交交易与信号跟单

**定位**：构建交易者社区，形成网络效应。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 信号发布 | 将策略信号发布为可订阅频道 | P3 |
| 跟单系统 | 一键跟随，支持倍率/止损自定义 | P3 |
| 排行榜 | 收益率、夏普比、最大回撤排名 | P3 |
| 策略评级 | 基于历史表现自动评分 | P3 |
| 社区讨论 | 策略评论、问答、经验分享 | P3 |

---

### 4.14 数据仓库与 ETL 管道

**定位**：高质量数据是量化交易的基石。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 本地时序数据库 | ClickHouse / TimescaleDB / DuckDB 存储 Tick 和 K 线 | P0 |
| 自动数据更新 | 定时任务自动拉取、清洗、入库 | P0 |
| 另类数据接入 | 卫星图像、航运数据、社交舆情、SEC Filing | P3 |
| 数据质量监控 | 缺失值检测、异常值告警、复权因子校验 | P1 |
| 数据目录 | 可视化浏览所有已有数据集、覆盖范围、更新状态 | P1 |

#### 技术要点

- 个人使用推荐 **DuckDB**（单机嵌入式，零运维）做主存储
- 大规模 Tick 数据考虑 ClickHouse / QuestDB
- ETL 调度：APScheduler / Prefect Lite
- 数据格式：Parquet 为持久化格式，Arrow 为内存格式

```
数据流水线：
  API/WebSocket → Raw JSON → 清洗/标准化 → Parquet → DuckDB/ClickHouse
                                                   ↓
                                            Redis (实时缓存)
```

---

### 4.15 插件与扩展生态

**定位**：核心精简，一切非核心功能插件化。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| 插件系统 | Python 插件热加载，自定义数据源 / 指标 / 执行器 / 告警渠道 | P1 |
| REST / WebSocket API | 对外暴露 API，供第三方调用 | P1 |
| Jupyter 集成 | 内嵌 Jupyter Notebook / Lab，研究即策略 | P1 |
| CLI 工具 | 命令行操作回测、部署策略、查看持仓 | P1 |
| 插件市场 | 社区插件发布、安装、评分 | P3 |

#### 技术要点

- 插件接口：基于 `pluggy` / `entry_points` 的 Hook 系统
- API：FastAPI 自动生成 OpenAPI 文档
- CLI：`click` / `typer` 构建

```python
# 插件 Hook 接口示例
class QuantPilotHookSpec:
    @hookspec
    def register_data_source(self) -> DataSourcePlugin: ...

    @hookspec
    def register_indicator(self) -> IndicatorPlugin: ...

    @hookspec
    def register_broker(self) -> BrokerAdapter: ...

    @hookspec
    def register_alert_channel(self) -> AlertChannel: ...
```

---

### 4.16 安全与合规

**定位**：保护策略 IP 和资金安全。

#### 功能清单

| 功能 | 描述 | 优先级 |
|---|---|---|
| API Key 加密管理 | Vault 级密钥管理，环境变量注入，不明文存储 | P0 |
| 操作审计日志 | 所有交易、配置变更、登录操作不可篡改记录 | P1 |
| 双因子认证 | TOTP / WebAuthn 保护实盘交易权限 | P1 |
| 数据加密备份 | AES-256 定时加密备份至本地 / 私有云 | P0 |
| 策略加密 | 策略代码加密存储，分享时可选混淆 | P1 |
| 网络安全 | HTTPS only / API Rate Limiting / IP 白名单 | P1 |

---

## 5. 技术架构设计

### 5.1 系统架构总览

#### 5.1.1 双前端产品形态

在 2026-04 的投资助理 MVP 迭代中，QuantPilot 明确拆分为两个面向不同工作流的前端产品：

- `frontend/`：QuantPilot 主工作台，负责研究中心、策略库、验证中心、运行中心、风险与复盘等专业量化工作流。
- `assistant_frontend/`：Investment Assistant，负责资产总览、机会池、调仓建议、风险雷达、复盘与问答等顾问式决策流程。
- `backend/`：共享平台层，统一承载行情、组合、顾问接口、策略执行与身份配置能力，对两个前端暴露一致的 API 契约。

该拆分的目标是在共享同一数据与执行平台的前提下，为专业工作台和顾问式助手分别提供更聚焦的交互入口。

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                               │
│                                                                     │
│   Tauri 2.0 (桌面壳)  +  React 18  +  TypeScript                    │
│   TradingView Lightweight Charts  |  ECharts  |  D3.js              │
│   Monaco Editor (策略编辑器)  |  xterm.js (终端)                      │
├─────────────────────────────────────────────────────────────────────┤
│                        API Gateway                                  │
│                     FastAPI (Python 3.12)                            │
│              REST + WebSocket + SSE (LLM Streaming)                 │
├──────────┬──────────┬──────────┬──────────┬─────────────────────────┤
│ 回测引擎  │ 实盘引擎  │ 因子引擎  │ ML 引擎  │    LLM Gateway          │
│          │          │          │          │                         │
│ Python + │ asyncio  │ Polars + │ PyTorch  │  LiteLLM 统一路由        │
│ Rust核心  │ Event    │ DuckDB   │ Optuna   │  OpenAI / Claude /     │
│ (PyO3)   │ Driven   │          │ ONNX RT  │  DeepSeek / Ollama     │
├──────────┴──────────┴──────────┴──────────┴─────────────────────────┤
│                        Data Layer                                   │
│                                                                     │
│   DuckDB (K线/因子)  |  Redis (实时行情缓存)  |  SQLite (配置/日志)    │
│   Parquet Files (历史数据归档)  |  本地 FS + AES (策略文件)            │
├─────────────────────────────────────────────────────────────────────┤
│                     Broker Adapter Layer                            │
│                                                                     │
│   富途  |  长桥  |  IB TWS  |  Alpaca  |  Binance  |  OKX  |  Bybit │
├─────────────────────────────────────────────────────────────────────┤
│                    Notification Layer                               │
│                                                                     │
│   飞书 Bot  |  Telegram  |  Email (SMTP)  |  Webhook  |  Discord    │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 技术栈选型

#### 5.2.1 前端

| 组件 | 选型 | 选型理由 |
|---|---|---|
| 桌面框架 | **Tauri 2.0** | Rust 内核，包体小（~5MB vs Electron ~150MB），内存占用低，安全性高 |
| 备选桌面框架 | Electron | 生态更成熟，跨平台兼容性好，如 Tauri 遇阻可退而求次 |
| UI 框架 | **React 18 + TypeScript** | 组件生态丰富，TS 类型安全 |
| 状态管理 | **Zustand** | 轻量、直观，适合中型应用 |
| 图表库 | **TradingView Lightweight Charts** | 专业金融图表，开源免费，性能优异 |
| 高级可视化 | **ECharts + D3.js** | ECharts 做仪表盘/热力图，D3 做自定义交互式图表 |
| 代码编辑器 | **Monaco Editor** | VS Code 同款引擎，原生支持 Python 语法高亮/补全 |
| 终端模拟 | **xterm.js** | 内嵌终端，支持 CLI 操作 |
| 样式方案 | **Tailwind CSS + shadcn/ui** | 原子化 CSS + 高质量组件库 |
| 3D 可视化 | **Three.js / Plotly.js** | 波动率曲面等 3D 场景 |
| 构建工具 | **Vite 6** | 极速 HMR，原生 ESM |

#### 5.2.2 后端

| 组件 | 选型 | 选型理由 |
|---|---|---|
| 主语言 | **Python 3.12** | 量化生态最丰富（NumPy/Pandas/TA-Lib/Backtrader） |
| 高性能计算 | **Rust (PyO3)** | 回测核心循环、Tick 数据处理等热路径用 Rust 加速 |
| Web 框架 | **FastAPI** | 异步原生，自动 OpenAPI 文档，WebSocket 支持 |
| 异步运行时 | **asyncio + uvicorn** | 高并发实时数据处理 |
| 任务调度 | **APScheduler / Celery Lite** | 定时数据拉取、报告生成 |
| LLM 网关 | **LiteLLM** | 统一 OpenAI/Claude/Gemini/Ollama 等 100+ 模型 API |
| 数据处理 | **Polars + NumPy** | Polars 替代 Pandas，性能提升 10-100x |
| 技术指标 | **pandas-ta / TA-Lib** | 200+ 技术指标实现 |
| 量化框架参考 | **vnpy / Backtrader / Zipline** | 参考其事件驱动架构，不直接依赖 |
| 插件系统 | **pluggy** | pytest 同款插件框架，成熟稳定 |
| CLI | **Typer** | 基于类型注解的现代 CLI 框架 |

#### 5.2.3 数据层

| 组件 | 选型 | 选型理由 | 适用场景 |
|---|---|---|---|
| 时序数据库（轻量） | **DuckDB** | 嵌入式，零运维，OLAP 查询极快，原生 Parquet 支持 | K线/因子/回测结果 |
| 时序数据库（重量） | **ClickHouse / QuestDB** | 高吞吐 Tick 数据写入和查询 | Tick 级数据（可选升级） |
| 缓存 | **Redis 7** | 实时行情、会话状态、告警状态 | 实时数据层 |
| 关系型 | **SQLite** | 嵌入式，配置/用户数据/交易日志 | 配置与审计 |
| 文件存储 | **本地 FS + AES-256** | 策略文件加密存储 | 策略管理 |
| 数据归档 | **Parquet** | 列式存储，高压缩比，Polars/DuckDB 原生支持 | 历史数据归档 |
| 密钥管理 | **keyring + python-dotenv** | OS 级密钥链 + 环境变量 | API Key 管理 |

#### 5.2.4 基础设施

| 组件 | 选型 | 选型理由 |
|---|---|---|
| 容器化 | **Docker + Docker Compose** | 本地开发与部署标准化 |
| CI/CD | **GitHub Actions** | 自动测试、构建、发布 |
| 日志 | **Loguru** | Python 最佳日志库 |
| 监控 | **Prometheus + Grafana** | 系统/策略运行监控（可选） |
| 测试 | **pytest + hypothesis** | 单元测试 + 属性测试 |
| 文档 | **MkDocs Material** | 技术文档站 |

#### 5.2.5 技术栈决策矩阵

> 以下记录重要的技术选型决策及其权衡。

| 决策点 | 方案 A | 方案 B | 最终选择 | 原因 |
|---|---|---|---|---|
| 桌面框架 | Tauri 2.0 | Electron | **Tauri** | 包体小、内存低、安全性高；Electron 做 fallback |
| 主数据库 | PostgreSQL + TimescaleDB | DuckDB | **DuckDB** | 个人项目零运维优先，嵌入式足够 |
| 数据处理 | Pandas | Polars | **Polars** | 性能 10-100x 优于 Pandas，API 更一致 |
| 回测引擎 | 纯 Python | Python + Rust | **Python + Rust** | Python 做策略层，Rust 做引擎核心循环 |
| LLM 接入 | 直连各 API | LiteLLM 统一层 | **LiteLLM** | 统一接口，模型切换零成本 |
| 前端框架 | Vue 3 | React 18 | **React** | 金融图表组件生态更丰富 |

### 5.3 数据库设计

#### 5.3.1 核心数据模型（ER 概要）

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Asset   │────<│   MarketData │     │   Strategy   │
│----------│     │--------------│     │--------------│
│ symbol   │     │ timestamp    │     │ name         │
│ type     │     │ open/high/   │     │ version      │
│ exchange │     │ low/close    │     │ code (enc)   │
│ currency │     │ volume       │     │ params       │
└──────────┘     └──────────────┘     │ status       │
      │                                └──────┬───────┘
      │          ┌──────────────┐             │
      └─────────<│   Position   │    ┌────────┴───────┐
                 │--------------│    │  BacktestRun   │
                 │ quantity     │    │----------------|
                 │ avg_price    │    │ start/end_date │
                 │ unrealized_pnl│   │ metrics (JSON) │
                 └──────────────┘    │ trades         │
                                     └────────────────┘
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │    Order     │    │    Trade     │    │  AlertRule   │
      │--------------│    │--------------│    │--------------│
      │ type         │    │ price        │    │ conditions   │
      │ side         │    │ quantity     │    │ channels     │
      │ status       │    │ commission   │    │ cooldown     │
      │ broker       │    │ slippage     │    │ status       │
      └──────────────┘    └──────────────┘    └──────────────┘
```

#### 5.3.2 存储分层策略

| 数据类型 | 存储引擎 | 保留策略 |
|---|---|---|
| Tick 数据 | Parquet 文件 + DuckDB 索引 | 按月归档，保留 3 年 |
| 分钟 K 线 | DuckDB | 保留 10 年 |
| 日线数据 | DuckDB | 永久保留 |
| 实时行情 | Redis | TTL 24h |
| 策略代码 | 本地 FS + AES | 永久，Git 版本控制 |
| 交易记录 | SQLite | 永久 |
| 回测结果 | DuckDB + Parquet | 永久 |
| 用户配置 | SQLite | 永久 |

### 5.4 核心模块技术方案

#### 5.4.1 回测引擎架构

```
                    ┌─────────────────┐
                    │   Backtest      │
                    │   Controller    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────────┐ ┌──────────┐ ┌──────────────┐
      │ DataHandler  │ │ Strategy │ │  Portfolio   │
      │              │ │          │ │              │
      │ - load_data  │ │ - on_bar │ │ - update     │
      │ - next_bar   │ │ - on_tick│ │ - calc_pnl   │
      │ - subscribe  │ │ - signals│ │ - risk_check │
      └──────┬───────┘ └─────┬────┘ └──────┬───────┘
             │               │              │
             └───────────────┼──────────────┘
                             ▼
                    ┌──────────────────┐
                    │ ExecutionHandler │
                    │                  │
                    │ - fill_order     │
                    │ - apply_slippage │
                    │ - apply_commission│
                    └──────────────────┘

核心循环（Rust 实现）:
  while data_handler.has_next():
      bar = data_handler.next()
      signals = strategy.on_bar(bar)
      orders = portfolio.process_signals(signals)
      fills = execution.execute(orders)
      portfolio.update(fills)
```

#### 5.4.2 实盘引擎架构

```
  MarketData WS ──→ EventQueue ──→ Strategy ──→ RiskManager ──→ BrokerAdapter
       ↑                                              │                │
       │                                              │ reject         │ submit
       └──────────────── Heartbeat ───────────────────┘                ▼
                                                                   Exchange
```

- EventQueue：`asyncio.Queue`，保证事件有序处理
- RiskManager：前置风控，拦截不合规订单
- 心跳检测：每 5s 检测数据源和券商连接状态

#### 5.4.3 LLM 集成架构

```
  用户输入 ──→ Intent Router ──→ Context Builder ──→ LLM Gateway ──→ Response
                    │                    │                │
                    │              ┌─────┴─────┐         │
                    │              │ RAG Engine │    ┌────┴────┐
                    │              │            │    │ LiteLLM │
                    │              │ - 行情数据  │    │         │
                    │              │ - 策略代码  │    │ GPT-4o  │
                    │              │ - 交易记录  │    │ Claude  │
                    │              │ - 新闻资讯  │    │ DeepSeek│
                    │              └────────────┘    │ Ollama  │
                    │                               └─────────┘
                    │
             ┌──────┴──────┐
             │ Tool Router │
             │             │
             │ - 查行情     │
             │ - 跑回测     │
             │ - 看持仓     │
             │ - 画图表     │
             └─────────────┘
```

### 5.5 部署架构

#### 5.5.1 个人本地部署（推荐）

```
  ┌─────────────────────────────────┐
  │         用户本机                 │
  │                                 │
  │  ┌───────────┐  ┌───────────┐  │
  │  │ Tauri App │  │ FastAPI   │  │
  │  │ (前端)     │──│ (后端)    │  │
  │  └───────────┘  └─────┬─────┘  │
  │                       │        │
  │  ┌────────┐  ┌────────┴─────┐  │
  │  │ Redis  │  │ DuckDB +    │  │
  │  │(Docker)│  │ SQLite      │  │
  │  └────────┘  └─────────────┘  │
  └─────────────────────────────────┘
          │              │
          ▼              ▼
     券商/交易所     LLM API
       API         (云端/本地)
```

#### 5.5.2 Docker Compose 一键部署

```yaml
# docker-compose.yml
version: '3.9'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./strategies:/app/strategies
    environment:
      - DATABASE_URL=duckdb:///app/data/quantpilot.duckdb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  jupyter:
    build: ./jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/app/notebooks
      - ./data:/app/data

  ollama:  # 可选：本地 LLM
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

volumes:
  redis_data:
  ollama_models:
```

#### 5.5.3 远程 VPS 部署（7×24 实盘）

对于需要 24 小时运行的实盘策略（尤其是加密货币），推荐：

- VPS：AWS Lightsail / Vultr / 搬瓦工（$5-20/月）
- OS：Ubuntu 22.04 LTS
- 部署方式：Docker Compose + Watchtower（自动更新）
- 监控：UptimeKuma 自托管监控

---

## 6. 开发路线图

### Phase 0：技术验证（2 周）

- [x] 搭建项目脚手架（Tauri + React + FastAPI）
- [x] 验证 DuckDB 性能（千万级 K 线查询 < 100ms）
- [x] 验证 Rust PyO3 回测引擎核心循环性能
- [x] 验证 TradingView Lightweight Charts 集成
- [x] 验证 LiteLLM 多模型切换

### Phase 1：MVP（P0 功能，8-12 周）

- [x] **数据模块**：AKShare/Yahoo Finance 数据拉取 + DuckDB 存储 + 定时更新
- [x] **可视化**：K 线图 + 20 个核心技术指标 + 多周期切换
- [x] **策略编辑器**：Monaco Editor + Python 策略基类 + 5 个模板策略
- [x] **回测引擎**：日线/分钟级回测 + 夏普/回撤/胜率等核心指标
- [x] **基础风控**：止损/止盈/最大持仓
- [x] **安全基础**：API Key 加密存储 + 策略文件加密

### Phase 2：可用版（P1 功能，8 周）

- [x] **模拟盘**：实时行情驱动的 Paper Trading
- [ ] **券商接入**：富途 + 长桥 + Binance API 适配器（需外部 SDK）
- [ ] **实盘交易**：完整订单管理 + 实盘风控（依赖券商接入）
- [x] **告警系统**：价格/信号/风控告警 + 飞书/Telegram 推送
- [x] **技术指标全量**：41 指标覆盖（pandas-ta）
- [x] **Markdown 复盘**：自动生成复盘报告
- [x] **策略版本管理**：Git 集成
- [x] **LLM 基础**：对话式研究 + Function Calling + SSE 流式输出

### Phase 3：好用版（P2 功能，8 周）

- [x] **LLM 深度集成**：策略代码生成（自然语言 → Python）+ AI 对话助手
- [x] **因子研究**：IC/IR 分析 + 分层回测（Spearman 相关性）
- [x] **期权模块**：Black-Scholes Greeks 仪表盘 + 隐含波动率反推
- [x] **飞书文档输出**：复盘报告自动推送飞书云文档
- [x] **多策略组合**：组合管理器 + 相关性矩阵 + 资金分配
- [x] **参数优化**：网格搜索 + Optuna 贝叶斯优化
- [x] **链上数据**：BTC 链上指标接入（blockchain.info）

### Phase 4：生态版（P3 功能，持续迭代）

- [x] **插件系统**：Hook 接口 + 热加载 + 插件市场（pluggy）
- [x] **ML 策略**：特征工程流水线 + LightGBM + 模型注册表（joblib）
- [x] **社交跟单**：信号发布 + SQLite 信号库 + 跟单订阅
- [x] **另类数据**：RSS 新闻 + VADER 情绪评分
- [x] **知识图谱**：策略 × 市场状态（牛/熊/横盘）× 收益关联分析

### 6.1 QuantPilot 工作台 IA（重构后）

顶层不再按专题能力组织，而按赚钱工作流组织：
1. 研究中心
2. 策略库
3. 验证中心
4. 运行中心
5. 风险与复盘

加密货币能力也按照同一工作流拆分：

- **研究中心**：加密现货行情与图表
- **验证中心**：加密货币策略回测
- **运行中心**：现货、永续合约、期权交易
- **风险与复盘**：加密持仓与挂单

在该工作流之下，当前加密研究栈已经扩展到：

- OKX `15m / 1h / 4h / 1d / 1w` 多时间维度数据集构建
- 核心加密因子 provider 与可扩展 provider 注册表
- BTC/ETH walk-forward 验证摘要与类别概率输出
- BTC 反转概率与证据特征
- `VWAP + EMA` 加密趋势策略模板（动态止损 + 超时离场）
- 基于现有 Optuna 引擎的加密参数搜索摘要
- 研究结果同时暴露给 QuantPilot 工作台验证中心与 Investment Assistant

---

## 7. 竞品对标分析

| 能力维度 | TradingView | QuantConnect | vnpy | Freqtrade | 3Commas | **QuantPilot** |
|---|---|---|---|---|---|---|
| 看盘可视化 | ★★★★★ | ★★☆ | ★★☆ | ★☆☆ | ★★★ | ★★★★☆ |
| 策略编写 | ★★★★ (Pine) | ★★★★★ (C#/Py) | ★★★★ (Py) | ★★★ (Py) | ★★ (GUI) | ★★★★ (Py+Pine) |
| 回测能力 | ★★★ | ★★★★★ | ★★★★ | ★★★ | ★☆☆ | ★★★★ |
| 实盘交易 | ✗ | ★★★★ | ★★★★★ | ★★★★ (Crypto) | ★★★★ | ★★★★ |
| 多资产支持 | ★★★★★ | ★★★★ | ★★★★ | ★★ (Crypto) | ★★ (Crypto) | ★★★★★ |
| LLM 集成 | ✗ | ✗ | ✗ | ✗ | ✗ | ★★★★★ |
| 本地部署 | ✗ | ✗ | ★★★★★ | ★★★★★ | ✗ | ★★★★★ |
| 复盘知识管理 | ✗ | ★★ | ✗ | ✗ | ✗ | ★★★★ |
| 链上数据 | ✗ | ✗ | ✗ | ★★ | ★★ | ★★★ |
| 期权分析 | ★★★ | ★★★★ | ★★ | ✗ | ✗ | ★★★★ |
| 费用 | $15-60/月 | $8-50/月 | 免费开源 | 免费开源 | $15-50/月 | 免费/自托管 |

---

## 8. 关键差异化策略

### 8.1 LLM-Native 而非 LLM-Attached

- **别人做的**：在旁边加个聊天窗口
- **我们做的**：LLM 贯穿策略生成 → 回测解读 → 实盘监控 → 异常归因 → 复盘总结全链路
- **具体体现**：
  - 自然语言描述策略 → 自动生成可执行代码
  - 回测报告中自动 highlight 关键问题并给出优化建议
  - 实盘异常自动分析归因并推送解释
  - 复盘报告 AI 自动撰写初稿

### 8.2 本地优先 + 隐私安全

- 策略和数据 100% 本地存储，AES-256 加密
- 可选本地 LLM（Ollama），完全离线运行
- 区别于 QuantConnect 等纯云端平台
- 解决量化交易者对策略泄露的核心焦虑

### 8.3 知识管理是一等公民

- 自动交易日志 + AI 复盘 + Markdown/飞书文档输出
- 构建个人交易知识库，长期积累 Alpha
- 策略 × 市场环境 × 收益的知识图谱（长期目标）

### 8.4 多资产统一工作台

- 股票 + 期货 + 期权 + 加密货币在一个界面内管理
- 跨资产相关性分析、组合风险监控
- 大多数工具要么做传统金融，要么做 Crypto，很少统一

---

## 9. 待决事项（Open Questions）

| # | 问题 | 状态 | 决议 | 日期 |
|---|---|---|---|---|
| Q1 | Tauri 2.0 vs Electron：Tauri 的 WebView 在 Windows 上是否足够稳定？ | 🟡 待验证 | Phase 0 技术验证决定 | - |
| Q2 | Pine Script 兼容层是否值得投入？还是纯 Python？ | 🟡 待讨论 | - | - |
| Q3 | 是否需要手机端？如果需要，React Native 还是 Flutter？ | 🟡 待讨论 | - | - |
| Q4 | 社交跟单功能是否需要后端服务器？纯 P2P 还是中心化？ | 🟡 待讨论 | - | - |
| Q5 | 初期是否直接支持 Tick 级回测，还是先做日线/分钟级？ | 🟡 待讨论 | 建议 MVP 只做日线+分钟 | - |
| Q6 | DuckDB 在高频写入场景（实盘 Tick 流）性能是否够用？ | 🟡 待验证 | Phase 0 技术验证决定 | - |

---

## 10. 参考资料

### 开源项目

- [vnpy](https://github.com/vnpy/vnpy) — Python 开源量化交易框架
- [Backtrader](https://github.com/mementum/backtrader) — Python 回测框架
- [Zipline](https://github.com/quantopian/zipline) — Quantopian 开源回测引擎
- [Freqtrade](https://github.com/freqtrade/freqtrade) — 加密货币量化交易框架
- [Jesse](https://github.com/jesse-ai/jesse) — 高级加密货币交易框架
- [QuantLib](https://github.com/lballabio/QuantLib) — 量化金融计算库
- [TradingView Lightweight Charts](https://github.com/nicehash/lightweight-charts) — 轻量金融图表

### API 文档

- [富途 OpenAPI](https://openapi.futunn.com/)
- [长桥 OpenAPI](https://open.longportapp.com/)
- [Binance API](https://binance-docs.github.io/apidocs/)
- [Interactive Brokers TWS API](https://interactivebrokers.github.io/tws-api/)
- [飞书 Open API](https://open.feishu.cn/)
- [LiteLLM](https://docs.litellm.ai/)

### 数据源

- [AKShare](https://github.com/akfamily/akshare) — A 股/期货/基金数据
- [Tushare](https://tushare.pro/) — 金融数据接口
- [Yahoo Finance](https://finance.yahoo.com/) — 全球市场数据
- [Glassnode](https://glassnode.com/) — 链上数据
- [DefiLlama](https://defillama.com/) — DeFi 数据

---

> **文档维护说明**：  
> 本文档采用 **持续迭代** 模式，每次功能变更、技术决策、路线图调整时更新对应章节并在 Changelog 中记录。  
> 建议每 2 周 Review 一次待决事项（Section 9），及时推进决策。
