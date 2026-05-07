import { useState } from "react";
import { fetchPivotPoints, type PivotPointsData } from "../api/client";

const SIGNAL_COLORS: Record<PivotPointsData["signal"], string> = {
  strong_bull: "#22c55e",
  bull: "#86efac",
  neutral: "#facc15",
  bear: "#f87171",
  strong_bear: "#dc2626",
  no_data: "#6b7280",
};

const SIGNAL_LABELS: Record<PivotPointsData["signal"], string> = {
  strong_bull: "强势看涨",
  bull: "看涨",
  neutral: "中性",
  bear: "看跌",
  strong_bear: "强势看跌",
  no_data: "数据不足",
};

function fmt(value: number | null): string {
  return value == null ? "--" : value.toFixed(2);
}

function ScoreBar({ score, signal }: { score: number; signal: PivotPointsData["signal"] }) {
  const pct = Math.max(0, Math.min(100, score));
  const color = SIGNAL_COLORS[signal] ?? "#6b7280";

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
        {[20, 40, 60, 80].map((threshold) => (
          <div
            key={threshold}
            style={{
              position: "absolute",
              left: `${threshold}%`,
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

function LevelGrid({ data }: { data: PivotPointsData }) {
  const levels = [
    ["R3", data.r3, "#22c55e"],
    ["R2", data.r2, "#4ade80"],
    ["R1", data.r1, "#86efac"],
    ["PP", data.pp, "#facc15"],
    ["S1", data.s1, "#fca5a5"],
    ["S2", data.s2, "#f87171"],
    ["S3", data.s3, "#dc2626"],
  ] as const;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(7, minmax(0, 1fr))",
        gap: 6,
        marginBottom: 12,
      }}
    >
      {levels.map(([label, value, color]) => (
        <div key={label} style={{ background: "#313244", borderRadius: 8, padding: "8px 6px" }}>
          <div style={{ fontSize: 10, color }}>{label}</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#cdd6f4", marginTop: 2 }}>
            {fmt(value)}
          </div>
        </div>
      ))}
    </div>
  );
}

export function PivotPointsPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<PivotPointsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    const nextTicker = input.trim().toUpperCase();
    if (!nextTicker) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchPivotPoints(nextTicker);
      setData(result);
      setTicker(nextTicker);
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  const signal = data?.signal ?? "no_data";
  const signalColor = SIGNAL_COLORS[signal];
  const signalLabel = SIGNAL_LABELS[signal];

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
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: "#6c7086", textTransform: "uppercase", letterSpacing: 1 }}>
          支撑压力 · Pivot Points
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#cdd6f4", marginTop: 2 }}>
          {ticker}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value.toUpperCase())}
          onKeyDown={(event) => event.key === "Enter" && void handleFetch()}
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
          onClick={() => void handleFetch()}
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
          {loading ? "..." : "查询"}
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
                <span style={{ marginLeft: "auto", color: "#9ca3af", fontSize: 12 }}>
                  收盘 {fmt(data.close)}
                </span>
              </div>

              <LevelGrid data={data} />
              <ScoreBar score={data.pivot_score} signal={data.signal} />

              <div
                style={{
                  marginTop: 12,
                  background: "#111827",
                  borderRadius: 8,
                  padding: "10px 12px",
                  fontSize: 12,
                  color: "#bac2de",
                  lineHeight: 1.6,
                }}
              >
                {data.interpretation}
              </div>
              <div style={{ marginTop: 8, color: "#6c7086", fontSize: 10 }}>
                as of {data.as_of_date}
              </div>
            </>
          )}
        </>
      )}

      {!data && !loading && (
        <div style={{ color: "#6c7086", fontSize: 12 }}>
          输入 ticker 查看传统 Pivot Point、R1/R2/R3 与 S1/S2/S3。
        </div>
      )}
    </div>
  );
}
