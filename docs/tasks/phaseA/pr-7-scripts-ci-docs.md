# Task phaseA.pr-7-scripts-ci-docs: 启动脚本 + CI 拆分 + 文档

**Phase**: A
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 写启动脚本（详细见 plan §3）：
  - `scripts/dev-stock.sh`：infra + stock 后端 (8001) + workbench (5173) + assistant (5174)
  - `scripts/dev-quant-py.sh`：infra + quant-py 后端 (8002) + 研究前端 (5175)
  - `scripts/dev-quant.sh`：占位脚本（PR 7 时只起 `cargo run` 当前 axum healthz 服务；Phase B MVP 时填实际逻辑）
  - `scripts/infra.sh`：Redis + DuckDB 健康检查（保留并适配新路径 `common/data-store/market.duckdb`）
- 拆分 GitHub Actions（按 path filter）：
  - `.github/workflows/stock-assistant.yml`（仅 `apps/stock-assistant/**` 变更触发）
  - `.github/workflows/quant-assistant-py.yml`
  - `.github/workflows/quant-assistant.yml`（Rust）
  - `.github/workflows/common.yml`（含 codegen drift check 已在 PR 2 建立）
  - 删除老的单一 backend/frontend workflow（如有）
- 文档更新：
  - 重写 `CLAUDE.md` 反映新结构、新启动命令、验收流程引用
  - 重写 `README.md` 反映新结构 + 各 app 启动方法
  - 重写 `docs/DESIGN.md` Section 3（目录结构）
  - 新增 `docs/MIGRATION.md`：从单后端到双 app 的迁移记录（Phase A 完工时点）
  - 新增 `docs/protocols/duckdb-write-discipline.md`：stock 单写约定
  - 新增 `docs/conventions/cross-language-types.md`：schema codegen 工作流
- 起 `tools/golden-generator/` 骨架（pyproject.toml + 空 cli.py，Phase B 接入用；本 PR 不实现 case 逻辑）

### 不做什么
- 不实现完整 CI agent 集成（acceptance-agent CI 集成是后续优化，本 PR 仅设置 path filter 跑测试集合）
- 不实现 golden-generator 实际逻辑（仅骨架）
- 不动现有代码逻辑

---

## 验收标准

- [ ] **AC-1**: 4 个启动脚本存在且可执行：`scripts/{dev-stock,dev-quant,dev-quant-py,infra}.sh`，权限含 +x
- [ ] **AC-2**: `bash -n scripts/dev-stock.sh && bash -n scripts/dev-quant.sh && bash -n scripts/dev-quant-py.sh && bash -n scripts/infra.sh`（语法检查）退出码 0
- [ ] **AC-3**: 4 个 GitHub Actions workflow 存在并语法合法：`.github/workflows/{stock-assistant,quant-assistant-py,quant-assistant,common}.yml`
- [ ] **AC-4**: 每个 workflow 都用 `paths:` filter 限定触发条件
- [ ] **AC-5**: `CLAUDE.md`、`README.md`、`docs/DESIGN.md` 都被修改（diff 中有改动）
- [ ] **AC-6**: 新增文档存在：`docs/MIGRATION.md`、`docs/protocols/duckdb-write-discipline.md`、`docs/conventions/cross-language-types.md`
- [ ] **AC-7**: `tools/golden-generator/pyproject.toml` 存在且声明 `name = "quantpilot-golden"`
- [ ] **AC-8**: 端到端冒烟（命令存在性检查；不实际启动）：
  - `scripts/dev-stock.sh` 中含 `8001`、`5173`、`5174` 三个端口字面值
  - `scripts/dev-quant-py.sh` 中含 `8002`、`5175`
  - `scripts/dev-quant.sh` 中含 `cargo run`
- [ ] **AC-9**: Phase A 完工总验收（plan §8 自动化部分完整跑过）：
  - 三个 Python app 各自 pytest 全过
  - 三个前端各自 npm run build 通过
  - codegen drift check 通过
  - 隔离 grep 全部干净（两 app 互不 import；common 不反向 import apps）

---

## 测试集合

```bash
# AC-1
for s in dev-stock dev-quant dev-quant-py infra; do
  test -x "scripts/${s}.sh" || (echo "NOT EXECUTABLE: $s" && exit 1)
done

# AC-2: 语法
for s in dev-stock dev-quant dev-quant-py infra; do
  bash -n "scripts/${s}.sh"
done

# AC-3,4
for w in stock-assistant quant-assistant-py quant-assistant common; do
  test -f ".github/workflows/${w}.yml"
  python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/${w}.yml')); assert 'on' in d"
  python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/${w}.yml')); on=d['on']; assert any('paths' in v for v in (on.values() if isinstance(on, dict) else [{}]))"
done

# AC-5: 文档改动（与 main 比较）
git diff main -- CLAUDE.md README.md docs/DESIGN.md | grep -q "^[+-]" || echo "WARN: no diff visible (maybe initial PR)"

# AC-6
test -f docs/MIGRATION.md
test -f docs/protocols/duckdb-write-discipline.md
test -f docs/conventions/cross-language-types.md

# AC-7
test -f tools/golden-generator/pyproject.toml
grep -q 'name = "quantpilot-golden"' tools/golden-generator/pyproject.toml

# AC-8
grep -q "8001" scripts/dev-stock.sh
grep -q "5173" scripts/dev-stock.sh
grep -q "5174" scripts/dev-stock.sh
grep -q "8002" scripts/dev-quant-py.sh
grep -q "5175" scripts/dev-quant-py.sh
grep -q "cargo run" scripts/dev-quant.sh

# AC-9: Phase A 完工总验收
(cd apps/stock-assistant/backend && uv run pytest tests/ -x)
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -x)
(cd common/python && uv run pytest tests/ -x)
(cd common/frontend-components && npm run build)
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
bash common/schemas/codegen.sh && git diff --exit-code

! grep -rE "from quantpilot_stock|import quantpilot_stock" apps/quant-assistant-py/
! grep -rE "from quantpilot_quant|import quantpilot_quant" apps/stock-assistant/
! grep -rE "from apps\.|import apps\." common/python/
```

---

## 文件影响范围（白名单）

```
- scripts/dev-stock.sh
- scripts/dev-quant.sh
- scripts/dev-quant-py.sh
- scripts/infra.sh (修改保留)
- .github/workflows/stock-assistant.yml
- .github/workflows/quant-assistant-py.yml
- .github/workflows/quant-assistant.yml
- .github/workflows/common.yml
- .github/workflows/* (删除老的)
- CLAUDE.md
- README.md
- docs/DESIGN.md
- docs/MIGRATION.md
- docs/protocols/duckdb-write-discipline.md
- docs/conventions/cross-language-types.md
- tools/golden-generator/**
- pyproject.toml (顶层；workspace 加入 tools/golden-generator)
```

---

## 引用

- **设计来源**：plan §3、§4 PR 7、§8 Phase A 完工验证
- **上游依赖**：phaseA.pr-6-frontend-split
- **下游依赖**：进入 Phase B 的 task spec（按需后写）
