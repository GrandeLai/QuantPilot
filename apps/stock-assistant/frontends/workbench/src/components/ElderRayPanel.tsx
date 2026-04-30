import { useState } from "react";
import { fetchElderRay, type ElderRayData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "多头极强 — 买盘压力明显",
  bull:        "多头力量偏强 — 趋势偏多",
  neutral:     "多空均衡 — 趋势中性",
  bear:        "空头力量偏强 — 趋势偏空",
  strong_bear: "空头极强 — 卖压明显",
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

/** Bipolar bar for Bull/Bear Power around zero. */
function PowerBar({ value, color, label }: { value: number; color: string; label: string }) {
  const absMax = Math.max(Math.abs(value), 0.01);
  const pct    = (value / absMax / 2 + 0.5) * 100;

  return (
    <div style={{ marginBottom:8 }}>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:3 }}>
        <span style={{ color:"#9ca3af" }}>{label}</span>
        <span style={{ color, fontWeight:700 }}>{value >= 0 ? "+" : ""}{value.toFixed(4)}</span>
      </div>
      <div style={{ background:"#374151", borderRadius:3, height:8, position:"relative" }}>
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:1, background:"#6b7280" }} />
        <div style={{
          position:"absolute",
          left:`${Math.max(2, Math.min(98, Math.min(50, pct)))}%`,
          top:1, height:"calc(100% - 2px)",
          width:`${Math.abs(pct - 50)}%`,
          background: color,
          borderRadius:2,
        }} />
      </div>
    </div>
  );
}

export function ElderRayPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<ElderRayData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchElderRay(input.trim().toUpperCase());
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
    <div style={{ background:"#1e1e2e", border:"1px solid #313244", borderRadius:12, padding:20, color:"#cdd6f4", fontFamily:"sans-serif" }}>
      {/* Header */}
      <div style={{ marginBottom:14 }}>
        <div style={{ fontSize:11, color:"#6c7086", textTransform:"uppercase", letterSpacing:1 }}>
          Elder Ray Index · 艾尔德射线 (EMA 13)
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
              </div>

              {/* Bull / Bear power bars */}
              {data.bull_power != null && data.bear_power != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"12px 14px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:10 }}>多空力量（相对EMA13）</div>
                  <PowerBar value={data.bull_power} color="#a6e3a1" label="多头力量 = High − EMA(13)" />
                  <PowerBar value={data.bear_power} color="#f38ba8" label="空头力量 = Low − EMA(13)" />
                </div>
              )}

              {/* Status badges */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>多头力量</div>
                  <div style={{ fontSize:11, fontWeight:700,
                    color: data.bull_positive ? "#a6e3a1" : "#f38ba8",
                    background: data.bull_positive ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.bull_positive ? "▲ 正值（高于EMA）" : "▼ 负值（低于EMA）"}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>空头力量趋势</div>
                  <div style={{ fontSize:11, fontWeight:700,
                    color: data.bear_rising ? "#a6e3a1" : "#f38ba8",
                    background: data.bear_rising ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.bear_rising ? "▲ 上升（空头减弱）" : "▼ 下降（空头加强）"}
                  </div>
                </div>
              </div>

              {/* EMA base */}
              {data.ema13 != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:2 }}>基准 EMA(13)</div>
                  <div style={{ fontSize:16, fontWeight:700, color:"#89b4fa" }}>{data.ema13.toFixed(2)}</div>
                </div>
              )}

              {/* Score */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>综合得分（0–100）</div>
                <ScoreBar score={data.elder_ray_score} />
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
