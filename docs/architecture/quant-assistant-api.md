# Quant-Assistant HTTP API Reference

Rust axum server — listens on **port 8002** by default.

Start with:
```bash
./scripts/dev-quant.sh
# or
(cd apps/quant-assistant/backend && cargo run)
```

All request/response bodies are JSON. Errors are returned as `{"error": "<message>"}` with an appropriate HTTP status code.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness check |
| POST | `/api/backtest/run` | MA crossover backtest on OHLCV bars |
| POST | `/api/walk-forward` | Walk-forward validation splits |
| POST | `/api/optimize` | Grid search over MA parameter combinations |
| POST | `/api/indicators` | SMA/EMA computation over price series |

---

## GET /healthz

Liveness check. Returns immediately with no dependencies.

### Response `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"` when the process is up |
| `service` | `string` | Service name — always `"quant-assistant"` |
| `version` | `string` | Crate version string (e.g. `"0.1.0"`) |
| `started_at` | `string` | RFC 3339 timestamp of when the health check was called |

```json
{
  "status": "ok",
  "service": "quant-assistant",
  "version": "0.1.0",
  "started_at": "2026-04-28T10:00:00Z"
}
```

### Error conditions

None. If the process is up this endpoint always returns 200.

---

## POST /api/backtest/run

Run an MA crossover backtest over a sequence of OHLCV bars. Returns equity curve and performance metrics.

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `symbol` | `string` | yes | — | Ticker symbol label (used only in response) |
| `bars` | `Bar[]` | yes | — | OHLCV bars; at minimum each bar must have `close` |
| `fast_period` | `usize` | yes | — | Fast MA window (bars) |
| `slow_period` | `usize` | yes | — | Slow MA window (bars) |
| `initial_cash` | `f64` | yes | — | Starting capital |
| `risk_free_rate` | `f64` | no | `0.0` | Annual risk-free rate for Sharpe/Sortino calculation |
| `periods_per_year` | `f64` | no | `252.0` | Annualisation factor (252 for daily, 252*6.5 for hourly) |

**Bar object**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `close` | `f64` | yes | Closing price |
| `time` | `string` | no | ISO 8601 timestamp; used to populate `start_date`/`end_date` in metrics |

### Response Body `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | `string` | Echoed from request |
| `fast_period` | `usize` | Echoed from request |
| `slow_period` | `usize` | Echoed from request |
| `bars_processed` | `usize` | Number of bars in request |
| `equity_curve` | `f64[]` | Portfolio value at each bar |
| `metrics` | `BacktestMetrics` | Performance summary (see below) |

**BacktestMetrics object**

| Field | Type | Description |
|-------|------|-------------|
| `total_return` | `f64` | Total return as a decimal (e.g. 0.15 = 15%) |
| `annual_return` | `f64` | Annualised return |
| `max_drawdown` | `f64` | Maximum peak-to-trough drawdown (positive value) |
| `volatility` | `f64` | Annualised volatility of returns |
| `sharpe_ratio` | `f64` | Sharpe ratio |
| `sortino_ratio` | `f64` | Sortino ratio (capped at 9999.0 when infinite) |
| `calmar_ratio` | `f64` | Calmar ratio (annual return / max drawdown) |
| `win_rate` | `f64` | Fraction of winning trades |
| `profit_factor` | `f64` | Gross profit / gross loss (capped at 9999.0 when infinite) |
| `total_trades` | `usize` | Total closed trades |
| `win_trades` | `usize` | Number of profitable trades |
| `loss_trades` | `usize` | Number of losing trades |
| `avg_win` | `f64` | Average gain per winning trade |
| `avg_loss` | `f64` | Average loss per losing trade |
| `initial_cash` | `f64` | Starting capital echoed |
| `final_value` | `f64` | Portfolio value at last bar |
| `start_date` | `string \| null` | ISO 8601 timestamp of first bar (if `time` provided) |
| `end_date` | `string \| null` | ISO 8601 timestamp of last bar (if `time` provided) |
| `trading_days` | `usize` | Total number of bars processed |

### Example

