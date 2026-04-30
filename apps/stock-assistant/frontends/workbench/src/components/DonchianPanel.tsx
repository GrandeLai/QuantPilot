import { useState } from "react";
import { fetchDonchian, type DonchianData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "价格近上轨 — 动量极强",
  bull:        "价格偏上轨 — 偏强",
  neutral:     "价格在通道中部 — 中性",
  bear:        "价格偏下轨 — 偏弱",
  strong_bear: "价格近下轨 — 趋势极弱",
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

/** Channel position gauge: 0 (lower) → 100 (upper) with upper/lower/middle labels. */
function ChannelGauge({
  position, upper, lower, middle, widthPct,
}: {
  position: number;
  upper: number;
  lower: number;
  middle: number;
  widthPct: number;
}) {
  const posPct = Math.max(0, Math.min(100, position));
  const color =
    posPct >= 80 ? "#22c55e" :
    posPct >= 60 ? "#86efac" :
    posPct >= 40 ? "#facc15" :
    posPct >= 20 ? "#f87171" : "#ef4444";

  return (
    <div>
      {/* Price labels */}
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:"#9ca3af", marginBottom:4 }}>
        <span style={{ color:"#f38ba8" }}>下轨 {lower.toFixed(2)}</span>
        <span style={{ color:"#89b4fa" }}>中轨 {middle.toFixed(2)}</span>
        <span style={{ color:"#a6e3a1" }}>上轨 {upper.toFixed(2)}</span>
      </div>

      {/* Band bar */}
      <div style={{ background:"#374151", borderRadius:6, height:14, position:"relative", marginBottom:6 }}>
        {/* Gradient fill for context */}
        <div style={{
          position:"absolute", left:0, top:0, height:"100%", width:"100%",
          background:"linear-gradient(to right, #f38ba822, #facc1522, #a6e3a122)",
          borderRadius:6,
        }} />
        {/* Middle line */}
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:1, background:"#89b4fa55" }} />
        {/* Position marker */}
        <div style={{
          position:"absolute",
          left:`${Math.max(2, Math.min(98, posPct))}%`,
          top:1, height:"calc(100% - 2px)",
          width:4, background:color,
          transform:"translateX(-50%)", borderRadius:2,
          boxShadow:`0 0 6px ${color}`,
        }} />
      </div>

      {/* Position % and width */}
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:11 }}>
        <span style={{ color }}>通道位置 {posPct.toFixed(1)}%</span>
        <span style={{ color:"#6c7086" }}>通道宽度 {widthPct.toFixed(1)}%</span>
      </div>
    </div>
  );
}

export function DonchianPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<DonchianData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDonchian(input.trim().toUpperCase());
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
          Donchian Channels · 唐奇安通道 (20)
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
                <span style={{ marginLeft:"auto", fontSize:11, color:"#6c7086" }}>
                  信号: {data.signal}
                </span>
              </div>

              {/* Channel gauge */}
              {data.upper != null && data.lower != null && data.middle != null && data.position != null && data.channel_width_pct != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"12px 14px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:8 }}>唐奇安通道（20日高低区间）</div>
                  <ChannelGauge
                    position={data.position}
                    upper={data.upper}
                    lower={data.lower}
                    middle={data.middle}
                    widthPct={data.channel_width_pct}
                  />
                </div>
              )}

              {/* Band prices grid */}
              {data.upper != null && data.lower != null && data.middle != null && (
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:8, marginBottom:10 }}>
                  {[
                    { label:"上轨（20日高）", value:data.upper, color:"#a6e3a1" },
                    { label:"中轨", value:data.middle, color:"#89b4fa" },
                    { label:"下轨（20日低）", value:data.lower, color:"#f38ba8" },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ background:"#313244", borderRadius:8, padding:"8px 10px", textAlign:"center" }}>
                      <div style={{ fontSize:9, color:"#6c7086", marginBottom:3 }}>{label}</div>
                      <div style={{ fontSize:14, fontWeight:700, color }}>{value.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Percentile score */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.donchian_score} />
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
