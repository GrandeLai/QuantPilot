# Claude Code 使用指南 — QuantPilot 项目

> 本文档教你如何在不同阶段给 Claude Code 下达精确指令，让它按照 DESIGN.md 高效执行。

---

## 一、项目初始配置

### 1.1 文件放置

```
quantpilot/
├── CLAUDE.md          ← Claude Code 自动读取的项目指令
├── docs/
│   └── DESIGN.md      ← 核心设计文档
└── ...
```

### 1.2 首次启动 Prompt

打开 Claude Code 后，发送这条指令启动项目：

```
阅读 docs/DESIGN.md 全文，这是本项目的完整设计文档。确认你理解了：
1. 项目目录结构 (Section 3)
2. 技术栈和依赖 (Section 4)
3. 编码规范 (Section 5)
4. 任务分解 (Section 10)

然后开始执行 Phase 0 的所有任务 (T-0.1 到 T-0.4)。按 Task 编号顺序逐个完成，每完成一个：
- 运行对应的验收命令确认通过
- 在 docs/DESIGN.md 中将该 Task 的 [ ] 改为 [x]
- 告诉我完成了什么，遇到了什么问题

不要跳过任何 Task，不要合并多个 Task 一起做。
```

---

## 二、按阶段执行的 Prompt 模板

### 2.1 启动某个 Phase

```
阅读 docs/DESIGN.md Section 10 中 Phase 1 的任务列表。
从第一个未完成的 Task (标记为 [ ] 的) 开始，按顺序执行。

对于每个 Task：
1. 先阅读 DESIGN.md 中对应模块的详细设计 (Section 6.x)，理解功能需求、关键接口和验收标准
2. 按照 Section 3 的目录结构创建文件
3. 实现功能代码
4. 编写单元测试 (放在 backend/tests/unit/)
5. 运行测试确认通过
6. 运行 ruff check 确认代码规范
7. 更新 DESIGN.md 中的 Task checklist

从 T-1.1 开始。
```

### 2.2 执行单个 Task（精确控制）

```
执行 docs/DESIGN.md 中的 Task T-1.3: AKShare 数据源适配器。

请按以下步骤：
1. 先阅读 Section 6.4 数据与可视化看盘 中的 DataSource 抽象接口定义
2. 创建 backend/src/quantpilot/data/sources/akshare_source.py
3. 实现 AKShareDataSource 类，继承 DataSource 基类
4. 实现 fetch_bars 方法，支持 A 股日线和分钟线，自动前复权
5. 编写测试 backend/tests/unit/test_akshare_source.py
6. 运行测试确认通过
7. 验收标准：可拉取任意 A 股标的 (如 000001.SZ) 10 年日线数据并存入 DuckDB
8. 完成后更新 DESIGN.md 将 T-1.3 标记为 [x]
```

### 2.3 实现某个完整模块

```
实现 docs/DESIGN.md Section 6.3 回测引擎模块的完整功能。

涉及的 Task: T-1.14, T-1.15, T-1.16, T-1.17
涉及的文件:
- backend/src/quantpilot/core/engine/backtest.py
- backend/src/quantpilot/core/engine/event_bus.py
- backend/src/quantpilot/core/engine/risk_manager.py
- backend/src/quantpilot/api/routes/backtest.py
- rust_core/src/backtest_loop.rs
- backend/tests/unit/test_backtest_engine.py
- backend/tests/unit/test_risk_manager.py

按 DESIGN.md 中定义的接口实现:
- BacktestEngine 类 (含 run 方法)
- RiskManager 类 (含 check_order 方法)
- BacktestResult / BacktestMetrics 数据模型

验收标准 (全部满足才算完成):
- AC-3.1: 10 年日线数据回测 < 5 秒
- AC-3.2: 夏普比、最大回撤计算与 empyrical 对照误差 < 0.01
- AC-3.3: 模拟盘与回测使用同一套 Strategy 接口
- AC-3.4: 风控拦截时订单不提交并记录原因
- AC-3.5: 支持同时运行 ≥3 个策略

逐个 Task 完成，每个完成后更新 DESIGN.md。
```

