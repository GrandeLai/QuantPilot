import { useState } from "react";
import { fetchAroon, type AroonData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "强势上升趋势",
  bull:        "上升偏强",
  neutral:     "多空均衡",
  bear:        "下降偏强",
  strong_bear: "强势下降趋势",
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

/** Up/Down dual-bar gauge showing Aroon Up and Aroon Down side-by-side. */
function AroonGauge({ up, down }: { up: number; down: number }) {
  const upColor   = "#a6e3a1";
  const downColor = "#f38ba8";

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
      {/* Aroon Up */}
      <div>
        <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:2 }}>
          <span>Aroon Up</span>
          <span style={{ color: upColor, fontWeight:700 }}>{up.toFixed(0)}</span>
        </div>
        <div style={{ background:"#374151", borderRadius:4, height:8, position:"relative" }}>
          <div style={{ position:"absolute", left:0, top:0, height:"100%", width:`${up}%`, background:upColor, borderRadius:4, transition:"width 0.4s ease" }} />
        </div>
      </div>
      {/* Aroon Down */}
      <div>
        <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:2 }}>
          <span>Aroon Down</span>
          <span style={{ color: downColor, fontWeight:700 }}>{down.toFixed(0)}</span>
        </div>
        <div style={{ background:"#374151", borderRadius:4, height:8, position:"relative" }}>
          <div style={{ position:"absolute", left:0, top:0, height:"100%", width:`${down}%`, background:downColor, borderRadius:4, transition:"width 0.4s ease" }} />
        </div>
      </div>
    </div>
  );
}

/** Oscillator bipolar bar (-100 to +100). */
function OscBar({ osc }: { osc: number }) {
  const clamped = Math.max(-100, Math.min(100, osc));
  const bullish  = clamped >= 0;
  const pct      = Math.abs(clamped) / 2; // 0-50% of half-width
  const color    = bullish ? "#a6e3a1" : "#f38ba8";

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:4 }}>
        <span>−100（下降极值）</span>
        <span style={{ color, fontWeight:700 }}>{clamped >= 0 ? "+" : ""}{clamped.toFixed(0)}</span>
        <span>+100（上升极值）</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:10, position:"relative" }}>
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:2, background:"#6b7280" }} />
        {bullish ? (
          <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:"0 4px 4px 0" }} />
        ) : (
          <div style={{ position:"absolute", left:`${50 - pct}%`, top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:"4px 0 0 4px" }} />
        )}
      </div>
    </div>
  );
}

export function AroonPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<AroonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAroon(input.trim().toUpperCase());
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
          Aroon · 趋势方向强度 (25)
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
                <span style={{ marginLeft:"auto", fontSize:12, color: data.aroon_bullish ? "#a6e3a1" : "#f38ba8", fontWeight:600 }}>
                  {data.aroon_bullish ? "▲ 上升优势" : "▼ 下降优势"}
                </span>
              </div>

              {/* Oscillator value */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>Aroon 振荡器（Up − Down）</div>
                {data.aroon_oscillator != null && <OscBar osc={data.aroon_oscillator} />}
              </div>

              {/* Up / Down bars */}
              {data.aroon_up != null && data.aroon_down != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:8 }}>Aroon Up / Down</div>
                  <AroonGauge up={data.aroon_up} down={data.aroon_down} />
                </div>
              )}

              {/* Score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.aroon_score} />
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
