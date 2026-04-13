# QuantPilot 富途 Provider 接入设计

> 日期：2026-04-14  
> 范围：在现有统一 broker / trading 主线中新增富途（Futu OpenAPI）provider，占住正式券商接入位；本轮不同时推进完整 OMS / 实盘风控重构。

## 1. 背景

当前 QuantPilot 的交易执行层已经收编为：

- 股票/通用交易统一走 `/api/trading/*`
- provider 层已有 `longbridge / mock / auto`
- 加密执行继续走 OKX 专用链路

这让系统已经有了一条正式的统一交易主线，但在 `DESIGN.md` 中仍有一个明确未完成项：

- **富途待接入**

因此，下一步最自然的增量不是继续扩张 UI，而是在现有 broker 架构里新增一个与 `longbridge` 平级的 `futu` provider，让券商接入真正形成多 provider 结构。

## 2. 目标

本轮目标只有三个：

1. 在 broker 主线中新增 `futu` provider
2. 让 `/api/trading/status` 能正确暴露 `futu` 的状态与能力边界
3. 保持现有 `longbridge / mock / okx` 链路不回退

## 3. 非目标

本轮不做这些事：

- 不实现完整 OMS
- 不实现更复杂的订单状态机重构
- 不把富途与长桥抽成新的超级抽象层
- 不把加密执行链路并入统一 trading API
- 不在这一轮开放新的前端富途专属页面

## 4. 方案比较

### 方案 A：先做富途 provider（推荐）

直接在现有 broker 主线下新增：

- `FutuTradingProvider`
- `trading_provider=futu`
- `auto` 模式下的 provider 选择扩展
- 对应测试与状态暴露

优点：

- 范围最清晰
- 与当前架构最一致
- 为后续 OMS / 风控扩展打下 provider 基础

缺点：

- 本轮不会显著改变运行中心 UI

### 方案 B：先做 OMS / 风控，再接富途

优点：

- 执行域更完整

缺点：

- 在 provider 还没占位时，投入产出比偏低
- 会把本轮范围拉大

### 方案 C：同时做富途 + OMS

优点：

- 一步到位

缺点：

- 范围和风险都明显过大

## 5. 最终选择

采用 **方案 A：先做富途 provider**。

原因：

- 这是当前系统最自然的下一个增量点；
- 它与已收编的 unified trading 主线完全同向；
- 它能在不扰乱现有交易面板的情况下补上正式券商接入能力；
- 它为之后做完整 OMS / 实盘风控预留清晰接入点。

## 6. 设计边界

### 6.1 后端

本轮新增或修改：

- `backend/src/quantpilot/broker/futu.py`
- `backend/src/quantpilot/broker/provider.py`
- `backend/src/quantpilot/broker/__init__.py`
- `backend/src/quantpilot/config.py`
- `backend/src/quantpilot/api/trading.py`（如需补 provider 状态字段映射）

要求：

1. `FutuTradingProvider` 对外满足现有 `TradingProvider` 协议
2. 如果本机未安装富途 SDK 或凭证不完整，应显式失败，并允许 `auto` 回退到其他 provider
3. `status` 必须暴露当前 provider、模式、configured 状态与能力边界

### 6.2 前端

本轮前端原则上不新增富途专用界面。

只要求：

1. 现有交易页能识别 `provider=futu`
2. 状态提示文案不因新增 provider 而崩坏
3. 不破坏 `longbridge / mock` 现有行为

### 6.3 配置

新增富途相关配置项，但不强制用户必须配置。

建议新增：

- `QUANTPILOT_TRADING_PROVIDER=futu`
- `QUANTPILOT_FUTU_HOST`
- `QUANTPILOT_FUTU_PORT`
- `QUANTPILOT_FUTU_MARKET`
- `QUANTPILOT_FUTU_UNLOCK_PASSWORD`（如需要）

## 7. 功能范围

富途 provider 第一阶段只覆盖统一 trading 主线需要的最小能力：

1. `get_status`
2. `search_securities`
3. `get_quotes`
4. `get_account_overview`
5. `get_positions`
6. `get_today_orders`
7. `get_history_orders`
8. `get_order_detail`
9. `estimate_order`
10. `submit_order`
11. `cancel_order`
12. `get_today_executions`
13. `get_history_executions`
14. `get_cash_flows`

如果某些富途 OpenAPI 能力在第一阶段不完整，必须通过：

- capability 字段显式说明
- 返回结构保持统一
- 错误信息可理解

## 8. 错误处理

本轮明确：

1. 富途 SDK 缺失 -> provider 初始化失败
2. 富途连接失败 -> provider 初始化失败
3. `trading_provider=futu` 但 provider 不可用 -> 明确返回错误，不静默伪装成功
4. `trading_provider=auto` -> 可按既定策略回退到 `longbridge` 或 `mock`

## 9. 测试策略

### 9.1 后端

至少补这些测试：

- `provider=futu` 时的选择逻辑
- SDK 缺失 / 配置不完整时的失败或 fallback 行为
- `status` 返回 `futu` 的能力边界
- 不回退现有 `mock / longbridge` 测试

### 9.2 前端

至少确认：

- trading client / UI 对 `provider=futu` 的状态展示不报错
- type-check 通过

## 10. 成功标准

本轮成功标准：

1. broker 主线中正式存在 `futu` provider
2. `/api/trading/status` 能正确暴露 `futu`
3. `trading_provider=futu` 与 `auto` 逻辑清晰可测
4. 现有 `longbridge / mock / okx` 不回退
5. 文档口径与代码现实一致

## 11. 风险

### 风险 1：Futu SDK 环境依赖

富途通常依赖本机 OpenD / SDK 环境，这在 CI 和本地开发中都可能不可用。

**应对方式**：第一阶段优先做 provider 协议适配与 graceful failure，不要求每台机器都能实际连通。

### 风险 2：provider 选择逻辑复杂化

provider 越多，`auto` 模式越容易变得不透明。

**应对方式**：在 `status` 中明确当前 provider 与 fallback reason，避免黑箱。

### 风险 3：提前卷入 OMS 需求

富途一接进来，很容易顺手想做更完整的执行域。

**应对方式**：严格限制本轮只做 provider 接入，不改大状态机。
