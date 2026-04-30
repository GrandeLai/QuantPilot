import { useState } from "react";
import { fetchSAR, type SARData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull: "#86efac",
  neutral: "#facc15",
  bear: "#f87171",
  strong_bear: "#dc2626",
  no_data: "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "强势看涨",
  bull: "看涨",
  neutral: "中性",
  bear: "看跌",
  strong_bear: "强势看跌",
  no_data: "数据不足",
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const color =
    pct >= 80
      ? "#22c55e"
      : pct >= 60
      ? "#86efac"
      : pct >= 40
      ? "#facc15"
      : pct >= 20
      ? "#f87171"
      : "#ef4444";

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 11,
          color: "#9ca3af",
          marginBottom: 3,
        }}
      >
        <span>0</span>
        <span style={{ color, fontWeight: 700 }}>{pct.toFixed(1)}</span>
        <span>100</span>
      </div>
      <div
        style={{
          background: "#374151",
          borderRadius: 4,
          height: 8,
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            height: "100%",
            width: `${pct}%`,
            background: color,
            borderRadius: 4,
            transition: "width 0.4s ease",
          }}
        />
        {[20, 40, 60, 80].map((t) => (
          <div
            key={t}
            style={{
              position: "absolute",
              left: `${t}%`,
              top: 0,
              height: "100%",
              width: 1,
              background: "#4b5563",
            }}
          />
        ))}
      </div>
    </div>
  );
}

export function SARPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<SARData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchSAR(input.trim().toUpperCase());
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
    <div
      style={{
        background: "#1e1e2e",
        border: "1px solid #313244",
        borderRadius: 12,
        padding: 20,
        color: "#cdd6f4",
        fontFamily: "sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: "#6c7086", textTransform: "uppercase", letterSpacing: 1 }}>
          抛物线 SAR · Parabolic Stop & Reverse
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#cdd6f4", marginTop: 2 }}>
          {ticker}
        </div>
      </div>

      {/* Ticker input */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleFetch()}
          placeholder="股票代码"
          style={{
            flex: 1,
            background: "#313244",
            border: "1px solid #45475a",
            borderRadius: 6,
            padding: "6px 10px",
            color: "#cdd6f4",
            fontSize: 13,
          }}
        />
        <button
          onClick={handleFetch}
          disabled={loading}
          style={{
            background: loading ? "#45475a" : "#89b4fa",
            color: "#1e1e2e",
            border: "none",
            borderRadius: 6,
            padding: "6px 14px",
            fontWeight: 700,
            fontSize: 13,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "…" : "查询"}
        </button>
      </div>

      {error && (
        <div
          style={{
            background: "#45475a33",
            color: "#f38ba8",
            borderRadius: 6,
            padding: "6px 10px",
            fontSize: 12,
            marginBottom: 10,
          }}
        >
          {error}
        </div>
      )}

      {data && (
        <>
          {!data.data_available ? (
            <div style={{ color: "#f38ba8", fontSize: 13 }}>数据获取失败</div>
          ) : (
            <>
              {/* Signal + direction row */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  marginBottom: 14,
                  background: "#313244",
                  borderRadius: 8,
                  padding: "8px 12px",
                }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: signalColor,
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontWeight: 700, color: signalColor, fontSize: 15 }}>
                  {signalLabel}
                </span>
                {data.sar_direction && (
                  <span
                    style={{
                      marginLeft: "auto",
                      fontSize: 13,
                      color: data.sar_direction === "up" ? "#a6e3a1" : "#f38ba8",
                      fontWeight: 600,
                    }}
                  >
                    {data.sar_direction === "up" ? "▲ 上升趋势" : "▼ 下降趋势"}
                  </span>
                )}
              </div>

              {/* Metrics grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 8,
                  marginBottom: 12,
                }}
              >
                {/* SAR value */}
                <div style={{ background: "#313244", borderRadius: 8, padding: "10px 12px" }}>
                  <div style={{ fontSize: 10, color: "#6c7086" }}>SAR 止损位</div>
                  <div
                    style={{
                      fontSize: 20,
                      fontWeight: 700,
                      marginTop: 2,
                      color: data.sar_bullish ? "#a6e3a1" : "#f38ba8",
                    }}
                  >
                    {data.sar != null ? data.sar.toFixed(2) : "—"}
                  </div>
                </div>

                {/* Distance % */}
                <div style={{ background: "#313244", borderRadius: 8, padding: "10px 12px" }}>
                  <div style={{ fontSize: 10, color: "#6c7086" }}>距 SAR 偏离</div>
                  <div
                    style={{
                      fontSize: 20,
                      fontWeight: 700,
                      marginTop: 2,
                      color:
                        (data.sar_distance_pct ?? 0) >= 0 ? "#a6e3a1" : "#f38ba8",
                    }}
                  >
                    {data.sar_distance_pct != null
                      ? `${data.sar_distance_pct >= 0 ? "+" : ""}${data.sar_distance_pct.toFixed(2)}%`
                      : "—"}
                  </div>
                </div>

                {/* Trend bars */}
                <div style={{ background: "#313244", borderRadius: 8, padding: "10px 12px" }}>
                  <div style={{ fontSize: 10, color: "#6c7086" }}>当前趋势持续</div>
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      marginTop: 2,
                      color: data.trend_bars > 0 ? "#a6e3a1" : "#f38ba8",
                    }}
                  >
                    {Math.abs(data.trend_bars)} 日
                  </div>
                </div>

                {/* SAR bullish badge */}
                <div style={{ background: "#313244", borderRadius: 8, padding: "10px 12px" }}>
                  <div style={{ fontSize: 10, color: "#6c7086" }}>价格 vs SAR</div>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      marginTop: 4,
                      color: data.sar_bullish ? "#a6e3a1" : "#f38ba8",
                      background: data.sar_bullish ? "#a6e3a122" : "#f38ba822",
                      borderRadius: 6,
                      padding: "2px 8px",
                      display: "inline-block",
                    }}
                  >
                    {data.sar_bullish ? "价格 > SAR" : "价格 < SAR"}
                  </div>
                </div>
              </div>

              {/* Score bar */}
              <div
                style={{
                  background: "#313244",
                  borderRadius: 8,
                  padding: "10px 12px",
                  marginBottom: 10,
                }}
              >
                <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 6 }}>
                  历史百分位得分（过去252日）
                </div>
                <ScoreBar score={data.sar_score} />
              </div>

              {/* Interpretation */}
              {data.interpretation && (
                <div
                  style={{
                    fontSize: 12,
                    color: "#bac2de",
                    background: "#313244",
                    borderRadius: 8,
                    padding: "8px 12px",
                    lineHeight: 1.6,
                    marginBottom: 8,
                  }}
                >
                  {data.interpretation}
                </div>
              )}

              {/* Footer */}
              <div style={{ fontSize: 10, color: "#6c7086", textAlign: "right" }}>
                {ticker} · {data.as_of_date}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
