import { useState } from "react";
import { fetchCMF, CMFData } from "../api/client";

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

export function CMFPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<CMFData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCMF(input.trim().toUpperCase());
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

  const cmfBarColor = (cmf: number) => {
    if (cmf > 0.25) return "#22c55e";
    if (cmf > 0) return "#86efac";
    if (cmf > -0.25) return "#f87171";
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
        🌊 CMF — Chaikin 资金流量面板
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

              {/* CMF value bar (centered at 0) */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                  <span style={{ color: "#a6adc8" }}>CMF 值</span>
                  <span
                    style={{
                      color: data.cmf !== null ? cmfBarColor(data.cmf) : "#6b7280",
                      fontWeight: 700,
                      fontSize: 14,
                    }}
                  >
                    {data.cmf !== null ? (data.cmf >= 0 ? "+" : "") + data.cmf.toFixed(3) : "—"}{" "}
                    <span style={{ fontSize: 11 }}>{DIR_ICONS[data.cmf_direction] ?? ""}</span>
                  </span>
                </div>
                {/* Centered bar */}
                <div
                  style={{
                    position: "relative",
                    height: 10,
                    background: "#313244",
                    borderRadius: 5,
                  }}
                >
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
                  {/* CMF bar */}
                  {data.cmf !== null && (
                    <div
                      style={{
                        position: "absolute",
                        left: data.cmf >= 0 ? "50%" : `${50 + data.cmf * 50}%`,
                        width: `${Math.abs(data.cmf) * 50}%`,
                        height: "100%",
                        background: cmfBarColor(data.cmf),
                        borderRadius: data.cmf >= 0 ? "0 4px 4px 0" : "4px 0 0 4px",
                        transition: "all 0.4s ease",
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
                    marginTop: 2,
                  }}
                >
                  <span>-1.0 (极度卖出)</span>
                  <span>0</span>
                  <span>+1.0 (极度买入)</span>
                </div>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>CMF 评分</span>
                  <span style={{ color: scoreColor(data.cmf_score), fontWeight: 700 }}>
                    {data.cmf_score.toFixed(1)}
                  </span>
                </div>
                <div style={{ height: 7, background: "#313244", borderRadius: 4, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${data.cmf_score}%`,
                      height: "100%",
                      background: scoreColor(data.cmf_score),
                      borderRadius: 4,
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
              </div>

              {/* Flags */}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
                {data.cmf_positive && (
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
                    ✅ CMF 正值（净买入）
                  </span>
                )}
                {!data.cmf_positive && (
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
                    ⚠️ CMF 负值（净卖出）
                  </span>
                )}
                {data.cmf_strong_bull && (
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
                    🚀 强势买入 &gt;0.25
                  </span>
                )}
                {data.cmf_strong_bear && (
                  <span
                    style={{
                      background: "#16213e",
                      border: "1px solid #dc2626",
                      color: "#dc2626",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: 11,
                    }}
                  >
                    🔻 强势卖出 &lt;-0.25
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
