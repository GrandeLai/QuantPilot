import { useEffect, useState } from "react";

import { fetchCryptoOpportunities, type AdvisorCard } from "../api/client";

/**
 * Crypto opportunity pool view backed by advisor cards.
 */
export function OpportunityPool() {
  const [items, setItems] = useState<AdvisorCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [btc, eth] = await Promise.all([
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("BTC-USDT"),
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("ETH-USDT"),
        ]);
        setItems([...btc.items, ...eth.items]);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section aria-labelledby="opportunity-pool-title">
      <h2 id="opportunity-pool-title">机会池</h2>
      <p>集中浏览 BTC / ETH 的多周期机会卡片。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {!loading && !error ? (
        <ul>
          {items.map((item) => (
            <li key={`${item.type}-${item.subject}`} className="rounded-lg border border-[#d1d5db] p-4 mb-3">
              <div className="font-semibold">{item.subject}</div>
              <div>{item.recommendation} · 置信度 {(item.confidence * 100).toFixed(1)}%</div>
              <div className="text-sm text-slate-600">{item.evidence[0]?.summary}</div>
              <div className="text-xs text-slate-500 mt-1">{item.risk_notes[0] ?? "—"}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
