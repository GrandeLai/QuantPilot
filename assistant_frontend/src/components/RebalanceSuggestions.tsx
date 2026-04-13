import { useEffect, useState } from "react";

import {
  fetchCryptoOpportunities,
  fetchCryptoResearchLatest,
  fetchCryptoResearchLatestOptimization,
  fetchCryptoResearchOptimization,
  fetchCryptoRisks,
  type AdvisorCard,
  type AdvisorCryptoOptimizationSummary,
  type AdvisorCryptoResearchSummary,
} from "../api/client";

/**
 * Minimal rebalance suggestion view composed from advisor cards.
 */
export function RebalanceSuggestions() {
  const [suggestions, setSuggestions] = useState<AdvisorCard[]>([]);
  const [research, setResearch] = useState<Record<string, AdvisorCryptoResearchSummary>>({});
  const [optimizations, setOptimizations] = useState<Record<string, AdvisorCryptoOptimizationSummary>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [
          btcOpportunities,
          btcRisks,
          ethOpportunities,
          ethRisks,
          btcResearch,
          ethResearch,
          btcOptimization,
          ethOptimization,
        ] = await Promise.all([
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("BTC-USDT"),
          fetchCryptoRisks<{ items: AdvisorCard[] }>("BTC-USDT"),
          fetchCryptoOpportunities<{ items: AdvisorCard[] }>("ETH-USDT"),
          fetchCryptoRisks<{ items: AdvisorCard[] }>("ETH-USDT"),
          fetchCryptoResearchLatest<AdvisorCryptoResearchSummary>("BTC-USDT"),
          fetchCryptoResearchLatest<AdvisorCryptoResearchSummary>("ETH-USDT"),
          fetchCryptoResearchLatestOptimization<AdvisorCryptoOptimizationSummary>("BTC-USDT", "vwap_ema_trend").catch(() =>
            fetchCryptoResearchOptimization<AdvisorCryptoOptimizationSummary>("BTC-USDT"),
          ),
          fetchCryptoResearchLatestOptimization<AdvisorCryptoOptimizationSummary>("ETH-USDT", "vwap_ema_trend").catch(() =>
            fetchCryptoResearchOptimization<AdvisorCryptoOptimizationSummary>("ETH-USDT"),
          ),
        ]);
        setSuggestions([
          ...btcOpportunities.items,
          ...btcRisks.items,
          ...ethOpportunities.items,
          ...ethRisks.items,
        ]);
        setResearch({
          "BTC-USDT": btcResearch,
          "ETH-USDT": ethResearch,
        });
        setOptimizations({
          "BTC-USDT": btcOptimization,
          "ETH-USDT": ethOptimization,
        });
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
              <div className="text-xs text-slate-500 mt-1">
                状态：{research[item.subject]?.market_regime ?? "—"} · 推荐策略：{research[item.subject]?.recommended_strategy_ids.join(" / ") ?? "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                推荐周期：{research[item.subject]?.recommended_timeframes.join(" / ") ?? "—"} · 最优参数：{
                  optimizations[item.subject]
                    ? Object.entries(optimizations[item.subject].best_params)
                        .map(([key, value]) => `${key}=${value}`)
                        .join(", ")
                    : "—"
                }
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
