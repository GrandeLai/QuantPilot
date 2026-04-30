import { useState } from "react";
import { fetchOBV, OBVData } from "../api/client";

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

const TREND_LABELS: Record<string, string> = {
  confirming_bull: "量价齐升 ✅",
  confirming_bear: "量价齐跌 ⚠️",
  diverging_bull: "OBV 背离看涨 🔼",
  diverging_bear: "OBV 背离看跌 🔽",
  neutral: "中性",
};

const TREND_COLORS: Record<string, string> = {
  confirming_bull: "#22c55e",
  confirming_bear: "#f87171",
  diverging_bull: "#60a5fa",
  diverging_bear: "#fb923c",
  neutral: "#9ca3af",
};

export function OBVPanel() {
  const [ticker, setTicker] = useState("AAPL");
  const [input, setInput] = useState("AAPL");
  const [data, setData] = useState<OBVData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchOBV(input.trim().toUpperCase());
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
        📊 OBV — 能量潮面板
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

              {/* OBV Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>OBV 评分</span>
                  <span style={{ color: scoreColor(data.obv_score), fontWeight: 700 }}>
                    {data.obv_score.toFixed(1)}
                  </span>
                </div>
                <div
                  style={{
                    height: 8,
                    background: "#313244",
                    borderRadius: 4,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${data.obv_score}%`,
                      height: "100%",
                      background: scoreColor(data.obv_score),
                      borderRadius: 4,
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 10,
                    color: "#585b70",
                    marginTop: 2,
                  }}
                >
                  <span>0</span>
                  <span>20</span>
                  <span>40</span>
                  <span>60</span>
                  <span>80</span>
                  <span>100</span>
                </div>
              </div>

              {/* OBV vs EMA20 */}
              <div
                style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "8px 10px",
                  marginBottom: 10,
                }}
              >
                <div style={{ fontSize: 11, color: "#a6adc8", marginBottom: 6 }}>OBV 趋势状态</div>
                <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#585b70" }}>OBV 值</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#cdd6f4" }}>
                      {data.obv !== null ? data.obv.toLocaleString() : "—"}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "#585b70" }}>EMA20</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#cdd6f4" }}>
                      {data.obv_ema20 !== null ? data.obv_ema20.toLocaleString() : "—"}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "#585b70" }}>OBV 位置</div>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 700,
                        color: data.obv_above_ema ? "#22c55e" : "#f87171",
                      }}
                    >
                      {data.obv_above_ema ? "▲ 均线上方" : "▼ 均线下方"}
                    </div>
                  </div>
                </div>
              </div>

              {/* 5-day momentum */}
              <div
                style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "8px 10px",
                  marginBottom: 10,
                }}
              >
                <div style={{ fontSize: 11, color: "#a6adc8", marginBottom: 6 }}>5日动量</div>
                <div style={{ display: "flex", gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#585b70" }}>OBV 5日涨跌</div>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color:
                          data.obv_5d_change_pct === null
                            ? "#6b7280"
                            : data.obv_5d_change_pct >= 0
                            ? "#22c55e"
                            : "#f87171",
                      }}
                    >
                      {data.obv_5d_change_pct !== null
                        ? `${(data.obv_5d_change_pct * 100).toFixed(2)}%`
                        : "—"}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "#585b70" }}>价格 5日涨跌</div>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color:
                          data.price_5d_change_pct === null
                            ? "#6b7280"
                            : data.price_5d_change_pct >= 0
                            ? "#22c55e"
                            : "#f87171",
                      }}
                    >
                      {data.price_5d_change_pct !== null
                        ? `${(data.price_5d_change_pct * 100).toFixed(2)}%`
                        : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Price-OBV trend */}
              <div
                style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "8px 10px",
                  marginBottom: 12,
                }}
              >
                <div style={{ fontSize: 11, color: "#a6adc8", marginBottom: 4 }}>量价关系</div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: TREND_COLORS[data.price_obv_trend] ?? "#9ca3af",
                  }}
                >
                  {TREND_LABELS[data.price_obv_trend] ?? data.price_obv_trend}
                </div>
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
