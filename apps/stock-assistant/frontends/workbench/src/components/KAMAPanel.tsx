/**
 * KAMAPanel — Kaufman Adaptive Moving Average (F.70)
 *
 * Shows close vs KAMA, trend slope badge, composite score bar,
 * efficiency-ratio concept explanation, and interpretation.
 */

import { useState } from "react";
import { fetchKAMA, type KAMAData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极强上行 — 自适应均线强势跟随",
  bull:        "偏强 — 趋势向好",
  neutral:     "中性 — 市场效率一般",
  bear:        "偏弱 — 趋势走弱",
  strong_bear: "极弱 — 自适应均线下行",
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

export function KAMAPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<KAMAData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchKAMA(input.trim().toUpperCase());
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
          KAMA(10) · 卡夫曼自适应移动平均线
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

          {/* Price / KAMA values */}
          {data.data_available && data.kama_value !== null && (
            <>
              <div style={{ background: "#313244", borderRadius: 8, padding: "12px 16px", marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <div style={{ textAlign: "center", flex: 1 }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>收盘价</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: "#cdd6f4" }}>
                      {(data.close_value ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ width: 1, background: "#45475a", margin: "0 12px" }} />
                  <div style={{ textAlign: "center", flex: 1 }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>KAMA(10)</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: "#cba6f7" }}>
                      {(data.kama_value ?? 0).toFixed(2)}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", justifyContent: "center", gap: 16 }}>
                  <span style={{ fontSize: 12, color: data.price_above_kama ? "#22c55e" : "#f38ba8", fontWeight: 600 }}>
                    价格 {data.price_above_kama ? "高于 ▲" : "低于 ▼"} KAMA
                  </span>
                  <span style={{ fontSize: 12, color: data.kama_rising ? "#22c55e" : "#f38ba8", fontWeight: 600 }}>
                    KAMA {data.kama_rising ? "上升 ↑" : "下降 ↓"}
                  </span>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#6c7086", marginBottom: 4 }}>综合得分 (0–100)</div>
                <ScoreBar score={data.kama_score} />
              </div>

              {/* Explanation chip */}
              <div style={{ background: "#181825", borderRadius: 6, padding: "6px 10px", fontSize: 11, color: "#6c7086", marginBottom: 10 }}>
                💡 KAMA 在趋势明确时快速跟随，震荡时自动减速——减少假突破信号
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
