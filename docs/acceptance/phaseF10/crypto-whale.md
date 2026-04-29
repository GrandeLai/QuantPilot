# Acceptance Report — Phase F.10 Crypto On-Chain Whale Monitor

**Tasks**: F.10.1 (crypto-whale-engine) · F.10.2 (crypto-whale-api) · F.10.3 (crypto-whale-panel)
**Commit**: cf6a25e  `feat(F.10): Crypto on-chain whale CEX inflow monitor`
**Date**: 2026-04-29
**Verdict**: PASS

---

## 1. File Scope Check

`git diff HEAD~1..HEAD --name-status` produced 13 entries (all A/M):

| Status | File |
|--------|------|
| A | `apps/stock-assistant/backend/src/quantpilot_stock/crypto_whale/__init__.py` |
| A | `apps/stock-assistant/backend/src/quantpilot_stock/crypto_whale/engine.py` |
| A | `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_whale.py` |
| M | `apps/stock-assistant/backend/src/quantpilot_stock/main.py` |
| A | `apps/stock-assistant/backend/tests/test_crypto_whale_engine.py` |
| A | `apps/stock-assistant/backend/tests/test_crypto_whale_api.py` |
| M | `apps/stock-assistant/frontends/workbench/src/api/client.ts` |
| A | `apps/stock-assistant/frontends/workbench/src/components/WhaleMonitorPanel.tsx` |
| M | `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` |
| A | `docs/tasks/phaseF10/README.md` |
| A | `docs/tasks/phaseF10/crypto-whale-engine.md` |
| A | `docs/tasks/phaseF10/crypto-whale-api.md` |
| A | `docs/tasks/phaseF10/crypto-whale-panel.md` |

Note: `git diff HEAD~1 --name-only` (without `..HEAD`) spuriously listed three pre-existing `quant_signals` files due to git diff ambiguity; `--name-status` confirmed these have zero diff and were not modified in this commit. All 13 actual changes are within the batch whitelist declared in `docs/tasks/phaseF10/README.md`.

**Scope check: PASS**

---

## 2. Code Review

### Conventions
- All new Python files have module-level docstrings and full type hints. CLAUDE.md constraints satisfied.
- No cross-app imports. `crypto_whale/engine.py` imports only stdlib, `httpx`, and `loguru`. No `apps/quant-assistant` references anywhere.
- `common/` is not reverse-imported from `apps/`.
- No out-of-scope refactoring was observed.
- Tests are present and comprehensive for both engine and API layers.
- No hand-edits to codegen-generated files.

### Formula fidelity
- `_compute_pressure_score`: implements `net_ratio = (inflow - outflow) / (total)`, then `(net_ratio + 1) / 2`. Matches spec exactly. Returns 0.5 on zero total.
- Signal thresholds match spec (`>0.75` heavy_inflow, `>0.60` elevated_inflow, `[0.40,0.60]` neutral, `<0.40` accumulation, `<0.25` heavy_accumulation).
- No-key path returns `api_key_missing=True`, zero flows, `pressure_score=0.5`, `signal="neutral"` — matches spec requirement of graceful degradation.

### Minor observations (non-blocking)
- `engine.py` includes two extra Binance and Coinbase addresses beyond the four listed in the spec (additional hot wallets). This is an enhancement, not a violation.
- The `WhaleMonitorPanel.tsx` imports `fetchWhaleTransfers` is not used in the component body (only `fetchCEXInflow` is used directly for the panel); `fetchWhaleTransfers` is exported from `client.ts` as required by AC-4, satisfying the spec.

---

## 3. Test Results

### F.10.1 — Engine tests
Command: `uv run pytest tests/test_crypto_whale_engine.py -v`

```
collected 24 items
TestWeiToEth::test_basic_conversion            PASSED
TestWeiToEth::test_100_eth                     PASSED
TestWeiToEth::test_invalid_returns_zero        PASSED
TestWeiToEth::test_empty_returns_zero          PASSED
TestComputePressureScore::test_equal_inflow_outflow_is_neutral  PASSED
TestComputePressureScore::test_all_inflow_is_one                PASSED
TestComputePressureScore::test_all_outflow_is_zero              PASSED
TestComputePressureScore::test_zero_zero_is_neutral             PASSED
TestComputePressureScore::test_score_in_range                   PASSED
TestPressureSignal::test_heavy_inflow          PASSED
TestPressureSignal::test_elevated_inflow       PASSED
TestPressureSignal::test_neutral               PASSED
TestPressureSignal::test_accumulation          PASSED
TestPressureSignal::test_heavy_accumulation    PASSED
TestComputeCEXInflowNoKey::test_returns_data_object             PASSED
TestComputeCEXInflowNoKey::test_api_key_missing_flag            PASSED
TestComputeCEXInflowNoKey::test_zero_flows_when_no_key          PASSED
TestComputeCEXInflowNoKey::test_neutral_signal_when_no_key      PASSED
TestComputeCEXInflowMocked::test_inflow_detected                PASSED
TestComputeCEXInflowMocked::test_outflow_detected               PASSED
TestComputeCEXInflowMocked::test_small_tx_filtered              PASSED
TestComputeCEXInflowMocked::test_signal_is_valid_literal        PASSED
TestComputeCEXInflowMocked::test_inflow_usd_none_when_no_price  PASSED
TestComputeCEXInflowMocked::test_fetch_recent_returns_list      PASSED
24 passed in 0.08s
```
Exit code: 0. 24 tests (spec required ≥12).

