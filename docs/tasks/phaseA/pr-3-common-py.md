# Task phaseA.pr-3-common-py: common/python 抽出基础设施

**Phase**: A
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 把现有 `backend/src/quantpilot/` 下的基础设施模块整体移到 `common/python/quantpilot_common/`：
  - `config.py` → `common/python/quantpilot_common/config/__init__.py`（如果只是单文件）或保持子包
  - `redis/` → `common/python/quantpilot_common/redis/`
  - `platform/` → `common/python/quantpilot_common/platform/`
  - `plugins/` → `common/python/quantpilot_common/plugins/`
  - `data/` → `common/python/quantpilot_common/data/`
- 完整保留 PR 2 已生成的 `common/python/quantpilot_common/schemas/` 不动
- 更新 `common/python/pyproject.toml`：注册 uv workspace member、声明依赖闭包（含 redis、yfinance、akshare、duckdb 等基础设施依赖）
- 在仓库根 `pyproject.toml` 的 uv workspace members 中加入 `common/python`
- 全局替换 `backend/src/quantpilot/` 中剩余代码的 import：`from quantpilot.config` → `from quantpilot_common.config` 等
- 把对应的测试（`backend/tests/test_config*.py`、`test_redis*.py`、`test_data_*.py`、`test_plugins*.py`、`test_platform*.py`）移到 `common/python/tests/`

### 不做什么
- 不动 quant 模块（backtest/factors/ml 等，PR 5）
- 不动 stock 模块（trading/portfolio/broker 等，PR 4）
- 不重构基础设施代码内部逻辑——只搬不改
- 不动前端

---

## 验收标准

- [ ] **AC-1**: 移动后 `backend/src/quantpilot/` 不再含 `config.py`、`redis/`、`platform/`、`plugins/`、`data/`（这些目录/文件已搬走）
- [ ] **AC-2**: `common/python/quantpilot_common/` 含上述模块
- [ ] **AC-3**: `common/python/pyproject.toml` 存在，含 `[project.name = "quantpilot-common"]`
- [ ] **AC-4**: `common/python/` 是根 `pyproject.toml` uv workspace 的合法 member（`uv sync` 退出码 0）
- [ ] **AC-5**: `cd backend && uv run pytest tests/ -x` 全过（现有 backend 测试在 import 替换后仍能通过）
- [ ] **AC-6**: `cd common/python && uv run pytest tests/ -x` 全过（移过来的测试还能跑）
- [ ] **AC-7**: 任何 `backend/src/quantpilot/` 中的剩余代码 import 都不再使用 `from quantpilot.config|redis|platform|plugins|data` 这种旧路径：`! grep -rE "from quantpilot\.(config|redis|platform|plugins|data)" backend/src/`
- [ ] **AC-8**: `common/python/` 中没有反向 import `apps/`：`! grep -r "from apps\." common/python/ && ! grep -r "import apps\." common/python/`

---

## 测试集合

```bash
# AC-1
! test -e backend/src/quantpilot/config.py
! test -e backend/src/quantpilot/redis
! test -e backend/src/quantpilot/platform
! test -e backend/src/quantpilot/plugins
! test -e backend/src/quantpilot/data

# AC-2
test -d common/python/quantpilot_common/redis
test -d common/python/quantpilot_common/platform
test -d common/python/quantpilot_common/plugins
test -d common/python/quantpilot_common/data
test -e common/python/quantpilot_common/config

# AC-3
test -f common/python/pyproject.toml
grep -q 'name = "quantpilot-common"' common/python/pyproject.toml

# AC-4
uv sync

# AC-5
cd backend && uv run pytest tests/ -x
cd ..

# AC-6
cd common/python && uv run pytest tests/ -x
cd ../..

# AC-7
! grep -rE "from quantpilot\.(config|redis|platform|plugins|data)" backend/src/

# AC-8
! grep -rE "from apps\.|import apps\." common/python/
```

---

## 文件影响范围（白名单）

```
- backend/src/quantpilot/config.py (删除/移动)
- backend/src/quantpilot/redis/** (移动)
- backend/src/quantpilot/platform/** (移动)
- backend/src/quantpilot/plugins/** (移动)
- backend/src/quantpilot/data/** (移动)
- backend/src/quantpilot/**/*.py (仅修改 import 行)
- backend/tests/test_{config,redis,platform,plugins,data,data_*}.py (移动)
- common/python/quantpilot_common/** (新增)
- common/python/pyproject.toml (新建)
- common/python/tests/** (新增；从 backend/tests 移过来)
- pyproject.toml (顶层；添加 workspace member)
```

---

## 引用

- **设计来源**：plan §1 模块归属表、§4 PR 3
- **上游依赖**：phaseA.pr-2-schemas-codegen
- **下游依赖**：phaseA.pr-4-stock-assistant
