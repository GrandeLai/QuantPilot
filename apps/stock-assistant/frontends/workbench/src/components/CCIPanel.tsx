import { useState } from "react";
import { fetchCCI, CCIData } from "../api/client";

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

export function CCIPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<CCIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCCI(input.trim().toUpperCase());
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

  // CCI to position [-300, 300] → [0%, 100%], clipped
  const cciToPercent = (cci: number) => Math.max(0, Math.min(100, (cci + 300) / 600 * 100));
  const cciColor = (cci: number) => {
    if (cci > 100) return "#22c55e";
    if (cci > 0) return "#86efac";
    if (cci > -100) return "#f87171";
    return "#dc2626";
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
        📏 CCI — 商品通道指数面板
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

              {/* CCI value display */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                  <span style={{ color: "#a6adc8" }}>CCI 值</span>
                  <span
                    style={{
                      color: data.cci !== null ? cciColor(data.cci) : "#6b7280",
                      fontWeight: 700,
                      fontSize: 14,
                    }}
                  >
                    {data.cci !== null ? (data.cci >= 0 ? "+" : "") + data.cci.toFixed(1) : "—"}{" "}
                    <span style={{ fontSize: 11 }}>{DIR_ICONS[data.cci_direction] ?? ""}</span>
                  </span>
                </div>

                {/* Zone bar with zone boundaries at ±100 */}
                <div
                  style={{
                    position: "relative",
                    height: 14,
                    borderRadius: 7,
                    overflow: "visible",
                  }}
                >
                  {/* Oversold zone: -300 to -100 (left 33%) */}
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      width: "33.3%",
                      height: "100%",
                      background: "#f87171",
                      borderRadius: "7px 0 0 7px",
                      opacity: 0.25,
                    }}
                  />
                  {/* Neutral zone: -100 to +100 (middle 33%) */}
                  <div
                    style={{
                      position: "absolute",
                      left: "33.3%",
                      width: "33.4%",
                      height: "100%",
                      background: "#facc15",
                      opacity: 0.2,
                    }}
                  />
                  {/* Overbought zone: +100 to +300 (right 33%) */}
                  <div
                    style={{
                      position: "absolute",
                      left: "66.7%",
                      width: "33.3%",
                      height: "100%",
                      background: "#22c55e",
                      borderRadius: "0 7px 7px 0",
                      opacity: 0.25,
                    }}
                  />
                  {/* Zero line */}
                  <div
                    style={{
                      position: "absolute",
                      left: "50%",
                      top: 0,
                      width: 1,
                      height: "100%",
                      background: "#585b70",
                    }}
                  />
                  {/* Cursor */}
                  {data.cci !== null && (
                    <div
                      style={{
                        position: "absolute",
                        left: `${cciToPercent(data.cci)}%`,
                        top: -2,
                        width: 4,
                        height: 18,
                        background: cciColor(data.cci),
                        borderRadius: 2,
                        transform: "translateX(-50%)",
                        boxShadow: `0 0 6px ${cciColor(data.cci)}`,
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
                  <span>-300</span>
                  <span>-100 (超卖)</span>
                  <span>0</span>
                  <span>+100 (超买)</span>
                  <span>+300</span>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>CCI 评分</span>
                  <span style={{ color: scoreColor(data.cci_score), fontWeight: 700 }}>
                    {data.cci_score.toFixed(1)}
                  </span>
                </div>
                <div style={{ height: 7, background: "#313244", borderRadius: 4, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${data.cci_score}%`,
                      height: "100%",
                      background: scoreColor(data.cci_score),
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
                    ⚠️ 超买区 CCI &gt; 100
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
                    ⚠️ 超卖区 CCI &lt; -100
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