---

## 三、过程中的关键 Prompt

### 3.1 要求它严格参照文档

当你发现 Claude Code 开始"自由发挥"偏离设计文档时：

```
停。回去阅读 docs/DESIGN.md Section 6.2 中 BaseStrategy 的接口定义。
你当前实现的接口签名与文档不一致：
- 文档定义 on_bar 返回 list[Signal]，你返回了 None
- 文档定义了 StrategyContext 参数，你没有用

请严格按照文档中的接口定义重新实现。
```

### 3.2 要求编写完整测试

```
你刚完成了指标模块的实现，但没有写测试。
阅读 docs/DESIGN.md Section 11 测试策略，按照其中的测试规范：
1. 创建 backend/tests/unit/test_indicators.py
2. 为每个指标至少编写 3 个测试用例：
   - 正常情况的计算正确性
   - 边界条件 (数据长度 < 周期)
   - 空数据/异常数据
3. 使用 DESIGN.md 中的测试示例代码风格
4. 运行 pytest 确认全部通过
```

### 3.3 要求更新文档

```
你完成了 T-1.8 到 T-1.10 三个 Task，但忘了更新文档。请：
1. 在 docs/DESIGN.md Section 10 中将 T-1.8, T-1.9, T-1.10 标记为 [x]
2. 如果实现中做了任何偏离文档的决策，在 Section 4.5 技术选型决策记录中补充说明
3. 如果创建了文档中未列出的新文件，在 Section 3 目录结构中补充
```

### 3.4 遇到问题时的调试

```
T-1.15 Rust 核心循环编译失败。请：
1. 仔细阅读错误信息
2. 查看 docs/DESIGN.md Section 4.2 中的 Rust 依赖版本
3. 如果是 PyO3 版本兼容问题，先尝试修复
4. 如果无法在 3 次尝试内解决，在 DESIGN.md Section 14 待决事项中记录问题，先跳到下一个 Task
```

### 3.5 阶段性检查

```
Phase 1 应该完成了大部分 Task。请：
1. 阅读 docs/DESIGN.md Section 10 Phase 1 的所有 Task
2. 列出所有仍标记为 [ ] 的未完成 Task
3. 对每个未完成 Task 说明：原因是什么，是否有阻塞依赖
4. 运行全量测试 `cd backend && uv run pytest tests/ -v` 汇报结果
5. 运行 `ruff check` 和 `mypy` 汇报结果
```

---

## 四、高级用法

### 4.1 利用 Claude Code 的 /compact 命令

Claude Code 的上下文窗口有限。当对话很长时：

```
/compact 保留以下关键上下文：
- 当前正在执行 DESIGN.md Phase 1 T-1.14 回测引擎
- BacktestEngine 基本框架已完成，正在实现滑点模型
- 测试文件在 tests/unit/test_backtest_engine.py
```

### 4.2 利用 Headless 模式批量执行

对于相对独立的 Task，可以用 Claude Code 的非交互模式：

```bash
# 批量执行多个独立 Task
claude -p "阅读 docs/DESIGN.md，执行 T-1.3 AKShare 数据源适配器。
按 Section 6.4 的 DataSource 接口实现，含测试，完成后更新 DESIGN.md checklist。"

claude -p "阅读 docs/DESIGN.md，执行 T-1.4 Yahoo Finance 数据源适配器。
按 Section 6.4 的 DataSource 接口实现，含测试，完成后更新 DESIGN.md checklist。"
```

### 4.3 用 GitHub Issue 驱动

如果你的项目在 GitHub 上，可以创建 Issue 然后让 Claude Code 处理：

