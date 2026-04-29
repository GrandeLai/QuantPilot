# Phase F.10 — Crypto On-Chain Whale Monitor

## 目标

实现链上 ETH 巨鲸监控：通过 Etherscan 公共 API 检测大额 ETH 转入/转出已知中心化交易所（CEX）钱包地址，计算 CEX 净流入压力评分，提供"做空压力 / 吸筹积累"方向性信号。

盈利逻辑：大额 ETH 转入 CEX（inflow）→ 持有者准备卖出 → 价格下行压力；大额转出 CEX（outflow）→ 提至自托管 → 积累信号，历史上 24h 大额净流入极值 > 2σ 与 ETH 当日 -3% 以上相关性 ~55-60%。

## 子任务

| ID | 名称 | 文件白名单 |
|---|---|---|
| F.10.1 | crypto-whale-engine | `quantpilot_stock/crypto_whale/`, `tests/test_crypto_whale_engine.py` |
| F.10.2 | crypto-whale-api | `quantpilot_stock/api/crypto_whale.py`, `main.py`, `tests/test_crypto_whale_api.py` |
| F.10.3 | crypto-whale-panel | `frontends/workbench/src/components/WhaleMonitorPanel.tsx`, `src/api/client.ts`, `RiskReviewCenter.tsx` |

## 批次说明

F.10.1–F.10.3 在同一工作树批量开发并统一提交。
