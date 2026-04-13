import { useEffect, useState } from "react";

import { fetchOverview } from "../api/client";

interface AdvisorOverview {
  net_worth: number;
  cash_ratio: number;
  positions: Array<Record<string, unknown>>;
  generated_at: string;
}

/**
 * Advisor overview backed by the shared backend snapshot.
 */
export function PortfolioOverview() {
  const [overview, setOverview] = useState<AdvisorOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        setOverview(await fetchOverview<AdvisorOverview>());
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section aria-labelledby="portfolio-overview-title">
      <h2 id="portfolio-overview-title">资产总览</h2>
      <p>查看共享后端输出的净值、现金占比和当前持仓快照。</p>
      {loading ? <p>加载中…</p> : null}
      {error ? <p>{error}</p> : null}
      {overview ? (
        <dl>
          <div>
            <dt>净资产</dt>
            <dd>{overview.net_worth.toLocaleString("en-US", { maximumFractionDigits: 2 })}</dd>
          </div>
          <div>
            <dt>现金占比</dt>
            <dd>{(overview.cash_ratio * 100).toFixed(1)}%</dd>
          </div>
          <div>
            <dt>持仓数量</dt>
            <dd>{overview.positions.length}</dd>
          </div>
          <div>
            <dt>生成时间</dt>
            <dd>{overview.generated_at}</dd>
          </div>
        </dl>
      ) : null}
    </section>
  );
}
