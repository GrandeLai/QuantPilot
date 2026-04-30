/**
 * ChoppinessPanel — Choppiness Index (F.79)
 *
 * Shows CHOP value, trending/choppy status, price vs SMA,
 * composite score bar, and interpretation.
 */

import { useState } from "react";
import { fetchCHOP, type CHOPData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极佳 — 趋势强烈+多头方向",
  bull:        "偏强 — 趋势市+价格偏多",
  neutral:     "中性 — 市场状态中性",
  bear:        "偏弱 — 价格偏空",
  strong_bear: "极弱 — 趋势强烈+空头方向",
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

function ChopGauge({ value }: { value: number }) {
  // Visual gauge: 0=trending, 100=choppy; key thresholds at 38.2 and 61.8
  const color = value < 38.2 ? "#22c55e" : value > 61.8 ? "#f38ba8" : "#facc15";
  const label = value < 38.2 ? "强趋势" : value > 61.8 ? "强盘整" : "过渡";
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#6c7086", marginBottom: 3 }}>
        <span>趋势(0)</span>
        <span style={{ color, fontWeight: 700 }}>{value.toFixed(1)} {label}</span>
        <span>盘整(100)</span>
      </div>
      <div style={{ background: "#374151", borderRadius: 4, height: 8, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${pct}%`, background: color, borderRadius: 4, transition: "width 0.4s ease" }} />
        {/* Thresholds at 38.2 and 61.8 */}
        {[38.2, 61.8].map(t => (
          <div key={t} style={{ position: "absolute", left: `${t}%`, top: 0, height: "100%", width: 1, background: "#cba6f7" }} />
        ))}
      </div>
    </div>
  );
}

export function ChoppinessPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<CHOPData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCHOP(input.trim().toUpperCase());
      setData(result);
      setTicker(input.trim().toUpperCase());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  const sigColor = data ? (SIGNAL_COLORS[data.signal] ?? "#6b7280") : "#6b7280";
  const sigLabel = data ? (SIGNAL_LABELS[data.signal] ?? data.signal) : "—";

  return (
    <div style={{ background: "#1e1e2e", border: "1px solid #313244", borderRadius: 12, padding: 20, color: "#cdd6f4", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: "#6c7086", textTransform: "uppercase", letterSpacing: 1 }}>
          CHOP · Choppiness Index (14)
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

      {error && (
        <div style={{ color: "#f38ba8", fontSize: 12, marginBottom: 10 }}>错误：{error}</div>
      )}

      {data && (
        <>
          <div style={{ marginBottom: 14 }}>
            <div style={{
              display: "inline-block",
              background: sigColor + "22",
              border: `1px solid ${sigColor}44`,
              borderRadius: 8,
              padding: "6px 14px",
              fontSize: 13,
              fontWeight: 700,
              color: sigColor,
            }}>
              {sigLabel}
            </div>
          </div>

          {data.data_available && data.chop_value !== null && (
            <>
              {/* CHOP gauge */}
              <div style={{ background: "#313244", borderRadius: 8, padding: "12px 16px", marginBottom: 12 }}>
                <div style={{ marginBottom: 10 }}>
                  <ChopGauge value={data.chop_value ?? 50} />
                </div>
                <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
                  <span style={{
                    fontSize: 12, fontWeight: 600,
                    color: data.is_trending ? "#22c55e" : "#f38ba8",
                  }}>
                    {data.is_trending ? "趋势市 ✓" : "盘整市 ✗"}
                  </span>
                  <span style={{
                    fontSize: 12, fontWeight: 600,
                    color: data.price_above_sma ? "#22c55e" : "#f38ba8",
                  }}>
                    价格{data.price_above_sma ? "高于" : "低于"} SMA(20)
                  </span>
                </div>
              </div>

              {/* Context tip */}
              <div style={{ background: "#181825", borderRadius: 6, padding: "6px 10px", fontSize: 11, color: "#6c7086", marginBottom: 10 }}>
                💡 CHOP{"<"}38.2=强趋势，CHOP{">"}61.8=强盘整；趋势策略在低 CHOP 时使用，均值回归策略在高 CHOP 时使用
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#6c7086", marginBottom: 4 }}>综合得分 (0–100)</div>
                <ScoreBar score={data.chop_score} />
              </div>
            </>
          )}

          {!data.data_available && (
            <div style={{ color: "#6c7086", fontSize: 13, marginBottom: 10 }}>数据不可用（yfinance 异常）</div>
          )}

          {data.interpretation && (
            <div style={{ background: "#313244", borderRadius: 8, padding: "8px 12px", fontSize: 12, color: "#a6adc8", lineHeight: 1.6, marginBottom: 8 }}>
              {data.interpretation}
            </div>
          )}

          <div style={{ fontSize: 10, color: "#6c7086", textAlign: "right" }}>
            {ticker} · {data.as_of_date}
          </div>
        </>
      )}
    </div>
  );
}
