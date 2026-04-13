import { useEffect, useState } from "react";

import { fetchCryptoOpportunities, fetchCryptoRisks, fetchOverview } from "../api/client";

interface AdvisorOverview {
  net_worth: number;
  cash_ratio: number;
  positions: Array<Record<string, unknown>>;
}

interface AdviceCard {
  type: string;
  subject: string;
  recommendation: string;
  confidence: number;
}

/**
 * Minimal review view backed by current overview and advisor card summaries.
 */
export function ReviewAsk() {
  const [overview, setOverview] = useState<AdvisorOverview | null>(null);
  const [opportunities, setOpportunities] = useState<AdviceCard[]>([]);
  const [risks, setRisks] = useState<AdviceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [overviewData, opportunityData, riskData] = await Promise.all([
          fetchOverview<AdvisorOverview>(),
          fetchCryptoOpportunities<{ items: AdviceCard[] }>("BTC-USDT"),
          fetchCryptoRisks<{ items: AdviceCard[] }>("BTC-USDT"),
        ]);
        setOverview(overviewData);
        setOpportunities(opportunityData.items);
        setRisks(riskData.items);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section aria-labelledby="review-ask-title">
      <h2 id="review-ask-title">复盘与问答</h2>
      <p>基于当前概览与研究结果，形成最小复盘摘要。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {!loading && !error && overview ? (
        <div>
          <p>当前净资产：{overview.net_worth.toLocaleString("en-US", { maximumFractionDigits: 2 })}</p>
          <p>当前现金占比：{(overview.cash_ratio * 100).toFixed(1)}%</p>
          <p>高优先机会数：{opportunities.length}</p>
          <p>高优先风险数：{risks.length}</p>
          <p>
            当前复盘结论：
            {risks.length > 0
              ? ` 优先关注 ${risks[0].subject} 的风险信号（${risks[0].recommendation}）。`
              : " 暂无高优先风险。"}
          </p>
        </div>
      ) : null}
    </section>
  );
}
