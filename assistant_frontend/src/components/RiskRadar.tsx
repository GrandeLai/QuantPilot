import { useEffect, useState } from "react";

import { fetchCryptoRisks, type AdvisorCard } from "../api/client";

/**
 * Crypto risk radar view backed by advisor risk cards.
 */
export function RiskRadar() {
  const [items, setItems] = useState<AdvisorCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const result = await fetchCryptoRisks<{ items: AdvisorCard[] }>("BTC-USDT");
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
            <li key={`${item.type}-${item.subject}`} className="rounded-lg border border-[#d1d5db] p-4 mb-3">
              <div className="font-semibold">{item.subject}</div>
              <div>{item.recommendation} · 风险置信度 {(item.confidence * 100).toFixed(1)}%</div>
              <div className="text-sm text-slate-600">{item.evidence[0]?.summary}</div>
              <div className="text-xs text-slate-500 mt-1">{item.risk_notes[0] ?? "—"}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
