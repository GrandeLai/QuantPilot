import { useEffect, useState } from "react";

import { fetchCryptoRisks } from "../api/client";

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
 * Crypto risk radar view backed by advisor risk cards.
 */
export function RiskRadar() {
  const [items, setItems] = useState<AdviceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const result = await fetchCryptoRisks<{ items: AdviceCard[] }>("BTC-USDT");
        setItems(result.items);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section aria-labelledby="risk-radar-title">
      <h2 id="risk-radar-title">风险雷达</h2>
      <p>聚合多周期趋势衰竭、反转概率与持仓分歧风险。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {!loading && !error ? (
        <ul>
          {items.map((item) => (
            <li key={`${item.type}-${item.subject}`}>
              <strong>{item.subject}</strong> · {item.recommendation} · 风险置信度 {(item.confidence * 100).toFixed(1)}%
              <div>{item.evidence[0]?.summary}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