```bash
curl -s -X POST http://localhost:8002/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "bars": [
      {"close": 150.0, "time": "2024-01-02"},
      {"close": 152.0, "time": "2024-01-03"},
      {"close": 155.0, "time": "2024-01-04"},
      {"close": 153.0, "time": "2024-01-05"},
      {"close": 157.0, "time": "2024-01-08"},
      {"close": 160.0, "time": "2024-01-09"},
      {"close": 158.0, "time": "2024-01-10"},
      {"close": 162.0, "time": "2024-01-11"}
    ],
    "fast_period": 3,
    "slow_period": 5,
    "initial_cash": 10000.0,
    "risk_free_rate": 0.02
  }'
```

```json
{
  "symbol": "AAPL",
  "fast_period": 3,
  "slow_period": 5,
  "bars_processed": 8,
  "equity_curve": [10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 10683.8, 10554.8, 10804.2],
  "metrics": {
    "total_return": 0.0804,
    "annual_return": 0.312,
    "max_drawdown": 0.012,
    "volatility": 0.18,
    "sharpe_ratio": 1.62,
    "sortino_ratio": 2.41,
    "calmar_ratio": 26.0,
    "win_rate": 1.0,
    "profit_factor": 9999.0,
    "total_trades": 1,
    "win_trades": 1,
    "loss_trades": 0,
    "avg_win": 804.2,
    "avg_loss": 0.0,
    "initial_cash": 10000.0,
    "final_value": 10804.2,
    "start_date": "2024-01-02",
    "end_date": "2024-01-11",
    "trading_days": 8
  }
}
```

### Error conditions

| Status | Cause |
|--------|-------|
| `400 Bad Request` | `bars` has fewer than 2 elements |
| `400 Bad Request` | `fast_period >= slow_period` or insufficient data for MA window |
| `422 Unprocessable Entity` | Missing required fields or wrong types (axum JSON deserialization error) |

---

## POST /api/walk-forward

Run walk-forward cross-validation by splitting the close price series into sequential train/test windows and running an MA crossover backtest on each test segment.

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `closes` | `f64[]` | yes | — | Close price series |
| `fast_period` | `usize` | yes | — | Fast MA window (bars) |
| `slow_period` | `usize` | yes | — | Slow MA window (bars) |
| `initial_cash` | `f64` | yes | — | Starting capital per window |
| `train_size` | `usize` | yes | — | Number of bars in each training window |
| `test_size` | `usize` | yes | — | Number of bars in each test window |
| `step_size` | `usize` | no | `1` | How many bars to advance the window each iteration |
| `embargo_size` | `usize` | no | `0` | Gap bars between train end and test start (leakage prevention) |

### Response Body `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `n_windows` | `usize` | Number of walk-forward windows produced |
| `equity_curve` | `f64[]` | Stitched equity curve across all test windows |
| `window_splits` | `WindowSplit[]` | Index ranges for each window (see below) |

**WindowSplit object**

| Field | Type | Description |
|-------|------|-------------|
| `train_start` | `usize` | Inclusive start index of training segment |
| `train_end` | `usize` | Inclusive end index of training segment |
| `test_start` | `usize` | Inclusive start index of test segment |
| `test_end` | `usize` | Inclusive end index of test segment |

### Example

```bash
curl -s -X POST http://localhost:8002/api/walk-forward \
  -H "Content-Type: application/json" \
  -d '{
    "closes": [100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120],
    "fast_period": 3,
    "slow_period": 7,
    "initial_cash": 10000.0,
    "train_size": 10,
    "test_size": 5,
    "step_size": 5
  }'
```

```json
{
  "n_windows": 2,
  "equity_curve": [10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 10000.0],
  "window_splits": [
    {"train_start": 0, "train_end": 10, "test_start": 10, "test_end": 15},
    {"train_start": 5, "train_end": 15, "test_start": 15, "test_end": 20}
  ]
}
```

### Error conditions

| Status | Cause |
|--------|-------|
| `400 Bad Request` | `train_size + test_size > closes.len()`, insufficient data for any window, or invalid MA parameters |
| `422 Unprocessable Entity` | Missing required fields or wrong types |

---

## POST /api/optimize

Grid search over all combinations of `fast_periods` x `slow_periods`. Only valid pairs (fast < slow) are evaluated. Results are sorted by Sharpe ratio descending.

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `closes` | `f64[]` | yes | — | Close price series |
| `initial_cash` | `f64` | yes | — | Starting capital |
| `fast_periods` | `usize[]` | yes | — | Fast MA period candidates |
| `slow_periods` | `usize[]` | yes | — | Slow MA period candidates |
| `risk_free_rate` | `f64` | no | `0.0` | Annual risk-free rate for Sharpe calculation |
| `periods_per_year` | `f64` | no | `252.0` | Annualisation factor |
| `top_n` | `usize` | no | `0` | Return only top N results; `0` returns all |

