import { useState } from "react";
import { fetchATR, ATRData } from "../api/client";

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

const REGIME_COLORS: Record<string, string> = {
  high: "#f59e0b",
  normal: "#60a5fa",
  low: "#22c55e",
};

const REGIME_LABELS: Record<string, string> = {
  high: "高波动（趋势扩张）",
  normal: "正常波动",
  low: "低波动（盘整压缩）",
};

export function ATRPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<ATRData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchATR(input.trim().toUpperCase());
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
        🌡️ ATR — 平均真实波幅面板
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

              {/* ATR metrics grid */}
              <div
                style={{
                  background: "#313244",
                  borderRadius: 6,
                  padding: "8px 10px",
                  marginBottom: 10,
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 8,
                }}
              >
                <div>
                  <div style={{ fontSize: 10, color: "#585b70" }}>ATR</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#cdd6f4" }}>
                    {data.atr?.toFixed(2) ?? "—"}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "#585b70" }}>ATR%</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#cdd6f4" }}>
                    {data.atr_pct?.toFixed(2) ?? "—"}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "#585b70" }}>波动率百分位</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#cdd6f4" }}>
                    {data.atr_pct_rank !== null
                      ? `${(data.atr_pct_rank * 100).toFixed(0)}th`
                      : "—"}
                  </div>
                </div>
              </div>

              {/* Volatility regime */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#a6adc8", marginBottom: 4 }}>波动率区间</div>
                <span
                  style={{
                    background: "#16213e",
                    border: `1px solid ${REGIME_COLORS[data.volatility_regime] ?? "#6b7280"}`,
                    color: REGIME_COLORS[data.volatility_regime] ?? "#6b7280",
                    borderRadius: 4,
                    padding: "2px 10px",
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {REGIME_LABELS[data.volatility_regime] ?? data.volatility_regime}
                </span>
              </div>

              {/* SMA position */}
              <div
                style={{
                  display: "flex",
                  gap: 10,
                  marginBottom: 12,
                  flexWrap: "wrap",
                }}
              >
                <span
                  style={{
                    background: "#16213e",
                    border: `1px solid ${data.above_sma20 ? "#22c55e" : "#f87171"}`,
                    color: data.above_sma20 ? "#22c55e" : "#f87171",
                    borderRadius: 4,
                    padding: "2px 8px",
                    fontSize: 11,
                  }}
                >
                  {data.above_sma20 ? "▲ SMA20 上方" : "▼ SMA20 下方"}
                </span>
                <span
                  style={{
                    background: "#16213e",
                    border: `1px solid ${data.above_sma50 ? "#22c55e" : "#f87171"}`,
                    color: data.above_sma50 ? "#22c55e" : "#f87171",
                    borderRadius: 4,
                    padding: "2px 8px",
                    fontSize: 11,
                  }}
                >
                  {data.above_sma50 ? "▲ SMA50 上方" : "▼ SMA50 下方"}
                </span>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#a6adc8" }}>趋势+波动评分</span>
                  <span style={{ color: scoreColor(data.atr_score), fontWeight: 700 }}>
                    {data.atr_score.toFixed(1)}
                  </span>
                </div>
                <div style={{ height: 7, background: "#313244", borderRadius: 4, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${data.atr_score}%`,
                      height: "100%",
                      background: scoreColor(data.atr_score),
                      borderRadius: 4,
                      transition: "width 0.4s ease",
                    }}
                  />
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
