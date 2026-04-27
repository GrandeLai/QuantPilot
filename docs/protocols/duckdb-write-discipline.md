# DuckDB Write Discipline

## 协议

`common/data-store/market.duckdb`（共享行情库）只能由 **stock-assistant** 写入。所有其他 app（包括 quant-assistant-py 和 Rust quant-assistant）只能 **read-only** 消费。

## 为什么

- DuckDB 单进程多写并发不友好；锁冲突会破坏数据
- 行情数据来源（yfinance / akshare / OKX）通过 stock-assistant 的 `quantpilot_common.data.fetchers` + `data_storage` 拉取写入
- 量化助手的 backtest / 因子计算 **只读** 历史行情；自身产出的中间数据（因子值、回测结果、信号）写入**自己的** `apps/quant-assistant-py/data/results.duckdb`（或 Rust 版的同名独立 db）

## 实施

### Stock-assistant 侧（写入方）
- `apps/stock-assistant/backend/src/quantpilot_stock/api/data.py` 路由提供数据拉取端点
- 写入路径：`common/python/quantpilot_common/data/storage.MarketDataStorage.upsert_bars()`
- DuckDB 路径：`get_settings().duckdb_path`（默认 `common/data-store/market.duckdb`）

### Quant-assistant-py 侧（只读方）
- `apps/quant-assistant-py/backend/src/quantpilot_quant/data/`（并不存在；通过 `quantpilot_common.data` 间接访问）
- **只调用** read-only 方法：`MarketDataStorage.query_bars()`、`get_symbols()`
- 自有写入：因子值、回测结果走独立 db（结构待定）

### Rust quant-assistant 侧（只读方）
- 用 `duckdb-rs` 以 read-only 模式打开 `common/data-store/market.duckdb`
- 自有写入：`apps/quant-assistant/data/results.duckdb`（Rust 独立 db）

## CI 守卫（Phase B+）

```
# .github/workflows/quant-assistant.yml 可加：
- name: assert quant-assistant doesn't write market.duckdb
  run: |
    ! grep -rE "common/data-store/market\.duckdb" apps/quant-assistant/backend/src/ | grep -v "read_only\|--readonly"
```

## 例外

- `tools/golden-generator/`（PR 7+ 起骨架）写 `common/data-store/golden/expected/` 但**只**写 `golden/` 子树，不动 `market.duckdb`
- `tools/ml-trainer/`（Phase B+）读 market.duckdb（read-only）+ 写 `common/data-store/models/<model_id>/`

## 违反时怎么办

- PR review 阶段抓住的违反，拒合 PR
- Runtime 抓住的违反（DuckDB 报锁冲突），紧急回滚违反方写入并恢复约定
