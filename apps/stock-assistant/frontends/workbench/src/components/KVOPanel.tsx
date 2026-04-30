/**
 * KVOPanel — Klinger Volume Oscillator (F.68)
 *
 * Displays KVO vs signal line, KVO positivity badge, composite score bar,
 * and Chinese-language interpretation.
 */

import { useState } from "react";
import { fetchKVO, type KVOData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极强积累 — 量价动能极强",
  bull:        "偏强 — 资金偏向买入",
  neutral:     "中性 — 量价动能平稳",
  bear:        "偏弱 — 资金偏向派发",
  strong_bear: "极弱 — 资金大量流出",
  no_data:     "数据不足",
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const color =
    pct >= 80 ? "#22c55e" :
    pct >= 60 ? "#86efac" :
    pct >= 40 ? "#facc15" :
    pct >= 20 ? "#f87171" : "#ef4444";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#9ca3af", marginBottom: 3 }}>
        <span>0</span>
        <span style={{ color, fontWeight: 700 }}>{pct.toFixed(1)}</span>
        <span>100</span>
      </div>
      <div style={{ background: "#374151", borderRadius: 4, height: 8, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${pct}%`, background: color, borderRadius: 4, transition: "width 0.4s ease" }} />
        {[20, 40, 60, 80].map(t => (
          <div key={t} style={{ position: "absolute", left: `${t}%`, top: 0, height: "100%", width: 1, background: "#4b5563" }} />
        ))}
      </div>
    </div>
  );
}

export function KVOPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<KVOData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchKVO(input.trim().toUpperCase());
      setData(result);
      setTicker(input.trim().toUpperCase());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  const signalColor = data ? (SIGNAL_COLORS[data.signal] ?? "#6b7280") : "#6b7280";
  const signalLabel = data ? (SIGNAL_LABELS[data.signal] ?? data.signal) : "—";

  return (
    <div style={{ background: "#1e1e2e", border: "1px solid #313244", borderRadius: 12, padding: 20, color: "#cdd6f4", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: "#6c7086", textTransform: "uppercase", letterSpacing: 1 }}>
          KVO · 克林格量价振荡器
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#cdd6f4", marginTop: 2 }}>{ticker}</div>
      </div>

      {/* Ticker input */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === "Enter" && handleFetch()}
          placeholder="股票代码"
          style={{ flex: 1, background: "#313244", border: "1px solid #45475a", borderRadius: 6, padding: "6px 10px", color: "#cdd6f4", fontSize: 13 }}
        />
        <button
          onClick={handleFetch}
          disabled={loading}
          style={{ background: "#89b4fa", color: "#1e1e2e", border: "none", borderRadius: 6, padding: "6px 14px", fontWeight: 700, cursor: "pointer", fontSize: 13 }}
        >
          {loading ? "…" : "查询"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ color: "#f38ba8", fontSize: 12, marginBottom: 10 }}>错误：{error}</div>
      )}

      {/* Data */}
      {data && (
        <>
          {/* Signal badge */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
            <div style={{
              background: signalColor + "22",
              border: `1px solid ${signalColor}44`,
              borderRadius: 8,
              padding: "6px 14px",
              fontSize: 13,
              fontWeight: 700,
              color: signalColor,
            }}>
              {signalLabel}
            </div>
          </div>

          {/* KVO and Signal values */}
          {data.data_available && data.kvo_value !== null && (
            <>
              {/* KVO value display */}
              <div style={{ background: "#313244", borderRadius: 8, padding: "12px 16px", marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 11, color: "#6c7086" }}>KVO 值</span>
                  <span style={{
                    fontSize: 22,
                    fontWeight: 800,
                    color: (data.kvo_value ?? 0) >= 0 ? "#22c55e" : "#f38ba8",
                  }}>
                    {(data.kvo_value ?? 0).toLocaleString("zh-CN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: "#6c7086" }}>信号线</span>
                  <span style={{ color: "#cba6f7", fontWeight: 600 }}>
                    {(data.signal_value ?? 0).toLocaleString("zh-CN", { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>

              {/* Status badges */}
              <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
                <div style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "5px 10px",
                  fontSize: 12,
                  textAlign: "center",
                  flex: 1,
                }}>
                  <div style={{ color: "#6c7086", fontSize: 10, marginBottom: 2 }}>KVO vs 信号线</div>
                  <div style={{ color: data.kvo_above_signal ? "#22c55e" : "#f38ba8", fontWeight: 700 }}>
                    {data.kvo_above_signal ? "高于 ▲" : "低于 ▼"}
                  </div>
                </div>
                <div style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "5px 10px",
                  fontSize: 12,
                  textAlign: "center",
                  flex: 1,
                }}>
                  <div style={{ color: "#6c7086", fontSize: 10, marginBottom: 2 }}>资金流向</div>
                  <div style={{ color: data.kvo_positive ? "#22c55e" : "#f38ba8", fontWeight: 700 }}>
                    {data.kvo_positive ? "净积累" : "净派发"}
                  </div>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#6c7086", marginBottom: 4 }}>综合得分 (0–100)</div>
                <ScoreBar score={data.kvo_score} />
              </div>
            </>
          )}

          {/* No data fallback */}
          {!data.data_available && (
            <div style={{ color: "#6c7086", fontSize: 13, marginBottom: 10 }}>
              数据不可用（yfinance 异常）
            </div>
          )}

          {/* Interpretation */}
          {data.interpretation && (
            <div style={{ background: "#313244", borderRadius: 8, padding: "8px 12px", fontSize: 12, color: "#a6adc8", lineHeight: 1.6, marginBottom: 8 }}>
              {data.interpretation}
            </div>
          )}

          {/* Footer */}
          <div style={{ fontSize: 10, color: "#6c7086", textAlign: "right" }}>
            {ticker} · {data.as_of_date}
          </div>
        </>
      )}
    </div>
  );
}
