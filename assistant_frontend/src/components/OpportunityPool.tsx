import { useEffect, useState } from "react";

import { fetchCryptoOpportunities } from "../api/client";

interface AdviceEvidence {
  source: string;
  summary: string;
  observed_at: string;
}

interface AdviceCard {
  type: string;
  subject: string;
  recommendation: string;
  confidence: number;
  evidence: AdviceEvidence[];
  risk_notes: string[];
}

/**
 * Crypto opportunity pool view backed by advisor cards.
 */
export function OpportunityPool() {
  const [items, setItems] = useState<AdviceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const result = await fetchCryptoOpportunities<{ items: AdviceCard[] }>("BTC-USDT");
        setItems(result.items);
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
      <p>集中浏览 BTC/ETH 等加密资产的多周期机会卡片。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {!loading && !error ? (
        <ul>
          {items.map((item) => (
            <li key={`${item.type}-${item.subject}`}>
              <strong>{item.subject}</strong> · {item.recommendation} · 置信度 {(item.confidence * 100).toFixed(1)}%
              <div>{item.evidence[0]?.summary}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
