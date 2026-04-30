import { useState } from "react";
import { fetchKeltner, type KeltnerData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "强势看涨",
  bull:        "看涨",
  neutral:     "中性",
  bear:        "看跌",
  strong_bear: "强势看跌",
  no_data:     "数据不足",
};

/** Horizontal channel position gauge — 0 at left (lower band) to 100 at right (upper band). */
function ChannelGauge({ position }: { position: number }) {
  const pct = Math.max(0, Math.min(100, position));
  const color =
    pct >= 80 ? "#22c55e" :
    pct >= 60 ? "#86efac" :
    pct >= 40 ? "#facc15" :
    pct >= 20 ? "#f87171" : "#ef4444";

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:3 }}>
        <span>下轨 (0)</span>
        <span style={{ color, fontWeight:700 }}>{pct.toFixed(1)}</span>
        <span>上轨 (100)</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:10, position:"relative" }}>
        {/* band zone colors */}
        <div style={{ position:"absolute", left:0, top:0, height:"100%", width:"20%", background:"#ef444433", borderRadius:"4px 0 0 4px" }} />
        <div style={{ position:"absolute", left:"80%", top:0, height:"100%", width:"20%", background:"#22c55e33", borderRadius:"0 4px 4px 0" }} />
        {/* middle line */}
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:1, background:"#6b7280" }} />
        {/* indicator dot */}
        <div style={{
          position: "absolute",
          left: `calc(${pct}% - 6px)`,
          top: "50%",
          transform: "translateY(-50%)",
          width: 12, height: 12,
          borderRadius: "50%",
          background: color,
          boxShadow: `0 0 6px ${color}`,
          transition: "left 0.4s ease",
        }} />
      </div>
    </div>
  );
}

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

export function KeltnerPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<KeltnerData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchKeltner(input.trim().toUpperCase());
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
          Keltner Channel · EMA(20) ± 2×ATR(10)
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
                {data.above_upper && <span style={{ marginLeft:"auto", fontSize:11, color:"#a6e3a1", background:"#a6e3a122", borderRadius:4, padding:"1px 6px" }}>突破上轨</span>}
                {data.below_lower && <span style={{ marginLeft:"auto", fontSize:11, color:"#f38ba8", background:"#f38ba822", borderRadius:4, padding:"1px 6px" }}>跌破下轨</span>}
              </div>

              {/* Channel gauge */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>通道位置（下轨→上轨）</div>
                <ChannelGauge position={data.kc_position ?? 50} />
              </div>

              {/* Band levels */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:6, marginBottom:10 }}>
                {[
                  { label:"上轨", val: data.upper,  color:"#a6e3a1" },
                  { label:"中轨", val: data.middle, color:"#89b4fa" },
                  { label:"下轨", val: data.lower,  color:"#f38ba8" },
                ].map(({ label, val, color }) => (
                  <div key={label} style={{ background:"#313244", borderRadius:8, padding:"8px 10px", textAlign:"center" }}>
                    <div style={{ fontSize:10, color:"#6c7086" }}>{label}</div>
                    <div style={{ fontSize:14, fontWeight:700, color, marginTop:2 }}>
                      {val != null ? val.toFixed(2) : "—"}
                    </div>
                  </div>
                ))}
              </div>

              {/* Width + score */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 10px" }}>
                  <div style={{ fontSize:10, color:"#6c7086" }}>通道宽度</div>
                  <div style={{ fontSize:16, fontWeight:700, color:"#cba6f7", marginTop:2 }}>
                    {data.channel_width_pct != null ? `${data.channel_width_pct.toFixed(1)}%` : "—"}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 10px" }}>
                  <div style={{ fontSize:10, color:"#6c7086" }}>通道内位置</div>
                  <div style={{ fontSize:16, fontWeight:700, color: signalColor, marginTop:2 }}>
                    {data.kc_position != null ? `${data.kc_position.toFixed(1)} / 100` : "—"}
                  </div>
                </div>
              </div>

              {/* Percentile score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.kc_score} />
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
