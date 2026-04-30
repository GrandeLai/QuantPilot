import { useState } from "react";
import { fetchWilliamsR, WilliamsRData } from "../api/client";

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

export function WilliamsRPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<WilliamsRData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchWilliamsR(input.trim().toUpperCase());
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

  // %R in [-100, 0] → cursor position 0-100%
  const wrToPercent = (wr: number) => Math.max(0, Math.min(100, wr + 100));

  const wrColor = (wr: number) => {
    if (wr > -20) return "#22c55e";   // overbought zone
    if (wr < -80) return "#f87171";   // oversold zone
    return "#facc15";
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
        📐 Williams %R 面板
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

              {/* Williams %R gauge */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                  <span style={{ color: "#a6adc8" }}>Williams %R</span>
                  <span
                    style={{
                      color: data.williams_r !== null ? wrColor(data.williams_r) : "#6b7280",
                      fontWeight: 700,
                      fontSize: 14,
                    }}
                  >
                    {data.williams_r?.toFixed(1) ?? "—"}{" "}
                    <span style={{ fontSize: 11 }}>{DIR_ICONS[data.wr_direction] ?? ""}</span>
                  </span>
                </div>

                {/* Track with zone markers */}
                <div
                  style={{
                    position: "relative",
                    height: 14,
                    borderRadius: 7,
                    overflow: "visible",
                  }}
                >
                  {/* Background: oversold (red) | neutral (yellow) | overbought (green) */}
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      width: "20%",
                      height: "100%",
                      background: "#f87171",
                      borderRadius: "7px 0 0 7px",
                      opacity: 0.3,
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      left: "20%",
                      width: "60%",
                      height: "100%",
                      background: "#facc15",
                      opacity: 0.2,
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      left: "80%",
                      width: "20%",
                      height: "100%",
                      background: "#22c55e",
                      borderRadius: "0 7px 7px 0",
                      opacity: 0.3,
                    }}
                  />
                  {/* Cursor */}
                  {data.williams_r !== null && (
                    <div
                      style={{
                        position: "absolute",
                        left: `${wrToPercent(data.williams_r)}%`,
                        top: -2,
                        width: 4,
                        height: 18,
                        background: wrColor(data.williams_r),
                        borderRadius: 2,
                        transform: "translateX(-50%)",
                        boxShadow: `0 0 6px ${wrColor(data.williams_r)}`,
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
                  <span>-100 (超卖)</span>
                  <span>-80</span>
                  <span>-50</span>
                  <span>-20</span>
                  <span>0 (超买)</span>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>%R 评分</span>
                  <span style={{ color: scoreColor(data.wr_score), fontWeight: 700 }}>
                    {data.wr_score.toFixed(1)}
                  </span>
                </div>
                <div style={{ height: 7, background: "#313244", borderRadius: 4, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${data.wr_score}%`,
                      height: "100%",
                      background: scoreColor(data.wr_score),
                      borderRadius: 4,
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
              </div>

              {/* Flags */}
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
                    ⚠️ 超买区 %R &gt; -20
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
                    ⚠️ 超卖区 %R &lt; -80
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
