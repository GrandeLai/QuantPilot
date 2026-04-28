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
| 2026-04-28 | phaseC.4.onnx | ✅ PASS — ONNX tract 推理 + Rhai ml_predict_from_dir 集成 + 精度验证全部通过 | [c4-onnx.md](phaseC/c4-onnx.md) |
| 2026-04-28 | phaseC.3.walk_forward | ✅ PASS — Walk-Forward 窗口切割 bit-identical + MA 回测链式拼接 + golden 等价验证 | [c3-walk-forward.md](phaseC/c3-walk-forward.md) |
| 2026-04-28 | phaseC.2.factor.sma | ✅ PASS — SMA/EMA 指标移植 + Rhai 注册 + golden 等价验证 | [c2-factor-sma.md](phaseC/c2-factor-sma.md) |
| 2026-04-28 | phaseC.1.rhai | ✅ PASS — Rhai DSL 引擎接入 | [c1-rhai.md](phaseC/c1-rhai.md) |
| 2026-04-28 | phaseB.mvp.backtest | ✅ PASS — **Phase B MVP 完工** | [mvp-backtest.md](phaseB/mvp-backtest.md) |
| 2026-04-27 | phaseB.mvp.healthz | ✅ PASS — **Phase B 起步** | [mvp-healthz.md](phaseB/mvp-healthz.md) |
| 2026-04-27 | phaseA.pr-7-scripts-ci-docs | ✅ PASS — **Phase A 完工** | [pr-7-scripts-ci-docs.md](phaseA/pr-7-scripts-ci-docs.md) |
| 2026-04-27 | phaseA.pr-6-frontend-split | ✅ PASS | [pr-6-frontend-split.md](phaseA/pr-6-frontend-split.md) |
| 2026-04-27 | phaseA.pr-5-quant-assistant-py | ✅ PASS | [pr-5-quant-assistant-py.md](phaseA/pr-5-quant-assistant-py.md) |
| 2026-04-27 | phaseA.pr-4-stock-assistant | ✅ PASS | [pr-4-stock-assistant.md](phaseA/pr-4-stock-assistant.md) |
| 2026-04-27 | phaseA.pr-3-common-py | ✅ PASS | [pr-3-common-py.md](phaseA/pr-3-common-py.md) |
| 2026-04-27 | phaseA.pr-2-schemas-codegen | ✅ PASS | [pr-2-schemas-codegen.md](phaseA/pr-2-schemas-codegen.md) |
| 2026-04-27 | phaseA.pr-1-skeleton | ✅ PASS | [pr-1-skeleton.md](phaseA/pr-1-skeleton.md) |
| 2026-04-27 | phaseA.pr-0-cleanup | ✅ PASS | [pr-0-cleanup.md](phaseA/pr-0-cleanup.md) |
| 2026-04-27 | phaseA.pr-minus-1-acceptance-infra | ✅ PASS | [pr-minus-1-acceptance-infra.md](phaseA/pr-minus-1-acceptance-infra.md) |
