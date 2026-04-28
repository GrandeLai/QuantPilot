# Task phaseE.mypy-type-coverage: mypy 类型覆盖修复（B4）

**Phase**: Phase E (post)
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

当前 `common/python` 和 `apps/stock-assistant/backend` 运行 mypy 共有 41 个错误，主要分 4 类：

1. **codegen 生成文件** — `common/python/quantpilot_common/schemas/` 中的 `confloat()`/`conint()` 调用方式已被 Pydantic v2 弃用（但仍然运行时正确）。这些文件是 `codegen.sh` 自动生成的，不应手动修改；应通过 mypy config 排除。
2. **gitpython 无类型 stubs** — `git_manager.py` 的 `_repo()` 返回 `object`，导致下游调用报 `attr-defined`。
3. **redis-py stubs 的 `Awaitable[T] | T` 联合类型** — redis.asyncio 方法在类型存根中返回 `Awaitable[T] | T`，mypy 无法处理这种模式。
4. **真实代码 bug** — `okx_fetcher.py` 用字符串代替 `Exchange`/`AssetType` 枚举；`broker/mock.py` 持仓 dict 类型不精确。

### 做什么

1. **为 `common/python/pyproject.toml` 添加 `[tool.mypy]` 配置**：
   - 排除 codegen schemas 目录（`exclude = ["quantpilot_common/schemas/"]`）
   - 为 gitpython、futu 等缺少 stubs 的第三方库添加 per-module ignore

2. **修复 `git_manager.py`**：
   - 将 `_repo()` 返回类型从 `object` 改为 `Any`
   - 导入 `Any` from typing

3. **修复 `redis/client.py` 和 `redis/price_cache.py`**：
   - 在 `await` 有问题的 redis 调用行添加 `# type: ignore[misc]`

4. **修复 `data/fetchers/okx_fetcher.py`**：
   - 导入 `AssetType, Exchange` from `quantpilot_common.data.models`
   - 将 `exchange="OKX"` 替换为 `exchange=Exchange.OKX`
   - 将 `asset_type="crypto"` 替换为 `asset_type=AssetType.CRYPTO`

5. **修复 `apps/stock-assistant/backend/src/quantpilot_stock/broker/mock.py`**：
   - 将 `self._positions: dict[str, dict[str, object]]` 改为 `dict[str, dict[str, Any]]`
   - 导入 `Any` from typing

6. **为 `apps/stock-assistant/backend/pyproject.toml` 添加 `[tool.mypy]` 配置**：
   - 为 futu、longbridge 等无 stubs 的 SDK 添加 per-module ignore

### 不做什么

- 不修改 codegen 生成的 schemas/ 文件
- 不修改 Rust 后端
- 不修改前端

---

## 验收标准

- [ ] **AC-1**: `cd common/python && uv run --with mypy mypy quantpilot_common/ --ignore-missing-imports 2>&1 | grep "^Found"` 显示 0 errors（或 `Success: no issues found`）
- [ ] **AC-2**: `cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/ --ignore-missing-imports 2>&1 | grep "^Found"` 显示 0 errors
- [ ] **AC-3**: `cd apps/stock-assistant/backend && uv run pytest tests/` 全通过（类型修复不应引入运行时错误）
- [ ] **AC-4**: `cd common/python && uv run pytest tests/` 全通过

---

## 文件影响范围（白名单）

修改：
- `common/python/pyproject.toml`
- `common/python/quantpilot_common/strategy_persistence/git_manager.py`
- `common/python/quantpilot_common/redis/client.py`
- `common/python/quantpilot_common/redis/price_cache.py`
- `common/python/quantpilot_common/redis/order_queue.py`（如有错误）
- `common/python/quantpilot_common/data/fetchers/okx_fetcher.py`
- `apps/stock-assistant/backend/pyproject.toml`
- `apps/stock-assistant/backend/src/quantpilot_stock/broker/mock.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/broker/futu.py`（futu SDK union-attr + MappingProxyType 修复，为达到 0 errors 所需）
- `common/python/quantpilot_common/plugins/spec.py`（hookspec 方法 type: ignore[empty-body]，为达到 0 errors 所需）
