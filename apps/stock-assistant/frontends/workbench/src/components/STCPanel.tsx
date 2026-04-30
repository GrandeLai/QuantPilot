/**
 * STCPanel — Schaff Trend Cycle (F.71)
 *
 * STC oscillator (0–100) combining MACD with double-smoothed Stochastic.
 * Shows STC gauge, buy/sell zone badges, trend direction, score bar.
 */

import { useState } from "react";
import { fetchSTC, type STCData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极强趋势 — 买入信号强烈",
  bull:        "趋势偏强 — 上行动能充足",
  neutral:     "趋势中性 — 方向不明",
  bear:        "趋势偏弱 — 下行压力增加",
  strong_bear: "极弱趋势 — 卖出信号强烈",
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

/** STC gauge showing 0–100 with buy zone (>25) and sell zone (<75) markers. */
function STCGauge({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct > 75 ? "#22c55e" : pct > 25 ? "#facc15" : "#f38ba8";
  const buyPct  = 25;
  const sellPct = 75;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#6c7086", marginBottom: 3 }}>
        <span>0 (卖出)</span>
        <span style={{ color, fontWeight: 800, fontSize: 16 }}>{value.toFixed(1)}</span>
        <span>100 (买入)</span>
      </div>
      <div style={{ background: "#374151", borderRadius: 4, height: 10, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${pct}%`, background: color, borderRadius: 4, transition: "width 0.4s ease" }} />
        <div style={{ position: "absolute", left: `${buyPct}%`, top: 0, height: "100%", width: 1, background: "#f38ba8", opacity: 0.8 }} />
        <div style={{ position: "absolute", left: `${sellPct}%`, top: 0, height: "100%", width: 1, background: "#22c55e", opacity: 0.8 }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#6c7086", marginTop: 2 }}>
        <span style={{ marginLeft: `${buyPct}%`, transform: "translateX(-50%)", color: "#f38ba8" }}>25</span>
        <span style={{ marginLeft: `${sellPct - buyPct - 5}%`, transform: "translateX(-50%)", color: "#22c55e" }}>75</span>
      </div>
    </div>
  );
}

export function STCPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<STCData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchSTC(input.trim().toUpperCase());
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
          STC · 沙夫趋势周期指标
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

          {/* STC gauge */}
          {data.data_available && data.stc_value !== null && (
            <>
              <div style={{ background: "#313244", borderRadius: 8, padding: "12px 16px", marginBottom: 12 }}>
                <STCGauge value={data.stc_value} />
              </div>

              {/* Zone and trend badges */}
              <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                <div style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "5px 12px",
                  fontSize: 12,
                  textAlign: "center",
                  flex: 1,
                }}>
                  <div style={{ color: "#6c7086", fontSize: 10, marginBottom: 2 }}>{"买入区域(>25)"}</div>
                  <div style={{ color: data.stc_above_buy ? "#22c55e" : "#f38ba8", fontWeight: 700 }}>
                    {data.stc_above_buy ? "高于 ✓" : "低于 ✗"}
                  </div>
                </div>
                <div style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "5px 12px",
                  fontSize: 12,
                  textAlign: "center",
                  flex: 1,
                }}>
                  <div style={{ color: "#6c7086", fontSize: 10, marginBottom: 2 }}>趋势方向</div>
                  <div style={{ color: data.stc_rising ? "#22c55e" : "#f38ba8", fontWeight: 700 }}>
                    {data.stc_rising ? "上升 ↑" : "下降 ↓"}
                  </div>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#6c7086", marginBottom: 4 }}>综合得分 (0–100)</div>
                <ScoreBar score={data.stc_score} />
              </div>
            </>
          )}

          {/* No data */}
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
