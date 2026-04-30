/**
 * AlligatorPanel — Williams Alligator (F.77)
 *
 * Shows Jaw/Teeth/Lips SMMA lines, alignment status,
 * composite score bar, and interpretation.
 */

import { useState } from "react";
import { fetchAlligator, type AlligatorData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极佳 — 鳄鱼嘴张开向上",
  bull:        "偏强 — 均线多头排列",
  neutral:     "中性 — 鳄鱼入睡盘整",
  bear:        "偏弱 — 均线空头排列",
  strong_bear: "极弱 — 鳄鱼嘴张开向下",
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

export function AlligatorPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<AlligatorData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAlligator(input.trim().toUpperCase());
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
          Alligator · Williams 鳄鱼指标 (SMMA 5/8/13)
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

      {error && (
        <div style={{ color: "#f38ba8", fontSize: 12, marginBottom: 10 }}>错误：{error}</div>
      )}

      {data && (
        <>
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

          {data.data_available && data.jaw !== null && (
            <>
              {/* Three lines */}
              <div style={{ background: "#313244", borderRadius: 8, padding: "12px 16px", marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-around", marginBottom: 8 }}>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>颚 Jaw (13)</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: "#89b4fa" }}>
                      {(data.jaw ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>齿 Teeth (8)</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: "#f38ba8" }}>
                      {(data.teeth ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>唇 Lips (5)</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: "#a6e3a1" }}>
                      {(data.lips ?? 0).toFixed(2)}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: data.lips_above_teeth ? "#22c55e" : "#f38ba8" }}>
                    唇{data.lips_above_teeth ? ">" : "<"}齿
                  </span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: data.teeth_above_jaw ? "#22c55e" : "#f38ba8" }}>
                    齿{data.teeth_above_jaw ? ">" : "<"}颚
                  </span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: data.price_above_jaw ? "#22c55e" : "#f38ba8" }}>
                    价格{data.price_above_jaw ? "高于" : "低于"}颚线
                  </span>
                </div>
              </div>

              {/* Context tip */}
              <div style={{ background: "#181825", borderRadius: 6, padding: "6px 10px", fontSize: 11, color: "#6c7086", marginBottom: 10 }}>
                💡 三线齐开（分叉）=趋势启动；三线交织（入睡）=盘整横盘；避免在鳄鱼入睡时交易
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#6c7086", marginBottom: 4 }}>综合得分 (0–100)</div>
                <ScoreBar score={data.alligator_score} />
              </div>
            </>
          )}

          {!data.data_available && (
            <div style={{ color: "#6c7086", fontSize: 13, marginBottom: 10 }}>数据不可用（yfinance 异常）</div>
          )}

          {data.interpretation && (
            <div style={{ background: "#313244", borderRadius: 8, padding: "8px 12px", fontSize: 12, color: "#a6adc8", lineHeight: 1.6, marginBottom: 8 }}>
              {data.interpretation}
            </div>
          )}

          <div style={{ fontSize: 10, color: "#6c7086", textAlign: "right" }}>
            {ticker} · {data.as_of_date}
          </div>
        </>
      )}
    </div>
  );
}
