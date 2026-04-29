# Task F.10.1 — Crypto Whale Engine

## 目标
实现链上 ETH 巨鲸监控引擎：追踪大额 ETH 转入/转出已知 CEX 热钱包。

## 数据源
- **Etherscan API**: `https://api.etherscan.io/api` (free tier, 5 req/s with key)
- **API Key**: env var `ETHERSCAN_API_KEY`（未设置时返回空数据，不崩溃）
- **ETH 价格**: Binance 公共 API（已在 crypto_derivs 使用）

## 已知 CEX 热钱包
- Binance: `0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE`
- Coinbase: `0x71660c4005BA85c37ccec55d0C4493E66Fe775d3`
- Kraken: `0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2`
- OKX: `0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b`

## 核心公式

```
inflow = Σ ETH transferred TO CEX wallets (last N hours, value > min_eth)
outflow = Σ ETH transferred FROM CEX wallets (last N hours, value > min_eth)

# Net flow ratio: [-1, 1], +1 = all inflow (bearish), -1 = all outflow (bullish)
net_ratio = (inflow - outflow) / (inflow + outflow + ε)

# Pressure score [0, 1]: 1.0 = maximum inflow (bearish)
pressure_score = (net_ratio + 1) / 2
```

## 信号阈值
- `score > 0.75` → `heavy_inflow` (强烈卖压)
- `score > 0.60` → `elevated_inflow` (偏高卖压)
- `score ∈ [0.40, 0.60]` → `neutral`
- `score < 0.40` → `accumulation` (积累)
- `score < 0.25` → `heavy_accumulation` (强积累)

## 验收标准

- **AC-1**: `quantpilot_stock/crypto_whale/__init__.py` 和 `engine.py` 存在
- **AC-2**: `WhaleTransfer`, `CEXInflowData`, `compute_cex_inflow`, `_compute_pressure_score` 均在 `engine.py` 中定义
- **AC-3**: `pytest tests/test_crypto_whale_engine.py` 通过，≥12 个测试
- **AC-4**: `mypy src/quantpilot_stock/crypto_whale/` 无错误
