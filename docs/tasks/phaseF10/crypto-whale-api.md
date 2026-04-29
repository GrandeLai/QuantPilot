# Task F.10.2 — Crypto Whale API

## 端点

| Method | Path | 描述 |
|---|---|---|
| GET | `/crypto-whale/eth-inflow` | ETH CEX 24h 净流入评分 |
| GET | `/crypto-whale/recent-transfers` | 最近 N 小时大额转账列表 |

## 查询参数

- `eth-inflow`: `hours` (default=24), `min_eth` (default=100)
- `recent-transfers`: `hours` (default=24), `min_eth` (default=100), `limit` (default=20, max=100)

## 响应设计

两个端点均有数据返回 200，无数据（API key 缺失或 API 失败）也返回 200（空数据/null score）——与 token_unlock 模式一致。

## 验收标准

- **AC-1**: `api/crypto_whale.py` 存在，已注册进 `main.py`
- **AC-2**: 端点数量 ≥ 2
- **AC-3**: `pytest tests/test_crypto_whale_api.py` 通过，≥ 8 个测试
- **AC-4**: mypy 无错误
