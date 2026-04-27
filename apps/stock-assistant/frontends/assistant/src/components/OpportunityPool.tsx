import { useEffect, useState } from "react";

import {
  fetchCryptoOpportunities,
  fetchCryptoResearchLatest,
  fetchCryptoResearchLatestOptimization,
  fetchCryptoResearchOptimization,
  type AdvisorCard,
  type AdvisorCryptoOptimizationSummary,
  type AdvisorCryptoResearchSummary,
} from "../api/client";

/**
 * Crypto opportunity pool view backed by advisor cards.
 */
export function OpportunityPool() {
  const [items, setItems] = useState<AdvisorCard[]>([]);
  const [research, setResearch] = useState<Record<string, AdvisorCryptoResearchSummary>>({});
  const [optimizations, setOptimizations] = useState<Record<string, AdvisorCryptoOptimizationSummary>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [btc, eth, btcResearch, ethResearch] = await Promise.all([
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("BTC-USDT"),
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("ETH-USDT"),
          fetchCryptoResearchLatest<AdvisorCryptoResearchSummary>("BTC-USDT"),
          fetchCryptoResearchLatest<AdvisorCryptoResearchSummary>("ETH-USDT"),
        ]);
        setItems([...btc.items, ...eth.items].sort((left, right) => right.confidence - left.confidence));
        setResearch({
          "BTC-USDT": btcResearch,
          "ETH-USDT": ethResearch,
        });
        const optimizationEntries = await Promise.all(
          ["BTC-USDT", "ETH-USDT"].map(async (symbol) => {
            try {
              return [symbol, await fetchCryptoResearchLatestOptimization<AdvisorCryptoOptimizationSummary>(symbol, "vwap_ema_trend")] as const;
            } catch {
              try {
                return [symbol, await fetchCryptoResearchOptimization<AdvisorCryptoOptimizationSummary>(symbol)] as const;
              } catch {
                return [symbol, null] as const;
              }
            }
          }),
        );
        setOptimizations(
          Object.fromEntries(
            optimizationEntries.filter((entry): entry is readonly [string, AdvisorCryptoOptimizationSummary] => entry[1] !== null),
          ),
        );
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
              <div className="text-xs text-slate-500 mt-1">
                状态：{research[item.subject]?.market_regime ?? "—"} · 推荐策略：{research[item.subject]?.recommended_strategy_ids.join(" / ") ?? "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                推荐周期：{research[item.subject]?.recommended_timeframes.join(" / ") ?? "—"} · 最优参数：{
                  optimizations[item.subject]
                    ? Object.entries(optimizations[item.subject].best_params).map(([key, value]) => `${key}=${value}`).join(", ")
                    : "—"
                }
              </div>
              <div className="text-xs text-slate-500 mt-1">{item.risk_notes[0] ?? "—"}</div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
