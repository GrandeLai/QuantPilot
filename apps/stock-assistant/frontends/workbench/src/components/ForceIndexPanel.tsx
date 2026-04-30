import { useState } from "react";
import { fetchForceIndex, type ForceIndexData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极强多方力量",
  bull:        "多方偏强",
  neutral:     "多空均衡",
  bear:        "空方偏强",
  strong_bear: "极强空方力量",
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
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:"#9ca3af", marginBottom:3 }}>
        <span>0</span>
        <span style={{ color, fontWeight:700 }}>{pct.toFixed(1)}</span>
        <span>100</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:8, position:"relative" }}>
        <div style={{ position:"absolute", left:0, top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:4, transition:"width 0.4s ease" }} />
        {[20,40,60,80].map(t => (
          <div key={t} style={{ position:"absolute", left:`${t}%`, top:0, height:"100%", width:1, background:"#4b5563" }} />
        ))}
      </div>
    </div>
  );
}

/** Bipolar bar centered at 0 — positive = right, negative = left. */
function ForceBar({ score }: { score: number }) {
  // score is 0-100; 50=neutral, >50=positive, <50=negative
  const center = 50;
  const bullish = score >= center;
  const magnitude = Math.abs(score - center) / center;
  const color = bullish ? "#a6e3a1" : "#f38ba8";

  return (
    <div style={{ background:"#374151", borderRadius:4, height:12, position:"relative" }}>
      {/* center line */}
      <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:2, background:"#6b7280" }} />
      {/* force bar */}
      {bullish ? (
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:`${magnitude * 50}%`, background:color, borderRadius:"0 4px 4px 0" }} />
      ) : (
        <div style={{ position:"absolute", right:`${50 + magnitude * 50}%`, top:0, height:"100%", width:`${magnitude * 50}%`, background:color, borderRadius:"4px 0 0 4px",
          left: `${50 - magnitude * 50}%` }} />
      )}
    </div>
  );
}

export function ForceIndexPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<ForceIndexData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchForceIndex(input.trim().toUpperCase());
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

  const dirMeta: Record<string, { icon: string; color: string }> = {
    rising:  { icon: "↑", color: "#a6e3a1" },
    falling: { icon: "↓", color: "#f38ba8" },
    flat:    { icon: "→", color: "#9ca3af" },
  };
  const dir = data ? (dirMeta[data.fi_direction] ?? dirMeta.flat) : null;

  const formatFI = (v: number | null) => {
    if (v == null) return "—";
    const abs = Math.abs(v);
    if (abs >= 1e9)  return `${(v / 1e9).toFixed(2)}B`;
    if (abs >= 1e6)  return `${(v / 1e6).toFixed(2)}M`;
    if (abs >= 1e3)  return `${(v / 1e3).toFixed(2)}K`;
    return v.toFixed(2);
  };

  return (
    <div style={{ background:"#1e1e2e", border:"1px solid #313244", borderRadius:12, padding:20, color:"#cdd6f4", fontFamily:"sans-serif" }}>
      {/* Header */}
      <div style={{ marginBottom:14 }}>
        <div style={{ fontSize:11, color:"#6c7086", textTransform:"uppercase", letterSpacing:1 }}>
          力量指数 · Force Index (EMA-13)
        </div>
        <div style={{ fontSize:18, fontWeight:700, color:"#cdd6f4", marginTop:2 }}>{ticker}</div>
      </div>

      {/* Ticker input */}
      <div style={{ display:"flex", gap:8, marginBottom:14 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === "Enter" && handleFetch()}
          placeholder="股票代码"
          style={{ flex:1, background:"#313244", border:"1px solid #45475a", borderRadius:6, padding:"6px 10px", color:"#cdd6f4", fontSize:13 }}
        />
        <button
          onClick={handleFetch}
          disabled={loading}
          style={{ background: loading ? "#45475a" : "#89b4fa", color:"#1e1e2e", border:"none", borderRadius:6, padding:"6px 14px", fontWeight:700, fontSize:13, cursor: loading ? "not-allowed" : "pointer" }}
        >
          {loading ? "…" : "查询"}
        </button>
      </div>

      {error && (
        <div style={{ background:"#45475a33", color:"#f38ba8", borderRadius:6, padding:"6px 10px", fontSize:12, marginBottom:10 }}>{error}</div>
      )}

      {data && (
        <>
          {!data.data_available ? (
            <div style={{ color:"#f38ba8", fontSize:13 }}>数据获取失败</div>
          ) : (
            <>
              {/* Signal row */}
              <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:12, background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                <div style={{ width:10, height:10, borderRadius:"50%", background:signalColor, flexShrink:0 }} />
                <span style={{ fontWeight:700, color:signalColor, fontSize:15 }}>{signalLabel}</span>
                {dir && (
                  <span style={{ marginLeft:"auto", fontSize:13, color:dir.color, fontWeight:600 }}>
                    {dir.icon} 力量{data.fi_direction === "rising" ? "增强" : data.fi_direction === "falling" ? "减弱" : "持平"}
                  </span>
                )}
              </div>

              {/* FI value + direction */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086" }}>力量指数值</div>
                  <div style={{ fontSize:18, fontWeight:700, marginTop:2, color: (data.force_index ?? 0) >= 0 ? "#a6e3a1" : "#f38ba8" }}>
                    {formatFI(data.force_index)}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086" }}>方向</div>
                  <div style={{ fontSize:14, fontWeight:700, marginTop:4,
                    color: data.fi_positive ? "#a6e3a1" : "#f38ba8",
                    background: data.fi_positive ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.fi_positive ? "▲ 正向（多头）" : "▼ 负向（空头）"}
                  </div>
                </div>
              </div>

              {/* Force bipolar bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:6 }}>
                  <span>空头极值</span>
                  <span>中性</span>
                  <span>多头极值</span>
                </div>
                <ForceBar score={data.fi_score} />
              </div>

              {/* Percentile score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.fi_score} />
              </div>

              {/* Interpretation */}
              {data.interpretation && (
                <div style={{ fontSize:12, color:"#bac2de", background:"#313244", borderRadius:8, padding:"8px 12px", lineHeight:1.6, marginBottom:8 }}>
                  {data.interpretation}
                </div>
              )}

              <div style={{ fontSize:10, color:"#6c7086", textAlign:"right" }}>{ticker} · {data.as_of_date}</div>
            </>
          )}
        </>
      )}
    </div>
  );
}
