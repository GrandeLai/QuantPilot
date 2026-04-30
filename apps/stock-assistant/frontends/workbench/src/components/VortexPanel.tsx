import { useState } from "react";
import { fetchVortex, type VortexData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "上涨涡旋极强 — +VI 显著高于 -VI",
  bull:        "上涨动量偏强 — +VI > -VI",
  neutral:     "涡旋方向中性",
  bear:        "下跌动量偏强 — -VI > +VI",
  strong_bear: "下跌涡旋极强 — -VI 显著高于 +VI",
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

/** +VI and -VI comparison bar. */
function VIBar({ viPlus, viMinus }: { viPlus: number; viMinus: number }) {
  const maxVI = Math.max(viPlus, viMinus, 0.5);
  const plusPct  = (viPlus  / maxVI) * 100;
  const minusPct = (viMinus / maxVI) * 100;

  return (
    <div>
      {/* +VI bar */}
      <div style={{ marginBottom:6 }}>
        <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:2 }}>
          <span style={{ color:"#a6e3a1" }}>+VI (上涨动量)</span>
          <span style={{ color:"#a6e3a1", fontWeight:700 }}>{viPlus.toFixed(4)}</span>
        </div>
        <div style={{ background:"#374151", borderRadius:3, height:8 }}>
          <div style={{ height:"100%", width:`${plusPct}%`, background:"#a6e3a1", borderRadius:3 }} />
        </div>
      </div>
      {/* -VI bar */}
      <div>
        <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:2 }}>
          <span style={{ color:"#f38ba8" }}>-VI (下跌动量)</span>
          <span style={{ color:"#f38ba8", fontWeight:700 }}>{viMinus.toFixed(4)}</span>
        </div>
        <div style={{ background:"#374151", borderRadius:3, height:8 }}>
          <div style={{ height:"100%", width:`${minusPct}%`, background:"#f38ba8", borderRadius:3 }} />
        </div>
      </div>
    </div>
  );
}

export function VortexPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<VortexData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchVortex(input.trim().toUpperCase());
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
          Vortex Indicator · 涡旋指标 (14)
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

              {/* +VI vs -VI bars */}
              {data.vi_plus != null && data.vi_minus != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"12px 14px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:8 }}>+VI 与 -VI 对比（14周期）</div>
                  <VIBar viPlus={data.vi_plus} viMinus={data.vi_minus} />
                </div>
              )}

              {/* Direction badge */}
              {data.vi_bullish != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>涡旋方向</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.vi_bullish ? "#a6e3a1" : "#f38ba8",
                    background: data.vi_bullish ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"4px 10px", display:"inline-block" }}>
                    {data.vi_bullish ? "▲ +VI > -VI — 上涨趋势" : "▼ -VI > +VI — 下跌趋势"}
                  </div>
                  {data.vi_spread != null && (
                    <span style={{ marginLeft:10, fontSize:11, color:"#6c7086" }}>
                      差值: {data.vi_spread >= 0 ? "+" : ""}{data.vi_spread.toFixed(4)}
                    </span>
                  )}
                </div>
              )}

              {/* Percentile score */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.vortex_score} />
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
