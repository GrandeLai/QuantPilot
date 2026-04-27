# quantpilot-golden (tools/golden-generator)

跨语言行为等价基准数据集生成器（Phase A skeleton）。

## Phase A 现状

仅有 CLI 骨架（`generate`、`verify-python`），未实际生成 case 输出。pyproject 注册到 uv workspace。

## Phase B+ 实现

按 plan §7 实现：
- 在 `common/data-store/golden/inputs/` 放固定输入 parquet
- 跑 `quant-assistant-py` 的 indicators / factors / walk-forward / backtest，输出到 `common/data-store/golden/expected/`
- 用作 Rust quant-assistant 实施时的对照基准（容差分级见 plan §7）
- `manifest.json` 记录每个 case 的容差 + applies_to

## 用法

```bash
# Phase A（仅打印占位）
uv run --package quantpilot-golden golden-generator generate

# Phase B+（实际生成）
uv run --package quantpilot-golden golden-generator generate --case-id indicator.sma.20.aapl
```
