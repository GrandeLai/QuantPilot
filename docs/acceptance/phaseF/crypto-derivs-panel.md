# Acceptance Report: phaseF.crypto-derivs-panel

**Run at**: 2026-04-28T00:00:00Z
**Implementation commit**: `ca4d6f7`
**Diff range**: `ca4d6f7^..ca4d6f7`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

---

## 文件影响范围检查

`git diff --name-only ca4d6f7^..ca4d6f7` 输出共 8 个路径：

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_derivs.py` | 允许（新建） |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | 允许（修改：注册 router） |
| `apps/stock-assistant/backend/tests/test_crypto_derivs_api.py` | 允许（新建） |
| `apps/stock-assistant/frontends/workbench/src/api/client.cryptoDerivs.test.ts` | 允许（新建） |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | 允许（修改：追加 3 个函数 + 类型） |
| `apps/stock-assistant/frontends/workbench/src/components/CryptoDerivsPanel.tsx` | 允许（新建） |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | 允许（挂载点） |
| `docs/tasks/phaseF/crypto-derivs-panel.md` | 允许（task spec 本身） |

`pyproject.toml`、`package.json` 均未出现在 diff 中（满足 AC-10 硬约束）。

**文件范围结论：全部 8 个路径均在白名单内。无违规。**

---

## 测试执行日志摘要

### 1. 后端单测（AC-5）
```
uv run pytest tests/test_crypto_derivs_api.py -v
collected 12 items
  TestSnapshotEndpoint::test_happy_path                   PASSED
  TestSnapshotEndpoint::test_default_asset_is_btc         PASSED
  TestSnapshotEndpoint::test_lowercase_asset_uppercased   PASSED
  TestSnapshotEndpoint::test_empty_asset_400              PASSED
  TestFundingStatsEndpoint::test_history_only_no_signal   PASSED
  TestFundingStatsEndpoint::test_with_current_returns_signal PASSED
  TestFundingStatsEndpoint::test_too_few_samples_400      PASSED
  TestFundingStatsEndpoint::test_invalid_threshold_422    PASSED
  TestETFFlowStatsEndpoint::test_history_only             PASSED
  TestETFFlowStatsEndpoint::test_large_inflow_signal      PASSED
  TestETFFlowStatsEndpoint::test_too_few_samples_400      PASSED
  TestETFFlowStatsEndpoint::test_signal_requires_30       PASSED
