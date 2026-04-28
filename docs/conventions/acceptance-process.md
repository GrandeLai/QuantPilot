# 验收流程

QuantPilot 拆分期间所有 PR/任务必须走验收流程。本文是流程规范。

## 角色

- **implementation-agent**：负责实现的 agent（人或 Claude Code 主对话）。写代码、改文件、提 PR。
- **acceptance-agent**：定义在 `.claude/agents/acceptance-agent.md`，负责验收。不写代码，只 review + 测试 + 落档。

## 三个核心制品

| 制品 | 路径 | 谁写 | 何时写 |
|---|---|---|---|
| Task spec | `docs/tasks/<phase>/<task-id>.md` | 用户/规划者 | **PR 开工前**（这是不可妥协的） |
| 实现 | 代码 + commit + PR | implementation-agent | 实现阶段 |
| 验收记录 | `docs/acceptance/<phase>/<task-id>.md` | acceptance-agent | 验收阶段 |

## 流程

```
[1] 写 task spec（含 AC、测试命令、文件白名单）
       │
       ▼
[2] implementation-agent 实现
       │     ├─► 改代码 → 提交
       │     └─► commit message 末尾：Refs: docs/tasks/<phase>/<task-id>.md
       ▼
[3] 调 acceptance-agent，输入：task id + spec 路径 + PR diff range
       │
       ▼
[4] acceptance-agent：
       │     ├─► 加载 spec
       │     ├─► 文件影响范围检查
       │     ├─► 代码 review
       │     ├─► 跑测试集合
       │     ├─► AC 逐条核对
       │     ├─► 写 docs/acceptance/<phase>/<task-id>.md
       │     └─► 输出 VERDICT
       ▼
[5] 据 verdict 决定：
       ├─► PASS  → 用户合 PR；更新 docs/acceptance/INDEX.md
       ├─► FAIL  → implementation-agent 按报告修复 → 重走 [3]
       └─► NEEDS-REVISION → 用户决断 → 据决断回到 [1] 修 spec 或回到 [2] 修实现
```

## Task spec schema

模板：`docs/tasks/_template.md`。

必填字段：
- `Task ID`：`<phase>.<short-name>`，例如 `phaseA.pr-3-common-py`
- `Phase`：A / B / C / Step 4 / pre
- `Status`：pending / in-progress / under-acceptance / passed / blocked
- `范围`：做什么、不做什么
- `验收标准`：AC-1..N，每条**必须可验证**（避免"代码清晰"这种主观项；用"`grep -r XXX YYY` 无匹配"或"`pytest` 退出码 0"这种）
- `测试集合`：必跑命令清单 + 期望结果
- `文件影响范围`：白名单（路径模式），超出 = FAIL
- `引用`：plan §、上游/下游 task

## 验收记录 schema

```markdown
# Acceptance Report: <Task ID>

**Run at**: <ISO 8601 UTC>
**Implementation PR**: <link or commit hash>
**Diff range**: `<base>..<head>`
**Acceptance-agent invocation**: <session id 或 commit>
**Verdict**: PASS / FAIL / NEEDS-REVISION

## 文件影响范围检查
- 改动文件总数：N
- 在白名单内：N-X
- 超出白名单：X
  - `<path>`：超出原因 → 影响 verdict
（若超出 = 自动 FAIL，可省略后续）

## 验收标准核对
| AC | 状态 | 证据 |
|---|---|---|
| AC-1: <copy from spec> | ✅ PASS | `pytest` 退出码 0，223 passed |
| AC-2: <copy from spec> | ❌ FAIL | grep 发现 2 处违规 import：apps/.../foo.py:34 |
| AC-3: <copy from spec> | ⚠️ PARTIAL | 测试通过但代码 review 发现 X，建议... |

## 测试执行日志摘要
### `<command>`
- 退出码：0/N
- 关键输出：<前 20 行 + 后 20 行；中间省略>

## 代码 Review 备注
（不阻塞 PASS 的建议性发现）

## 后续动作
- 如 FAIL：列具体修复项 + 责任 agent
- 如 NEEDS-REVISION：列待用户决断的开放问题
- 如 PASS：列 PR 可合的 prerequisite（如 main 已更新需 rebase 等）
```

## 多次重跑

- 第一次：`docs/acceptance/<phase>/<task-id>.md`
- 第二次（FAIL 后修复重验）：`docs/acceptance/<phase>/<task-id>-v2.md`
- 第 N 次：`-vN.md`
- **从不覆盖**旧报告。所有报告 commit 进 git，构成审计线。

## INDEX 维护

`docs/acceptance/INDEX.md` 是所有验收记录的索引：
- 时间倒序
- 每行：`<date> | <task id> | <verdict> | <link>`
- 同一 task 多次跑只在最新行；旧行用 strikethrough

初期手动维护；如太累，可后期写 `tools/acceptance-indexer/` 自动生成。

## CI 集成（可选 / 渐进）

`.github/workflows/acceptance.yml`：
- 触发：PR open / push
- 步骤：
  1. 解析 PR description 的 `Refs: docs/tasks/...` 行
  2. 加载对应 task spec
  3. 调用 acceptance-agent（GitHub Action 调 Claude API 或 Claude Code SDK）
  4. 把 acceptance report 作为 PR comment 发布
  5. 据 verdict 设 PR check status

**渐进式**：初期可只跑 task spec 中"测试集合"那节的命令（不跑 agent），acceptance-agent 由开发者本地手动调；CI 完整集成是后续优化。

## 不变式

- **没有 task spec 不动手**
- **没有 PASS 不合 PR**
- **任务范围之外的改动 = FAIL**（不接受"顺手做了一点别的"）
- **NEEDS-REVISION 的两种原因**：(a) 实现 scope creep（需修实现）；(b) task spec 白名单遗漏必要伴随文件（需修 spec 白名单后重验）。acceptance-agent 报告中会说明属于哪种。
- **AC 是冻结契约**：写错了改 spec 而不是放宽验收
- **验收记录全 commit，永不删**
