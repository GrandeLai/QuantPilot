# common/schemas

Cross-language type contracts for QuantPilot. JSON Schema is the single source of truth; Python (Pydantic v2), Rust (serde), and TypeScript types are auto-generated from these `.schema.json` files.

## Files

Each `<name>.schema.json` defines one logical record. Schemas are independent — no cross-file `$ref` (avoids tooling friction across three codegens).

Current schemas:

| File | Title | Used by |
|---|---|---|
| `ohlcv.schema.json` | `Ohlcv` | data layer, factor calc, backtest |
| `symbol.schema.json` | `Symbol` | universe, broker layer |
| `factor.schema.json` | `FactorValue` | factor pipeline |
| `signal.schema.json` | `Signal` | strategy output, backtest input |
| `backtest_config.schema.json` | `BacktestConfig` | backtest API request |
| `backtest_result.schema.json` | `BacktestResult` | backtest API response |

More will be added as Phase A → C progress (see plan §2 待定义 schema 列表).

## How codegen works

```
common/schemas/<name>.schema.json (source of truth, hand-edited)
        │
        ├─ codegen.sh + datamodel-codegen ─► common/python/quantpilot_common/schemas/<name>.py
        │                                       (Pydantic v2 BaseModel)
        │
        ├─ codegen.sh + quicktype ───────► apps/quant-assistant/backend/src/schemas/<name>.rs
        │                                       (Rust serde struct)
        │
        └─ codegen.sh + quicktype ───────► common/frontend-components/src/types/<name>.ts
                                                (TypeScript interface)
```

Aggregator files generated alongside:
- `common/python/quantpilot_common/schemas/__init__.py` — re-exports
- `apps/quant-assistant/backend/src/schemas/mod.rs` — `pub mod` declarations
- `common/frontend-components/src/types/index.ts` — `export *` lines

## How to use

### Modifying a schema

1. Edit `common/schemas/<name>.schema.json`
2. Run `./common/schemas/codegen.sh`
3. Commit both the schema **and** the regenerated artifacts

### Adding a new schema

1. Create `common/schemas/<name>.schema.json` (use existing files as template)
2. Run `./common/schemas/codegen.sh`
3. Commit schema + all generated artifacts

### CI drift guard

`.github/workflows/codegen-drift.yml` runs `codegen.sh` on every PR and asserts `git diff --exit-code` — any drift between source schemas and generated artifacts fails the build.

## Conventions

- File names: snake_case, ending in `.schema.json`
- `title` field: PascalCase, matches the generated type name (e.g., `BacktestConfig`)
- `$schema`: `http://json-schema.org/draft-07/schema#` (broadest tool compatibility)
- `$id`: `https://quantpilot.local/schemas/<base>.json`
- `additionalProperties: false` everywhere — strict shape contracts
- No `$ref` between schemas — keep each file independent
- ISO 8601 strings for timestamps (`format: "date-time"`) and dates (`format: "date"`)
- Numerical fields: `number` for floats, `integer` for ints; specify `minimum` where it makes physical sense

## Tools (one-time setup)

- Python codegen: `datamodel-code-generator` — pulled via `uv run --with` (no install required)
- Rust + TS codegen: `quicktype` — pulled via `npx --yes`

Both tools are auto-installed on first run by `codegen.sh`. No manual install steps.
