import { useEffect, useState } from "react";

import { fetchOverview, type AdvisorOverviewPayload } from "../api/client";

/**
 * Advisor overview backed by the shared backend snapshot.
 */
export function PortfolioOverview() {
  const [overview, setOverview] = useState<AdvisorOverviewPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        setOverview(await fetchOverview<AdvisorOverviewPayload>());
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
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-[#d1d5db] p-4">
            <div className="text-sm text-slate-500">净资产</div>
            <div className="text-2xl font-semibold">{overview.net_worth.toLocaleString("en-US", { maximumFractionDigits: 2 })}</div>
          </div>
          <div className="rounded-lg border border-[#d1d5db] p-4">
            <div className="text-sm text-slate-500">现金占比</div>
            <div className="text-2xl font-semibold">{(overview.cash_ratio * 100).toFixed(1)}%</div>
          </div>
          <div className="rounded-lg border border-[#d1d5db] p-4">
            <div className="text-sm text-slate-500">持仓数量</div>
            <div className="text-2xl font-semibold">{overview.positions.length}</div>
          </div>
          <div className="rounded-lg border border-[#d1d5db] p-4">
            <div className="text-sm text-slate-500">资产姿态</div>
            <div className="text-lg font-semibold">
              {overview.cash_ratio >= 0.5 ? "防守偏高" : overview.cash_ratio >= 0.2 ? "均衡" : "进攻偏高"}
            </div>
            <div className="text-xs text-slate-500 mt-1">{overview.generated_at}</div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
