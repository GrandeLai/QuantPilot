import { useEffect, useState } from "react";

import {
  fetchCryptoResearchSummary,
  type CryptoResearchSummary,
} from "../api/client";

export default function CryptoResearchPanel() {
  const [summaries, setSummaries] = useState<CryptoResearchSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const result = await Promise.all([
          fetchCryptoResearchSummary("BTC-USDT"),
          fetchCryptoResearchSummary("ETH-USDT"),
        ]);
        setSummaries(result);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section className="rounded-xl border border-[#30363d] bg-[#0d1117] p-5 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-white">加密 ML 验证摘要</h2>
        <p className="text-sm text-[#8b949e]">BTC / ETH 多周期研究、walk-forward 与反转识别结果。</p>
      </div>
      {loading ? <div className="text-sm text-[#8b949e]">加载中…</div> : null}
      {error ? <div className="text-sm text-red-400">{error}</div> : null}
      {!loading && !error ? (
        <div className="grid gap-4 md:grid-cols-2">
          {summaries.map((summary) => (
            <div key={summary.symbol} className="rounded-lg border border-[#2a2e39] bg-[#161b22] p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{summary.symbol}</span>
                <span className="text-xs text-[#8b949e]">{summary.validation_windows} 窗口</span>
              </div>
              <div className="text-sm text-[#c9d1d9]">特征数：{summary.feature_count}</div>
              <div className="text-xs text-[#8b949e]">样本数：{summary.rows} · 均值准确率 {(summary.mean_accuracy * 100).toFixed(1)}%</div>
              <div className="text-xs text-[#8b949e]">均值策略收益：{(summary.mean_strategy_return * 100).toFixed(2)}%</div>
              <div className="text-xs text-[#8b949e]">
                最新类别概率：空 {((summary.latest_class_probabilities["-1"] ?? 0) * 100).toFixed(1)}% / 横 {((
                  summary.latest_class_probabilities["0"] ?? 0
                ) * 100).toFixed(1)}% / 多 {((summary.latest_class_probabilities["1"] ?? 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-[#8b949e]">反转概率：{(summary.reversal_probability * 100).toFixed(1)}% · 信号 {summary.reversal_signal}</div>
              <div className="text-xs text-[#8b949e]">关键证据：{summary.reversal_evidence.join(" / ") || "—"}</div>
              <div className="pt-2 border-t border-[#2a2e39]">
                <div className="text-xs font-medium text-white mb-2">Top 因子重要性</div>
                <ul className="space-y-1 text-xs text-[#8b949e]">
                  {Object.entries(summary.feature_importance)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([name, value]) => (
                      <li key={name} className="flex items-center justify-between gap-2">
                        <span className="truncate">{name}</span>
                        <span className="font-mono text-white">{(value * 100).toFixed(1)}%</span>
                      </li>
                    ))}
                </ul>
              </div>
              <div className="pt-2 border-t border-[#2a2e39]">
                <div className="text-xs font-medium text-white mb-2">窗口表现</div>
                <ul className="space-y-1 text-xs text-[#8b949e]">
                  {summary.window_metrics.slice(0, 3).map((window, index) => (
                    <li key={`${summary.symbol}-${index}`} className="flex items-center justify-between gap-2">
                      <span>窗口 {index + 1}</span>
                      <span className="font-mono">
                        准确率 {(window.accuracy * 100).toFixed(1)}% / 收益 {(window.strategy_return * 100).toFixed(2)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
