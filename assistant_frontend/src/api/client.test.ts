import assert from "node:assert/strict";
import test from "node:test";

import { fetchCryptoOpportunities, fetchCryptoRisks } from "./client.ts";

test("fetchCryptoOpportunities calls the crypto opportunity advisor endpoint", async () => {
  let capturedUrl = "";
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    capturedUrl = String(input);
    return new Response(JSON.stringify({ items: [] }), { status: 200 });
  }) as typeof fetch;

  try {
    const result = await fetchCryptoOpportunities<{ items: [] }>("BTC-USDT");
    assert.equal(capturedUrl, "/api/advisor/crypto/opportunities?symbol=BTC-USDT");
    assert.deepEqual(result, { items: [] });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchCryptoRisks calls the crypto risk advisor endpoint", async () => {
  let capturedUrl = "";
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (input: RequestInfo | URL) => {
    capturedUrl = String(input);
    return new Response(JSON.stringify({ items: [] }), { status: 200 });
  }) as typeof fetch;

  try {
    const result = await fetchCryptoRisks<{ items: [] }>("BTC-USDT");
    assert.equal(capturedUrl, "/api/advisor/crypto/risks?symbol=BTC-USDT");
    assert.deepEqual(result, { items: [] });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
