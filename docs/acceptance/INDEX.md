# 验收记录索引

时间倒序所有 acceptance-agent 跑出的验收报告。

## 维护规则

- 每个 task 的最新一次验收占一行
- 同一 task 历史版本（`-v2.md` 等）显示在最新版下方，**用 strikethrough 标记**
- 行格式：`<date> | <task-id> | <verdict> | <link>`
- 验收记录文件**永不删除**；INDEX 可重新生成

## 记录

| 日期 | Task ID | Verdict | 报告 |
|---|---|---|---|
| 2026-04-27 | phaseA.pr-1-skeleton | ✅ PASS | [pr-1-skeleton.md](phaseA/pr-1-skeleton.md) |
| 2026-04-27 | phaseA.pr-0-cleanup | ✅ PASS | [pr-0-cleanup.md](phaseA/pr-0-cleanup.md) |
| 2026-04-27 | phaseA.pr-minus-1-acceptance-infra | ✅ PASS | [pr-minus-1-acceptance-infra.md](phaseA/pr-minus-1-acceptance-infra.md) |
