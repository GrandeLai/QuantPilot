# Task <task-id>: <名称>

**Phase**: A / B / C / Step 4 / pre
**Status**: pending
**Implementation PR**: <填合 PR 后的 link 或 commit hash>
**Created**: <YYYY-MM-DD>
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
（一段话或要点列表，描述本任务的实现范围）

### 不做什么
（明确边界外的事项；这部分对验收很重要——任何超出范围的改动都是 FAIL 项）

---

## 验收标准（acceptance-agent 逐条核对）

每条 AC 必须**可机械验证**——避免主观措辞如"代码清晰"。用具体命令、grep、退出码、输出包含等可断言项。

- [ ] **AC-1**: <可验证项 1>
- [ ] **AC-2**: <可验证项 2>
- [ ] **AC-3**: ...

示例：
> - [ ] **AC-1**: `cd apps/stock-assistant/backend && uv run pytest tests/ -v` 退出码 0，所有测试通过
> - [ ] **AC-2**: `! grep -r "from quantpilot_quant" apps/stock-assistant/`（没有跨 app 源码 import）
> - [ ] **AC-3**: 文件 `apps/stock-assistant/backend/pyproject.toml` 存在，含 `[project.name = "quantpilot-stock"]`

---

## 测试集合（acceptance-agent 必跑）

每条命令一行，期望结果显式说明。

```bash
# 命令 1：期望退出码 0
<command>

# 命令 2：期望输出包含 "X passed"
<command>

# 命令 3：期望返回空（grep 无匹配）
<command>
```

---

## 文件影响范围（白名单）

本任务**只允许**动这些路径下的文件，超出 = FAIL。

```
- <path-pattern-1>
- <path-pattern-2>
- ...
```

例外（默认允许的全局变更，无需在此列出）：
- `docs/acceptance/...`（验收记录由 acceptance-agent 写）

如本任务确实需要改动顶层多个目录，明确写 `**/*` 并解释理由。

---

## 引用

- **设计来源**：plan §X
- **上游依赖**（必须先完成的 task）：<task-id 或 "无">
- **下游依赖**（依赖本 task 的 task）：<task-id 或 "无">
- **相关文档**：<docs/... 或 "无">
