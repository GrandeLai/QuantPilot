import assert from "node:assert/strict";
import test from "node:test";

import { fetchCryptoResearchSummary } from "./client.ts";

test("fetchCryptoResearchSummary posts the expected research payload", async () => {
  let capturedUrl = "";
  let capturedInit: RequestInit | undefined;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    capturedUrl = String(input);
    capturedInit = init;
    return new Response(
      JSON.stringify({
        symbol: "BTC-USDT",
        base_timeframe: "15m",
        higher_timeframes: ["1h", "4h", "1d", "1w"],
        rows: 100,
        dataset_version: "demo",
        feature_count: 12,
        feature_columns: ["ema_20"],
        validation_windows: 2,
        window_metrics: [],
        mean_accuracy: 0.55,
        mean_strategy_return: 0.03,
        latest_class_signal: 1,
        latest_class_probabilities: { "-1": 0.2, "0": 0.3, "1": 0.5 },
        feature_importance: { ema_20: 0.4 },
        reversal_probability: 0.18,
        reversal_signal: "none",
        reversal_evidence: ["ema_20"],
      }),
      { status: 200 },
    );
  }) as typeof fetch;

  try {
    const result = await fetchCryptoResearchSummary("BTC-USDT");
    assert.equal(capturedUrl, "/api/crypto/research/train");
    assert.equal(capturedInit?.method, "POST");
    assert.ok(String(capturedInit?.body).includes('"symbol":"BTC-USDT"'));
    assert.equal(result.symbol, "BTC-USDT");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
