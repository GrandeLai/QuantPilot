# quantpilot-quant (apps/quant-assistant-py/backend)

**Phase A 临时态** — Python 量化助手后端，Step 4 (Rust quant-assistant 对齐) 后**整目录删除**。

## 范围

- 数据：行情拉取（via quantpilot-common.data）
- 计算：回测引擎、因子库、ML 训练 + 推理、信号生成、walk-forward 验证、组合优化、策略加载
- LLM 投顾：advisor 路由（Phase B-C 时迁出 / 改 HTTP-based）
- API：14 quant 路由

## 启动

```bash
# From repo root
./scripts/dev-quant-py.sh
# Or directly
cd apps/quant-assistant-py/backend
uv run uvicorn quantpilot_quant.main:app --port 8002 --reload
```

## 依赖

直接依赖 `quantpilot-common`。重型 ML 依赖（scikit-learn、xgboost、lightgbm、catboost、cvxpy）只在这里出现，不在 stock-assistant。
