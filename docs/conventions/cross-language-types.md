# Cross-Language Types

## 规则

类型契约的**单一真相之源**是 `common/schemas/*.schema.json`（JSON Schema draft-07）。

Python (Pydantic v2)、Rust (serde)、TypeScript 类型都从 schema **自动生成**，不允许手写跨语言类型。

## 工作流

### 添加一个新类型
1. 在 `common/schemas/` 下创建 `<name>.schema.json`，遵循 README.md 的命名规范
2. 跑 `bash common/schemas/codegen.sh`
3. 提交 schema **和**所有生成产物（.py、.rs、.ts）

### 修改现有类型
1. 编辑 `common/schemas/<name>.schema.json`
2. 跑 `bash common/schemas/codegen.sh`
3. 检查 git diff，确认改动符合预期
4. 提交所有改动

### 不该做的事
- ❌ 在 `common/python/quantpilot_common/schemas/`、`apps/quant-assistant/backend/src/schemas/`、`common/frontend-components/src/types/` 中**手改**生成产物
- ❌ 在某一语言独立定义跨语言类型（应进 common/schemas/）
- ❌ 用 `Any` / `dict[str, object]` 绕过类型契约

## 工具链

| 语言 | 工具 | 调用 |
|---|---|---|
| Python | `datamodel-code-generator` | `uv run --with datamodel-code-generator` |
| Rust | `quicktype` | `npx --yes quicktype --lang rust` |
| TypeScript | `quicktype` | `npx --yes quicktype --lang typescript` |

## CI Drift Check

`.github/workflows/codegen-drift.yml` 在每个 PR 跑 `codegen.sh`，断言 `git diff --exit-code`。任何漂移（schema 改了但未跑 codegen，或反之）都会让 CI 失败。

## 当前 schema 集

详见 `common/schemas/README.md`。Phase A 起 6 个核心：
- ohlcv, symbol, factor, signal, backtest_config, backtest_result

Phase B+ 增加：order, position, portfolio_snapshot, strategy_spec, ml_model_meta 等。
