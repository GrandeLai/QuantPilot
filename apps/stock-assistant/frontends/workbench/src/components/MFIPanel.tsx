import { useState } from "react";
import { fetchMFI, MFIData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull: "#86efac",
  neutral: "#facc15",
  bear: "#f87171",
  strong_bear: "#dc2626",
  no_data: "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "强势多头",
  bull: "多头",
  neutral: "中性",
  bear: "空头",
  strong_bear: "强势空头",
  no_data: "无数据",
};

const DIR_ICONS: Record<string, string> = {
  rising: "▲",
  falling: "▼",
  flat: "→",
};

export function MFIPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<MFIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMFI(input.trim().toUpperCase());
      setData(result);
      setTicker(input.trim().toUpperCase());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return "#22c55e";
    if (score >= 60) return "#86efac";
    if (score >= 40) return "#facc15";
    if (score >= 20) return "#f87171";
    return "#dc2626";
  };

  const mfiZoneColor = (mfi: number) => {
    if (mfi >= 80) return "#22c55e";
    if (mfi <= 20) return "#f87171";
    return "#cdd6f4";
  };

  return (
    <div
      style={{
        background: "#1e1e2e",
        border: "1px solid #333",
        borderRadius: 8,
        padding: 16,
        color: "#cdd6f4",
        fontFamily: "monospace",
        minWidth: 320,
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: "#89b4fa" }}>
        💧 MFI — 资金流量指数面板
      </div>

      {/* Ticker input */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleFetch()}
          placeholder="AAPL"
          style={{
            flex: 1,
            background: "#313244",
            border: "1px solid #45475a",
            borderRadius: 4,
            color: "#cdd6f4",
            padding: "4px 8px",
            fontSize: 13,
          }}
        />
        <button
          onClick={handleFetch}
          disabled={loading}
          style={{
            background: "#89b4fa",
            color: "#1e1e2e",
            border: "none",
            borderRadius: 4,
            padding: "4px 12px",
            cursor: loading ? "wait" : "pointer",
            fontWeight: 700,
            fontSize: 13,
          }}
        >
          {loading ? "…" : "查询"}
        </button>
      </div>

      {error && (
        <div style={{ color: "#f38ba8", fontSize: 12, marginBottom: 8 }}>{error}</div>
      )}

      {data && (
        <>
          {!data.data_available ? (
            <div style={{ color: "#f38ba8", fontSize: 12 }}>数据不可用（yfinance 异常）</div>
          ) : data.signal === "no_data" ? (
            <div style={{ color: "#fab387", fontSize: 12 }}>{data.interpretation}</div>
          ) : (
            <>
              {/* Signal badge */}
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                <span
                  style={{
                    background: SIGNAL_COLORS[data.signal] ?? "#6b7280",
                    color: "#1e1e2e",
                    borderRadius: 4,
                    padding: "2px 10px",
                    fontWeight: 700,
                    fontSize: 13,
                  }}
                >
                  {SIGNAL_LABELS[data.signal] ?? data.signal}
                </span>
                <span style={{ color: "#a6adc8", fontSize: 12 }}>{ticker} · {data.as_of_date}</span>
              </div>

              {/* MFI Gauge */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>MFI 值</span>
                  <span style={{ color: mfiZoneColor(data.mfi ?? 50), fontWeight: 700, fontSize: 14 }}>
                    {data.mfi?.toFixed(1) ?? "—"}{" "}
                    <span style={{ fontSize: 11 }}>
                      {DIR_ICONS[data.mfi_direction] ?? ""}
                    </span>
                  </span>
                </div>
                <div
                  style={{
                    position: "relative",
                    height: 12,
                    background: "linear-gradient(to right, #dc2626 0%, #f87171 15%, #facc15 35%, #facc15 65%, #86efac 85%, #22c55e 100%)",
                    borderRadius: 6,
                    overflow: "visible",
                  }}
                >
                  {/* Cursor */}
                  {data.mfi !== null && (
                    <div
                      style={{
                        position: "absolute",
                        left: `${data.mfi}%`,
                        top: -3,
                        width: 3,
                        height: 18,
                        background: "#cdd6f4",
                        borderRadius: 2,
                        transform: "translateX(-50%)",
                      }}
                    />
                  )}
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 10,
                    color: "#585b70",
                    marginTop: 3,
                  }}
                >
                  <span>0 (超卖)</span>
                  <span>50</span>
                  <span>100 (超买)</span>
                </div>
              </div>

              {/* MFI Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>MFI 评分</span>
                  <span style={{ color: scoreColor(data.mfi_score), fontWeight: 700 }}>
                    {data.mfi_score.toFixed(1)}
                  </span>
                </div>
                <div style={{ height: 7, background: "#313244", borderRadius: 4, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${data.mfi_score}%`,
                      height: "100%",
                      background: scoreColor(data.mfi_score),
                      borderRadius: 4,
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
              </div>

              {/* Flags row */}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
                {data.overbought && (
                  <span
                    style={{
                      background: "#16213e",
                      border: "1px solid #22c55e",
                      color: "#22c55e",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: 11,
                    }}
                  >
                    ⚠️ 超买 ≥80
                  </span>
                )}
                {data.oversold && (
                  <span
                    style={{
                      background: "#16213e",
                      border: "1px solid #f87171",
                      color: "#f87171",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: 11,
                    }}
                  >
                    ⚠️ 超卖 ≤20
                  </span>
                )}
                {data.bullish_divergence && (
                  <span
                    style={{
                      background: "#16213e",
                      border: "1px solid #60a5fa",
                      color: "#60a5fa",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: 11,
                    }}
                  >
                    🔼 资金背离看涨
                  </span>
                )}
                {data.bearish_divergence && (
                  <span
                    style={{
                      background: "#16213e",
                      border: "1px solid #fb923c",
                      color: "#fb923c",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: 11,
                    }}
                  >
                    🔽 资金背离看跌
                  </span>
                )}
              </div>

              {/* Interpretation */}
              <div
                style={{
                  fontSize: 11,
                  color: "#a6adc8",
                  lineHeight: 1.6,
                  borderTop: "1px solid #313244",
                  paddingTop: 8,
                }}
              >
                {data.interpretation}
              </div>
            </>
          )}
        </>
      )}

      {!data && !loading && (
        <div style={{ color: "#585b70", fontSize: 12, textAlign: "center", paddingTop: 16 }}>
          输入股票代码后点击查询
        </div>
      )}
    </div>
  );
}