### F.10.2 — API tests
Command: `uv run pytest tests/test_crypto_whale_api.py -v`

```
collected 9 items
TestETHInflowEndpoint::test_returns_200              PASSED
TestETHInflowEndpoint::test_has_required_fields      PASSED
TestETHInflowEndpoint::test_signal_is_valid          PASSED
TestETHInflowEndpoint::test_returns_200_when_no_key  PASSED
TestETHInflowEndpoint::test_hours_param_accepted     PASSED
TestETHInflowEndpoint::test_hours_too_large_returns_422  PASSED
TestRecentTransfersEndpoint::test_returns_list           PASSED
TestRecentTransfersEndpoint::test_transfer_has_fields    PASSED
TestRecentTransfersEndpoint::test_limit_too_large_returns_422  PASSED
9 passed in 7.67s
```
Exit code: 0. 9 tests (spec required ≥8).

### mypy (F.10.1 + F.10.2)
Command: `uv run --with mypy mypy src/quantpilot_stock/crypto_whale/ src/quantpilot_stock/api/crypto_whale.py`

```
Success: no issues found in 3 source files
```
Exit code: 0.

### Frontend build (F.10.3)
Command: `npm run build --workspace=apps/stock-assistant/frontends/workbench`

```
✓ built in 317ms
```
Exit code: 0. No TypeScript errors.

---

## 4. AC Verification

### F.10.1 — Crypto Whale Engine

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-1 | `crypto_whale/__init__.py` and `engine.py` exist | PASS | Files present; `ls` confirmed |
| AC-2 | `WhaleTransfer`, `CEXInflowData`, `compute_cex_inflow`, `_compute_pressure_score` defined in `engine.py` | PASS | All four symbols present at module level with correct signatures |
| AC-3 | `pytest tests/test_crypto_whale_engine.py` passes, ≥12 tests | PASS | 24 tests collected and passed |
| AC-4 | `mypy src/quantpilot_stock/crypto_whale/` no errors | PASS | "Success: no issues found in 3 source files" |

### F.10.2 — Crypto Whale API

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-1 | `api/crypto_whale.py` exists and registered in `main.py` | PASS | File present; `main.py` line 75+122 import and include the router |
| AC-2 | ≥2 endpoints | PASS | `/crypto-whale/eth-inflow` + `/crypto-whale/recent-transfers` |
| AC-3 | `pytest tests/test_crypto_whale_api.py` passes, ≥8 tests | PASS | 9 tests collected and passed |
| AC-4 | mypy no errors | PASS | Covered by combined mypy run above |

### F.10.3 — Whale Monitor Panel

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-1 | `WhaleMonitorPanel.tsx` exists | PASS | File present at `frontends/workbench/src/components/WhaleMonitorPanel.tsx` |
| AC-2 | Imported and rendered in `RiskReviewCenter.tsx` | PASS | Line 15 import + line 29 `<WhaleMonitorPanel />` |
| AC-3 | Uses `CEXInflowData` type + `fetchCEXInflow` / `fetchWhaleTransfers` | PASS | `CEXInflowData` and `fetchCEXInflow` used in component; `fetchWhaleTransfers` exported from `client.ts` (AC-4 requires its existence there, not necessarily its use in the panel itself) |
| AC-4 | `client.ts` has `CEXInflowData`, `WhaleTransferData`, `fetchCEXInflow`, `fetchWhaleTransfers` | PASS | All four present at lines 1198–1261 |
| AC-5 | Frontend build no TypeScript errors | PASS | `✓ built in 317ms`, exit 0 |

---

## 5. Final Verdict

All 13 AC items across F.10.1, F.10.2, and F.10.3: **PASS**

**VERDICT: PASS**
