# Task F.10.3 — Whale Monitor Panel

## 功能

- ETH CEX 净流入压力评分仪表盘（0-1 渐变条）
- 信号标签：heavy_inflow / elevated_inflow / neutral / accumulation / heavy_accumulation
- 最近大额转账表格（hash truncated, from/to, ETH 金额, 方向箭头, 交易所名）
- 参数控制：hours (6/24/72h) + min_eth (50/100/500)

## 验收标准

- **AC-1**: `WhaleMonitorPanel.tsx` 存在
- **AC-2**: 导入并渲染于 `RiskReviewCenter.tsx`
- **AC-3**: 使用 `CEXInflowData` 类型 + `fetchCEXInflow` / `fetchWhaleTransfers` 函数
- **AC-4**: `client.ts` 有 `CEXInflowData`, `WhaleTransferData`, `fetchCEXInflow`, `fetchWhaleTransfers`
- **AC-5**: 前端构建无 TypeScript 错误
