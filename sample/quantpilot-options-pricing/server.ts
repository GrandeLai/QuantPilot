import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";

// --- Black-Scholes Implementation ---

function normalCDF(x: number): number {
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989423 * Math.exp(-x * x / 2);
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.7814779 + t * (-1.821256 + t * 1.330274))));
  return x > 0 ? 1 - p : p;
}

function normalPDF(x: number): number {
  return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

interface GreeksResult {
  price: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}

function calculateGreeks(
  S: number,
  K: number,
  T: number,
  r: number,
  sigma: number,
  type: "call" | "put"
): GreeksResult {
  if (T <= 0) T = 0.00001; // Avoid division by zero
  const d1 = (Math.log(S / K) + (r + (sigma * sigma) / 2) * T) / (sigma * Math.sqrt(T));
  const d2 = d1 - sigma * Math.sqrt(T);

  const n_d1 = normalCDF(d1);
  const n_d2 = normalCDF(d2);
  const np_d1 = normalPDF(d1);

  let price, delta, theta, rho;

  if (type === "call") {
    price = S * n_d1 - K * Math.exp(-r * T) * n_d2;
    delta = n_d1;
    theta =
      (-S * np_d1 * sigma) / (2 * Math.sqrt(T)) -
      r * K * Math.exp(-r * T) * n_d2;
    rho = K * T * Math.exp(-r * T) * n_d2;
  } else {
    price = K * Math.exp(-r * T) * (1 - n_d2) - S * (1 - n_d1);
    delta = n_d1 - 1;
    theta =
      (-S * np_d1 * sigma) / (2 * Math.sqrt(T)) +
      r * K * Math.exp(-r * T) * (1 - n_d2);
    rho = -K * T * Math.exp(-r * T) * (1 - n_d2);
  }

  const gamma = np_d1 / (S * sigma * Math.sqrt(T));
  const vega = S * Math.sqrt(T) * np_d1;

  return {
    price,
    delta,
    gamma,
    theta: theta / 365, // Daily theta
    vega: vega / 100,   // Per 1% change in vol
    rho: rho / 100,     // Per 1% change in rate
  };
}

function calculateIV(
  marketPrice: number,
  S: number,
  K: number,
  T: number,
  r: number,
  type: "call" | "put"
): number {
  let sigma = 0.5; // Initial guess
  const maxIterations = 100;
  const precision = 1e-5;

  for (let i = 0; i < maxIterations; i++) {
    const greeks = calculateGreeks(S, K, T, r, sigma, type);
    const diff = greeks.price - marketPrice;
    if (Math.abs(diff) < precision) return sigma;
    
    // Vega is the derivative of price with respect to sigma
    // calculateGreeks returns vega per 1% change, so multiply by 100
    const vega = S * Math.sqrt(T) * normalPDF((Math.log(S / K) + (r + (sigma * sigma) / 2) * T) / (sigma * Math.sqrt(T)));
    
    if (vega < 1e-10) break; // Avoid division by zero
    sigma = sigma - diff / vega;
    if (sigma <= 0) sigma = 0.0001; // Keep sigma positive
  }
  return sigma;
}

// --- Server Setup ---

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API routes
  app.post("/api/options/greeks", (req, res) => {
    const { S, K, T, r, sigma, type } = req.body;
    try {
      const result = calculateGreeks(
        Number(S),
        Number(K),
        Number(T),
        Number(r),
        Number(sigma),
        type
      );
      res.json(result);
    } catch (error) {
      res.status(400).json({ error: "Invalid parameters" });
    }
  });

  app.post("/api/options/implied-vol", (req, res) => {
    const { marketPrice, S, K, T, r, type } = req.body;
    try {
      const iv = calculateIV(
        Number(marketPrice),
        Number(S),
        Number(K),
        Number(T),
        Number(r),
        type
      );
      res.json({ iv });
    } catch (error) {
      res.status(400).json({ error: "Invalid parameters" });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
