import { useEffect, useState } from "react";

import { fetchCryptoOpportunities, fetchCryptoRisks } from "../api/client";

interface AdviceCard {
  type: string;
  subject: string;
  recommendation: string;
  confidence: number;
  evidence: Array<{ summary: string }>;
  risk_notes: string[];
}

/**
 * Minimal rebalance suggestion view composed from advisor cards.
 */
export function RebalanceSuggestions() {
  const [suggestions, setSuggestions] = useState<AdviceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [opportunities, risks] = await Promise.all([
          fetchCryptoOpportunities<{ items: AdviceCard[] }>("BTC-USDT"),
          fetchCryptoRisks<{ items: AdviceCard[] }>("BTC-USDT"),
        ]);
        setSuggestions([...opportunities.items, ...risks.items]);
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
      <p>基于 BTC/ETH 研究结果生成最小可执行的观察/降风险建议。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {!loading && !error ? (
        <ul>
          {suggestions.map((item, index) => (
            <li key={`${item.type}-${item.subject}-${index}`}>
              <strong>{item.subject}</strong> · {item.recommendation} · {(item.confidence * 100).toFixed(1)}%
              <div>{item.evidence[0]?.summary}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
