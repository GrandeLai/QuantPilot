# Task phaseA.pr-2-schemas-codegen: Schema 单源 + Codegen 流水线

**Phase**: A
**Status**: passed
**Implementation PR**: commit `801dbfa`
**Acceptance**: [docs/acceptance/phaseA/pr-2-schemas-codegen.md](../../acceptance/phaseA/pr-2-schemas-codegen.md) — ✅ PASS (2026-04-27)
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 写 6 个核心 schema 到 `common/schemas/`：
  - `ohlcv.schema.json`：K 线
  - `symbol.schema.json`：标的元信息
  - `factor.schema.json`：因子计算结果
  - `signal.schema.json`：信号
  - `backtest_config.schema.json`：回测配置
  - `backtest_result.schema.json`：回测结果
- 写 `common/schemas/codegen.sh`：单源生成 Py/Rust/TS 三种类型
- 写 `common/schemas/codegen.config.yaml`（如需）：codegen 工具配置
- 跑 codegen，把生成产物提交：
  - `common/python/quantpilot_common/schemas/*.py`（datamodel-codegen → Pydantic v2）
  - `apps/quant-assistant/backend/src/schemas/*.rs`（typify）
  - `common/frontend-components/src/types/*.ts`（json-schema-to-typescript）
- 写 `common/schemas/README.md`：schema 命名规范、修改流程
- 添加 GitHub Actions：`codegen-drift-check`（跑 codegen.sh，断言 git diff 为空）

### 不做什么
- 不写 schema 之外的 Python/Rust/TS 业务代码
- 不引入 schemas 之外的依赖
- 不实现完整的 frontend-components TS 包（PR 6）
- 不创建 stock/quant 的 backend pyproject.toml（PR 3-5）

---

## 验收标准

- [ ] **AC-1**: 6 个 schema 文件存在并是合法 JSON Schema（含 `$schema`、`type`、`properties`）
- [ ] **AC-2**: `common/schemas/codegen.sh` 存在、可执行（chmod +x）
- [ ] **AC-3**: `bash common/schemas/codegen.sh` 退出码 0
- [ ] **AC-4**: 跑完 codegen 后 `git diff --exit-code` 通过（生成产物已提交且无漂移）
- [ ] **AC-5**: 生成的 Python 类型存在：`common/python/quantpilot_common/schemas/{ohlcv,symbol,factor,signal,backtest_config,backtest_result}.py`
- [ ] **AC-6**: 生成的 Rust 类型存在：`apps/quant-assistant/backend/src/schemas/mod.rs`（或单独 .rs 文件）
- [ ] **AC-7**: 生成的 TS 类型存在：`common/frontend-components/src/types/*.ts`
- [ ] **AC-8**: `apps/quant-assistant/backend/cargo check` 仍然退出码 0（生成的 Rust 类型能编译，且 Cargo.toml 有 serde 依赖）
- [ ] **AC-9**: GitHub Actions workflow `.github/workflows/codegen-drift.yml` 存在并语法合法
- [ ] **AC-10**: `common/schemas/README.md` 存在且说明 schema 命名规范

---

## 测试集合

```bash
# AC-1: 6 个 schema 是合法 JSON
for s in ohlcv symbol factor signal backtest_config backtest_result; do
  test -f "common/schemas/${s}.schema.json"
  python3 -c "import json; json.load(open('common/schemas/${s}.schema.json'))"
  python3 -c "import json; d=json.load(open('common/schemas/${s}.schema.json')); assert '\$schema' in d and 'type' in d"
done

# AC-2,3
test -x common/schemas/codegen.sh
bash common/schemas/codegen.sh

# AC-4: 重跑后无 diff
bash common/schemas/codegen.sh
git diff --exit-code

# AC-5
for s in ohlcv symbol factor signal backtest_config backtest_result; do
  test -f "common/python/quantpilot_common/schemas/${s}.py"
done

# AC-6
test -f apps/quant-assistant/backend/src/schemas/mod.rs

# AC-7
ls common/frontend-components/src/types/*.ts

# AC-8
cd apps/quant-assistant/backend && cargo check && cd ../../..

# AC-9
test -f .github/workflows/codegen-drift.yml
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/codegen-drift.yml'))"

# AC-10
test -f common/schemas/README.md
```

---

## 文件影响范围（白名单）

```
- common/schemas/**
- common/python/quantpilot_common/schemas/**
- common/python/pyproject.toml (仅添加 codegen 工具依赖)
- apps/quant-assistant/backend/src/schemas/**
- apps/quant-assistant/backend/Cargo.toml (添加 serde 等依赖)
- apps/quant-assistant/backend/src/lib.rs (注册 mod schemas; 仅 stub)
- common/frontend-components/src/types/**
- common/frontend-components/package.json (创建)
- .github/workflows/codegen-drift.yml
```

---

## 引用

- **设计来源**：plan §2、§4 PR 2
- **上游依赖**：phaseA.pr-1-skeleton
- **下游依赖**：phaseA.pr-3-common-py
