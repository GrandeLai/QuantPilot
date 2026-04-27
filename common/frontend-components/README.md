# @quantpilot/common-frontend

跨前端共享的 TS 类型 + UI 组件 (Phase A skeleton)。

## 内容

- `src/types/`：由 `common/schemas/codegen.sh` 自动生成的 TS 类型（OHLCV、Symbol、Factor、Signal、BacktestConfig、BacktestResult），三个前端共用
- `src/chart/`：图表组件（Phase B+ 时从 stock-assistant/frontends/workbench 抽出）
- `src/ui/`：UI primitives（Phase B+ 时抽出）
- `src/api-client-base/`：API client base（Phase B+）

## 使用

```ts
// 在三个前端任何一个
import type { Ohlcv, BacktestConfig } from "@quantpilot/common-frontend/types";
```

## Phase A 现状

只有 `types/`（PR 2 codegen 已生成 + commit）。其他子模块为 Phase B+ 抽出工作；目前各前端仍在自己的 src/ 下保留本地拷贝。