```
查看 GitHub Issue #12 "实现 Binance WebSocket 数据源"。
参考 docs/DESIGN.md Section 6.4 DataSource 接口和 T-1.5 的详细描述。
实现功能、编写测试、提交 PR。
PR 描述中引用 Issue 编号和 DESIGN.md 中的验收标准。
```

### 4.4 代码审查模式

完成一个模块后，让 Claude Code 自查：

```
请审查 backend/src/quantpilot/core/engine/ 目录下的所有代码：

对照 docs/DESIGN.md 检查：
1. 接口是否与 Section 6.3 定义一致
2. 编码规范是否符合 Section 5
3. 所有 public 函数是否有 type hints 和 docstring
4. 测试覆盖是否满足 Section 11 的要求
5. 验收标准 AC-3.1 到 AC-3.5 是否全部通过

输出审查报告，列出需要修复的问题。
```

---

## 五、常见问题处理

### 5.1 Claude Code 自作主张改结构

```
你创建了 utils/helpers.py，这不在 DESIGN.md 的目录结构中。
请删除该文件，将对应功能放到 DESIGN.md Section 3 定义的正确位置。
如果你认为需要新文件，先告诉我理由，我同意后再创建并更新文档。
```

### 5.2 Claude Code 跳过测试

```
你刚实现了 risk_manager.py 但没有编写测试。
这违反了 CLAUDE.md 中的"不要跳过测试编写"约束。
请立即为 RiskManager 编写完整测试，覆盖以下场景：
- 正常订单通过检查
- 触发单笔止损上限被拦截
- 触发日亏损上限被拦截
- 触发持仓集中度上限被拦截
- 可用资金不足被拦截
```

### 5.3 Claude Code 引入了非文档依赖

```
你在代码中 import 了 pandas，但 DESIGN.md 技术栈指定使用 Polars 替代 Pandas。
请将所有 pandas 用法改为 polars。
参考 DESIGN.md Section 4.5 的决策记录。
```

### 5.4 上下文太长导致遗忘

```
你似乎忘了项目的编码规范。请重新阅读：
1. CLAUDE.md (项目根目录)
2. docs/DESIGN.md Section 5 编码规范

然后继续完成当前 Task，注意使用 loguru 而不是 print，使用 async/await 做 I/O 操作。
```

---

## 六、推荐的每日工作流

```
# 早上：启动当天任务
"阅读 docs/DESIGN.md Section 10，告诉我当前 Phase 的进度：
已完成多少 Task，下一个要做的是哪个。然后开始执行下一个 Task。"

# 中午：检查进度
"汇报一下今天完成了哪些 Task，运行一下全量测试看看有没有回归。"

# 遇到困难时：降级处理
"这个 Task 卡住了，请在 DESIGN.md Section 14 记录问题，
标注为 🔴 阻塞，然后跳到下一个不依赖它的 Task。"

# 结束时：阶段总结
"今天的工作总结一下：
1. 列出今天完成的所有 Task
2. 运行全量测试
3. 运行 lint 和 typecheck
4. 确认 DESIGN.md 的 checklist 已更新
5. 如果有新发现的问题，追加到 Section 14"
```

---

## 七、Prompt 黄金法则

| 原则 | 好的做法 | 坏的做法 |
|---|---|---|
| **具体指向文档** | "按 DESIGN.md Section 6.3 的接口" | "实现回测引擎" |
| **明确文件路径** | "创建 backend/src/quantpilot/core/engine/backtest.py" | "写个回测文件" |
| **给出验收标准** | "10年日线回测 < 5秒" | "性能要好" |
| **要求更新文档** | "完成后更新 DESIGN.md checklist" | (不说，它就忘了) |
| **一次一个 Task** | "执行 T-1.14" | "把 Phase 1 全做了" |
| **及时纠偏** | "停，你用了 pandas，应该用 polars" | (等它写完再说就晚了) |
| **上下文提醒** | "当前在做 T-1.14 回测引擎" | (默认它记得) |
