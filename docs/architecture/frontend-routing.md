# Frontend Routing & Vite Dev Proxy

This document describes how each React frontend routes API calls in development mode via Vite's built-in proxy, and what to configure for production deployments.

---

## 1. Quant-Assistant Frontend (port 5175)

**Config:** `apps/quant-assistant/frontend/vite.config.ts`

This frontend talks to **two** backends:

- **stock-assistant (8001)** — owns all market data (`/api/data/*`). The quant-assistant does not maintain its own market data store; it reads through to the stock-assistant.
- **quant-assistant Rust backend (8002)** — owns all quantitative computation (backtest, walk-forward, optimize, indicators).

### Proxy table

| URL pattern | Target | Purpose |
|-------------|--------|---------|
| `/api/data/*` | `http://localhost:8001` | Market data (OHLCV, quotes) owned by stock-assistant |
| `/api/backtest/*` | `http://localhost:8002` | MA crossover backtest |
| `/api/walk-forward` | `http://localhost:8002` | Walk-forward validation |
| `/api/optimize` | `http://localhost:8002` | MA parameter grid search |
| `/api/indicators` | `http://localhost:8002` | SMA/EMA computation |

### Why two backends?

The QuantPilot architecture enforces a strict ownership rule: `common/data-store/market.duckdb` is **write-accessible only to stock-assistant**. The quant-assistant Rust backend performs stateless computation on data provided by the caller — it does not read from the database directly. The frontend therefore fetches raw OHLCV data from stock-assistant and forwards it (in the request body) to the Rust backend for computation.

See also: [quant-assistant-api.md](quant-assistant-api.md) for the full Rust API reference.

---

## 2. Stock-Assistant Workbench (port 5173)

**Config:** `apps/stock-assistant/frontends/workbench/vite.config.ts`

### Proxy table

| URL pattern | Target | Purpose |
|-------------|--------|---------|
| `/api/*` | `http://127.0.0.1:8000` | All stock-assistant API calls (rewrite strips `/api` prefix) |

> **Note:** The vite.config.ts rewrites `/api` → `` (empty) before forwarding, so the backend sees paths without the `/api` prefix. The dev script starts the stock-assistant backend on port **8001**; ensure the vite config target port matches your local setup.
>
> **Warning:** The actual `vite.config.ts` targets port 8000, but the stock-assistant backend canonical port is 8001 (see `scripts/dev-stock.sh` and CLAUDE.md). The `vite.config.ts` likely contains a stale port value and may need updating.

---

## 3. Stock-Assistant Assistant Frontend (port 5174)

**Config:** `apps/stock-assistant/frontends/assistant/vite.config.ts`

This frontend has a minimal Vite config with no explicit proxy block. The dev script starts it on port 5174:

```bash
(cd apps/stock-assistant/frontends/assistant && npm run dev -- --port 5174 --strictPort)
```

API calls from this frontend must be directed to the stock-assistant backend at port 8001 using a full URL or a separate proxy configuration added to its `vite.config.ts`. Note: the assistant frontend's `src/api/client.ts` issues calls to relative paths such as `/api/advisor/*` and `/api/crypto/*` — these will only resolve correctly in development once a proxy block (targeting port 8001) is added to its `vite.config.ts`, or when the frontend is served behind a reverse proxy that forwards those paths to stock-assistant.

---

## 4. Production Note

Vite's dev proxy **only works when running `vite dev`**. In production (`vite build` output served as static files), the proxy is not available and requests go directly to whatever host/port the browser resolves.

For production deployments, configure a reverse proxy (nginx, Caddy, etc.) in front of all services.

### Example nginx fragment

```nginx
# quant-assistant frontend (served as static files)
server {
    listen 443 ssl;
    server_name quant.example.com;

    root /srv/quant-assistant/dist;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Market data — forward to stock-assistant
    location /api/data/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
    }

    # Quant computation — forward to Rust backend
    location /api/backtest/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
    }
    location /api/walk-forward {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
    }
    location /api/optimize {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
    }
    location /api/indicators {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
    }
}

# stock-assistant workbench
server {
    listen 443 ssl;
    server_name workbench.example.com;

    root /srv/stock-assistant/workbench/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
    }
}
```

---

## 5. Port Summary

| Service | Port | Type | Notes |
|---------|------|------|-------|
| stock-assistant backend | **8001** | Python (FastAPI/uvicorn) | Market data, options, crypto; owns market.duckdb |
| quant-assistant backend | **8002** | Rust (axum) | Stateless quantitative computation |
| stock-assistant workbench | **5173** | Vite dev / static | Main trading workbench UI |
| stock-assistant assistant | **5174** | Vite dev / static | Conversational assistant UI |
| quant-assistant frontend | **5175** | Vite dev / static | Research & backtest UI |
| Redis | **6379** | Redis | Session/cache store (used by stock-assistant) |
