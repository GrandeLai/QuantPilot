import { useState } from "react";
import { fetchIchimoku, type IchimokuData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "多重看涨 — 价格云上，排列强势",
  bull:        "偏强看涨 — 一云图倾向多头",
  neutral:     "信号混杂 — 云层内部整理",
  bear:        "偏弱看跌 — 一云图倾向空头",
  strong_bear: "多重看跌 — 价格云下，排列弱势",
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

/** Visual showing price position relative to Ichimoku cloud. */
function CloudPositionBadge({ priceVsCloud }: { priceVsCloud: string }) {
  const cfg = {
    above:  { label:"▲ 云层上方（看涨）", color:"#22c55e", bg:"#22c55e22" },
    inside: { label:"◼ 云层内部（中性）", color:"#facc15", bg:"#facc1522" },
    below:  { label:"▼ 云层下方（看跌）", color:"#f87171", bg:"#f8717122" },
  }[priceVsCloud] ?? { label: priceVsCloud, color:"#6b7280", bg:"#6b728022" };

  return (
    <div style={{ background: cfg.bg, borderRadius:6, padding:"4px 10px", display:"inline-block" }}>
      <span style={{ color: cfg.color, fontWeight:700, fontSize:12 }}>{cfg.label}</span>
    </div>
  );
}

export function IchimokuPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<IchimokuData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchIchimoku(input.trim().toUpperCase());
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
          Ichimoku Cloud · 一云图 (9/26/52)
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

              {/* Price vs cloud */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>价格相对云层位置</div>
                <CloudPositionBadge priceVsCloud={data.price_vs_cloud} />
              </div>

              {/* Senkou A/B and TK status */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>云层方向</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.cloud_bullish ? "#a6e3a1" : "#f38ba8",
                    background: data.cloud_bullish ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.cloud_bullish ? "▲ 先行A>先行B（多头云）" : "▼ 先行A<先行B（空头云）"}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>转换线/基准线</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.tk_bullish ? "#a6e3a1" : "#f38ba8",
                    background: data.tk_bullish ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.tk_bullish ? "▲ 转换线>基准线（金叉）" : "▼ 转换线<基准线（死叉）"}
                  </div>
                </div>
              </div>

              {/* Chikou Span */}
              {data.chikou_above != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>迟行线（26日前）</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.chikou_above ? "#a6e3a1" : "#f38ba8" }}>
                    {data.chikou_above ? "▲ 高于26日前收盘（看涨）" : "▼ 低于26日前收盘（看跌）"}
                  </div>
                </div>
              )}

              {/* Component prices grid */}
              {data.tenkan != null && data.kijun != null && data.senkou_a != null && data.senkou_b != null && (
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                  {[
                    { label:"转换线 (9)", value:data.tenkan, color:"#89dceb" },
                    { label:"基准线 (26)", value:data.kijun, color:"#89b4fa" },
                    { label:"先行A", value:data.senkou_a, color:"#a6e3a1" },
                    { label:"先行B (52)", value:data.senkou_b, color:"#fab387" },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ background:"#313244", borderRadius:8, padding:"8px 10px" }}>
                      <div style={{ fontSize:9, color:"#6c7086", marginBottom:3 }}>{label}</div>
                      <div style={{ fontSize:14, fontWeight:700, color }}>{value.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Score */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>综合得分（0–100）</div>
                <ScoreBar score={data.ichimoku_score} />
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
