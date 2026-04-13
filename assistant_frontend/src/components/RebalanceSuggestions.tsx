import { useEffect, useState } from "react";

import { fetchCryptoOpportunities, fetchCryptoRisks, type AdvisorCard } from "../api/client";

/**
 * Minimal rebalance suggestion view composed from advisor cards.
 */
export function RebalanceSuggestions() {
  const [suggestions, setSuggestions] = useState<AdvisorCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [btcOpportunities, btcRisks, ethOpportunities, ethRisks] = await Promise.all([
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("BTC-USDT"),
          fetchCryptoRisks<{ items: AdvisorCard[] }>("BTC-USDT"),
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("ETH-USDT"),
          fetchCryptoRisks<{ items: AdvisorCard[] }>("ETH-USDT"),
        ]);
        setSuggestions([
          ...btcOpportunities.items,
          ...btcRisks.items,
          ...ethOpportunities.items,
          ...ethRisks.items,
        ]);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section aria-labelledby="rebalance-suggestions-title">
      <h2 id="rebalance-suggestions-title">调仓建议</h2>
      <p>基于 BTC / ETH 研究结果生成最小可执行的观察/降风险建议。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {!loading && !error ? (
        <ul>
          {suggestions.map((item, index) => (
            <li key={`${item.type}-${item.subject}-${index}`} className="rounded-lg border border-[#d1d5db] p-4 mb-3">
              <div className="font-semibold">{item.subject}</div>
              <div>{item.recommendation} · {(item.confidence * 100).toFixed(1)}%</div>
              <div className="text-sm text-slate-600">{item.evidence[0]?.summary}</div>
              <div className="text-xs text-slate-500 mt-1">{item.risk_notes[0] ?? "—"}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
