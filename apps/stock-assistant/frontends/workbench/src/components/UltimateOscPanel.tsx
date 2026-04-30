import { useState } from "react";
import { fetchUltimateOsc, type UltimateOscData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "多周期极强多头",
  bull:        "多周期偏多",
  neutral:     "多周期中性",
  bear:        "多周期偏空",
  strong_bear: "多周期极强空头",
  no_data:     "数据不足",
};

/** UO gauge — 0 to 100 with overbought/oversold zones highlighted. */
function UOGauge({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  const color =
    pct >= 70 ? "#ef4444" :   // overbought
    pct >= 55 ? "#22c55e" :   // bullish
    pct >= 45 ? "#facc15" :   // neutral
    pct >= 30 ? "#f87171" :   // bearish
    "#dc2626";                 // oversold

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:"#9ca3af", marginBottom:3 }}>
        <span style={{ color:"#dc2626" }}>0 超卖</span>
        <span style={{ color, fontWeight:700, fontSize:16 }}>{pct.toFixed(1)}</span>
        <span style={{ color:"#ef4444" }}>超买 100</span>
      </div>
      {/* Multi-zone bar */}
      <div style={{ background:"#374151", borderRadius:4, height:12, position:"relative", overflow:"hidden" }}>
        {/* Oversold zone (0-30) */}
        <div style={{ position:"absolute", left:0, top:0, height:"100%", width:"30%", background:"#dc262633", borderRadius:"4px 0 0 4px" }} />
        {/* Overbought zone (70-100) */}
        <div style={{ position:"absolute", left:"70%", top:0, height:"100%", width:"30%", background:"#ef444433", borderRadius:"0 4px 4px 0" }} />
        {/* Value indicator */}
        <div style={{ position:"absolute", left:0, top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:4, opacity:0.85, transition:"width 0.4s ease" }} />
        {/* Zone lines at 30 and 70 */}
        {[30, 70].map(t => (
          <div key={t} style={{ position:"absolute", left:`${t}%`, top:0, height:"100%", width:1.5, background:"#6b7280" }} />
        ))}
      </div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginTop:2 }}>
        <span>超卖 (&lt;30)</span>
        <span>中性 (30–70)</span>
        <span>超买 (&gt;70)</span>
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

export function UltimateOscPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<UltimateOscData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUltimateOsc(input.trim().toUpperCase());
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
          终极振荡器 · Ultimate Oscillator (7/14/28)
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
                {data.uo_overbought && (
                  <span style={{ marginLeft:"auto", background:"#ef444422", color:"#f38ba8", fontSize:11, fontWeight:700, borderRadius:4, padding:"2px 8px" }}>⚠ 超买</span>
                )}
                {data.uo_oversold && (
                  <span style={{ marginLeft:"auto", background:"#22c55e22", color:"#a6e3a1", fontSize:11, fontWeight:700, borderRadius:4, padding:"2px 8px" }}>⚡ 超卖</span>
                )}
              </div>

              {/* UO gauge */}
              {data.uo_value != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"12px 14px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:8 }}>终极振荡器值（0–100）</div>
                  <UOGauge value={data.uo_value} />
                </div>
              )}

              {/* Score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.uo_score} />
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
