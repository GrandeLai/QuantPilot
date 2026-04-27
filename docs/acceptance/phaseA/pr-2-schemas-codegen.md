# Acceptance Report: phaseA.pr-2-schemas-codegen

**Run at**: 2026-04-27T15:05:00Z
**Implementation PR/commit**: `801dbfa` — feat(schemas): add 6 core JSON Schemas + 3-language codegen pipeline
**Diff range**: `c42b4be..801dbfa`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS**

---

## 文件影响范围检查

PR 2 改动文件（32 个新增/修改）：
- `common/schemas/{6 schemas, codegen.sh, README.md}` ✅ 在白名单内
- `common/python/quantpilot_common/schemas/{6 .py + __init__.py}` ✅ 在白名单内
- `apps/quant-assistant/backend/src/schemas/{6 .rs + mod.rs}` ✅ 在白名单内
- `common/frontend-components/src/types/{6 .ts + index.ts}` ✅ 在白名单内
- `apps/quant-assistant/backend/Cargo.toml` ✅ 在白名单内（添加 serde/serde_json/chrono 依赖）
- `apps/quant-assistant/backend/src/lib.rs` ✅ 在白名单内（添加 `pub mod schemas`）
- `.github/workflows/codegen-drift.yml` ✅ 在白名单内

补充：白名单中提到的 `common/python/pyproject.toml` 本 PR 未触及——schemas 工具通过 `uv run --with` 即时拉取，不进入项目依赖；待 PR 3 创建 quantpilot_common 包时再写 pyproject.toml。

**结论**：无超出白名单的改动。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 6 schema 文件存在并是合法 JSON Schema | ✅ PASS | 6 个 `.schema.json` 全部 `python3 -c "json.load(open(f))"` 成功；都含 `$schema` 和 `type` |
| AC-2: codegen.sh 存在且可执行 | ✅ PASS | `test -x common/schemas/codegen.sh` 通过 |
| AC-3: `bash common/schemas/codegen.sh` 退出码 0 | ✅ PASS | 二次运行 exit code 0；log 26 行 |
| AC-4: 跑完 codegen 后 git diff --exit-code 通过 | ✅ PASS | 二次运行后 `git diff` 输出空，确认 codegen deterministic |
| AC-5: Python 类型存在 6 个 | ✅ PASS | `common/python/quantpilot_common/schemas/{ohlcv,symbol,factor,signal,backtest_config,backtest_result}.py` 全部存在 |
| AC-6: Rust 类型 mod.rs 存在 | ✅ PASS | `apps/quant-assistant/backend/src/schemas/mod.rs` 存在并 `pub mod` 6 个 schema |
| AC-7: TS 类型存在 | ✅ PASS | `common/frontend-components/src/types/*.ts`（7 个：6 schema + index.ts） |
| AC-8: cargo check 仍退出码 0 | ✅ PASS | `Finished dev profile in 0.11s`（增量构建） |
| AC-9: codegen-drift.yml 存在并 YAML 合法 | ✅ PASS | yaml.safe_load 解析通过；含 `jobs.drift-check` |
| AC-10: README.md 存在并有命名规范 | ✅ PASS | `common/schemas/README.md` 含"Conventions"段落，规范 file naming/title/$schema/$id |

---

## 测试执行日志摘要

```
=== AC-1: 6 schemas valid JSON ===
  ohlcv: OK
  symbol: OK
  factor: OK
  signal: OK
  backtest_config: OK
  backtest_result: OK
=== AC-2: codegen.sh executable === OK
=== AC-3: codegen.sh exit 0 ===
  exit: 0; log lines: 26
=== AC-4: no drift after re-run ===
  ✓ NO DRIFT — codegen is deterministic
=== AC-5: Python types === OK (6 files)
=== AC-6: Rust mod.rs === OK
=== AC-7: TS types === OK (7 files: 6 + index)
=== AC-8: cargo check ===
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.11s
=== AC-9: GitHub Actions YAML ===
  AC-9: OK — workflow YAML valid and structurally correct
=== AC-10: README.md === OK
```

---

## 代码 Review 备注

非阻塞性观察：

1. **Codegen 工具按需拉取，不进项目依赖**
   - Python `datamodel-code-generator` 通过 `uv run --with 'datamodel-code-generator>=0.25.0'` 临时安装到 uv 缓存
   - Rust + TS `quicktype` 通过 `npx --yes quicktype` 临时安装到 npm 缓存
   - 优势：项目根 `pyproject.toml` / `package.json` 不被 codegen 工具污染，运行时依赖更干净
   - 代价：首次或冷缓存时 codegen 慢（约几十秒）；CI 用 `astral-sh/setup-uv` + cache 即可应对

2. **Quicktype 对 `strategy_params` 的处理**
   - `backtest_config.strategy_params` schema 类型是 `object`（无 properties），quicktype 推断为 `Option<HashMap<String, Option<serde_json::Value>>>`（Rust）和 `{[k: string]: any}`（TS）
   - 这是符合预期的——strategy_params 故意是开放对象，由策略自定义；类型层面就该是 untyped map
   - quicktype 输出了一行 info 提示但未失败；忽略

3. **Datamodel-codegen 的 black/isort 弃用警告**
   - 5 行 FutureWarning："The default formatters (black, isort) will be replaced by ruff in a future version"
   - 不阻塞当前生成；未来如改 ruff，可加 `--formatters ruff_format,ruff_check` 显式指定
   - 暂不动

4. **YAML 1.1 quirk: `on:` 解析为 boolean**
   - GitHub Actions workflow 顶层 `on:` 字段在 pyyaml 中解析为 `True`（YAML 1.1 yes/no/on/off → bool）
   - GitHub 自身的 YAML 解析器 tolerant，但本地 lint 工具需要显式处理
   - 未阻塞 AC-9；记录在此

5. **Schema 风格统一性**
   - 所有 schemas 使用 draft-07，相同 `$schema` URL，相同 `$id` 域（quantpilot.local），相同的 `additionalProperties: false`
   - 命名一致：file = snake_case，title = PascalCase
   - 后续添加新 schema 时遵循 `common/schemas/README.md` 的"Conventions"段落

6. **PR 2 范围内未做但应在 PR 3 完成**
   - `common/python/quantpilot_common/__init__.py`（包根）尚未创建——目前 `schemas/__init__.py` 中的 `from quantpilot_common.schemas.<name> import *` 在没有顶层 `__init__.py` 时不能 import。PR 3 抽出 quantpilot_common 时会同时建立完整 package 结构。

---

## 后续动作

- ✅ 本 PR 可视为已合并（commit `801dbfa` 已落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步：进入 PR 3（common/python/quantpilot_common/ 抽出基础设施），见 `docs/tasks/phaseA/pr-3-common-py.md`
- PR 3 范围会建立 `quantpilot_common/__init__.py` 顶层包，使 PR 2 生成的 schemas 实际可 import；同时把现 backend 的 config/redis/platform/plugins/data 移过来