12 passed in 6.67s
EXIT: 0
```

### 2. ruff 检查（AC-6）
```
uv run --with ruff ruff check src/quantpilot_stock/api/crypto_derivs.py tests/test_crypto_derivs_api.py
All checks passed!
EXIT: 0
```

### 3. mypy 检查（AC-6）
```
uv run --with mypy mypy src/quantpilot_stock/api/crypto_derivs.py --ignore-missing-imports
Success: no issues found in 1 source file
EXIT: 0
```

### 4. 后端回归测试（AC-7）
```
uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_api.py -q
303 passed in 7.97s
EXIT: 0
```

### 5. 前端 TypeScript 类型检查（AC-8）
```
npm run type-check  →  tsc --noEmit
(no errors, no output)
EXIT: 0
```

### 6. 前端 build（AC-8）
```
npm run build  →  tsc -b && vite build
vite v8.0.10  2996 modules transformed
dist/assets/... ✓ built in 383ms
EXIT: 0
```
无 error 输出，仅 GVM shell hook 警告（与构建无关）。

### 7. 前端 client 测试（AC-9）
```
node --test --experimental-strip-types src/api/client.cryptoDerivs.test.ts
✔ fetchCryptoDerivsSnapshot posts asset to /api/crypto-derivs/snapshot (23.24ms)
✔ fetchCryptoDerivsSnapshot defaults to BTC (0.21ms)
✔ fetchFundingStats posts history + current + threshold (0.16ms)
✔ fetchETFFlowStats omits current as null when not provided (0.13ms)
✔ postCryptoDerivs surfaces FastAPI 400 detail (0.30ms)
ℹ tests 5  pass 5  fail 0
EXIT: 0
```

### 8. 无新依赖（AC-10）
```
git diff main -- apps/stock-assistant/backend/pyproject.toml apps/stock-assistant/frontends/workbench/package.json
(no output)
EXIT: 0
```

---

## AC 逐条核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 后端两个文件存在 | PASS | `crypto_derivs.py` 与 `test_crypto_derivs_api.py` 均在 diff 中新建，`test -f` 返回 0 |
| AC-2: 前端两个文件存在 | PASS | `CryptoDerivsPanel.tsx` 与 `client.cryptoDerivs.test.ts` 均在 diff 中新建，`test -f` 返回 0 |
| AC-3: router 已挂载 | PASS | `grep -q "from quantpilot_stock.api.crypto_derivs import router as crypto_derivs_router"` 返回 0；`grep -q "include_with_api_alias(crypto_derivs_router)"` 返回 0 |
| AC-4: 前端 panel 已挂载 | PASS | `grep -q "CryptoDerivsPanel"` 返回 0；在 RiskMetricsPanel 之下、PortfolioPanel 之上（行 11），符合 spec 要求 |
| AC-5: 后端单测全过 ≥ 10 用例 | PASS | 12 个用例全部 PASSED，退出码 0 |
| AC-6: ruff + mypy 全过 | PASS | ruff "All checks passed!"；mypy "no issues found in 1 source file"；均退出码 0 |
| AC-7: 后端回归无问题 | PASS | 303 passed，退出码 0 |
| AC-8: 前端 type-check + build 退出码 0 | PASS | tsc --noEmit 无错误；vite build 成功 2996 模块，退出码 0 |
| AC-9: 前端 client 测试 ≥ 4 用例全过 | PASS | 5 个用例全部 pass，退出码 0 |
| AC-10: 不引入新依赖 | PASS | `git diff main -- pyproject.toml package.json` 输出为空 |

全部 10 项 AC 均为 PASS，无 PARTIAL，无 FAIL。

---

## 代码 Review 备注

1. `crypto_derivs.py` 有模块级 docstring（含端点说明），全量 type hints，符合项目 Python 规范。
2. 三个端点分别覆盖 snapshot（async，monkeypatch 测试 fetch_aggregated_derivs）、funding-stats（同步，调 funding_percentile_stats + funding_extreme_signal）、etf-flow-stats（同步，手算 _flow_describe，不复用 funding_percentile_stats，符合 spec 语义要求）。
3. history < 30 时 funding-stats 返回 400（由 funding_percentile_stats 内部 raise ValueError 转换），etf-flow-stats 则 < 10 时 400（独立 spec），均与 spec 一致。
4. `CryptoDerivsPanel.tsx` 实现了 Asset Selector（BTC/ETH/SOL 按钮）、Live Snapshot（Refresh 触发 /snapshot，Funding rates 表 + OI 表 + Errors banner）、Funding Extreme Analyzer（textarea paste history + current 输入 + z_threshold + signal badge）三段布局，符合 spec 要求。
5. client.ts 新增 `postCryptoDerivs` 内部工厂函数 + `fetchCryptoDerivsSnapshot` / `fetchFundingStats` / `fetchETFFlowStats` 三个导出函数，类型完整（CryptoDerivsSnapshot、FundingStatsResult、ETFFlowStatsResult 等接口定义在 client.ts 中）。
6. 无跨 app import；无顺带重构；无引入新 npm/python 依赖。
7. ETF flow UI 按 spec "不做什么"正确缺省（etf-flow-stats 端点已实现，前端 UI 留单独任务）。

---

## 后续动作

PASS — PR 可合。无修复项。

**Phase F.1 full batch 1 全部完成**：风控三件套（risk-engine-core + risk-sharpe-decay + risk-var-cvar + risk-api-endpoints + risk-metrics-panel）+ 加密衍生品面板（crypto-derivs-collector + crypto-basis-engine + crypto-etf-flow + crypto-derivs-panel）共 9 个任务全部通过验收，Phase F.1 正式关闭。