### Response Body `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `total_combinations` | `usize` | Total valid (fast < slow) combinations evaluated |
| `results` | `OptimizeResult[]` | Sorted by Sharpe ratio descending (truncated to `top_n` if specified) |

**OptimizeResult object**

| Field | Type | Description |
|-------|------|-------------|
| `fast_period` | `usize` | Fast MA period |
| `slow_period` | `usize` | Slow MA period |
| `sharpe_ratio` | `f64` | Sharpe ratio of this parameter combination |
| `total_return` | `f64` | Total return as a decimal |
| `max_drawdown` | `f64` | Maximum drawdown (positive value) |

### Example

```bash
curl -s -X POST http://localhost:8002/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "closes": [100,101,102,101,103,105,104,106,107,108,109,110,111,110,112,113,114,115,116,117,118,119,120,119,121],
    "initial_cash": 10000.0,
    "fast_periods": [3, 5, 7],
    "slow_periods": [10, 15, 20],
    "top_n": 3
  }'
```

```json
{
  "total_combinations": 9,
  "results": [
    {"fast_period": 5, "slow_period": 15, "sharpe_ratio": 1.84, "total_return": 0.072, "max_drawdown": 0.018},
    {"fast_period": 3, "slow_period": 10, "sharpe_ratio": 1.52, "total_return": 0.065, "max_drawdown": 0.021},
    {"fast_period": 7, "slow_period": 20, "sharpe_ratio": 1.31, "total_return": 0.058, "max_drawdown": 0.015}
  ]
}
```

### Error conditions

| Status | Cause |
|--------|-------|
| `400 Bad Request` | `closes` has fewer than 2 elements |
| `400 Bad Request` | `fast_periods` or `slow_periods` is empty |
| `422 Unprocessable Entity` | Missing required fields or wrong types |

---

## POST /api/indicators

Compute SMA or EMA over a close price series. During the warm-up period (fewer bars than `period`), values are `null`.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `closes` | `f64[]` | yes | Close price series |
| `indicator` | `"sma" \| "ema"` | yes | Indicator type (lowercase) |
| `period` | `usize` | yes | Look-back window; must be >= 1 |

### Response Body `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `indicator` | `string` | Echoed indicator name (`"sma"` or `"ema"`) |
| `period` | `usize` | Echoed period |
| `values` | `(f64 \| null)[]` | Indicator values, same length as `closes`; `null` during warm-up |

### Example

```bash
curl -s -X POST http://localhost:8002/api/indicators \
  -H "Content-Type: application/json" \
  -d '{
    "closes": [100.0, 101.0, 102.0, 103.0, 104.0],
    "indicator": "sma",
    "period": 3
  }'
```

```json
{
  "indicator": "sma",
  "period": 3,
  "values": [null, null, 101.0, 102.0, 103.0]
}
```

```bash
# EMA example
curl -s -X POST http://localhost:8002/api/indicators \
  -H "Content-Type: application/json" \
  -d '{
    "closes": [100.0, 101.0, 102.0, 103.0, 104.0],
    "indicator": "ema",
    "period": 3
  }'
```

```json
{
  "indicator": "ema",
  "period": 3,
  "values": [null, null, 101.0, 102.0, 103.0]
}
```

### Error conditions

| Status | Cause |
|--------|-------|
| `400 Bad Request` | `closes` is empty |
| `400 Bad Request` | `period` is 0 |
| `422 Unprocessable Entity` | `indicator` is not `"sma"` or `"ema"`, missing fields, or wrong types |

---

## Frontend Proxy

In development mode, the quant-assistant frontend (Vite, port 5175) proxies API calls to the appropriate backend so the browser never needs to make cross-origin requests directly.

```
Browser → Vite dev server (5175) → [proxy] → 8001 or 8002
```

- `/api/data/*` routes to **port 8001** (stock-assistant) for market data
- All `/api/backtest/*`, `/api/walk-forward`, `/api/optimize`, `/api/indicators` routes go to **port 8002** (quant-assistant Rust backend)

For full proxy routing tables across all three frontends, see [frontend-routing.md](frontend-routing.md).
