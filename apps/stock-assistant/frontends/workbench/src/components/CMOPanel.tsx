import { useState } from "react";
import { fetchCMO, type CMOData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "CMO 极强 — 上涨动量显著",
  bull:        "CMO 偏强 — 多头占优",
  neutral:     "CMO 中性",
  bear:        "CMO 偏弱 — 空头占优",
  strong_bear: "CMO 极弱 — 下跌动量显著",
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

/** CMO gauge: maps −100…+100 to a bar centred at 0. */
function CMOGauge({ value }: { value: number }) {
  const clamped = Math.max(-100, Math.min(100, value));
  const isPos   = clamped >= 0;
  const pct     = Math.abs(clamped);          // 0–100 half-width
  const color   = isPos ? "#a6e3a1" : "#f38ba8";

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:3 }}>
        <span>−100</span>
        <span style={{ color, fontWeight:700 }}>{clamped.toFixed(1)}</span>
        <span>+100</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:8, position:"relative" }}>
        {/* centre line */}
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:2, background:"#6b7280" }} />
        {/* filled bar */}
        <div style={{
          position:"absolute",
          top:0, height:"100%",
          left:  isPos ? "50%" : `${50 - pct / 2}%`,
          width: `${pct / 2}%`,
          background: color,
          borderRadius: isPos ? "0 4px 4px 0" : "4px 0 0 4px",
          transition: "width 0.4s ease, left 0.4s ease",
        }} />
      </div>
    </div>
  );
}

export function CMOPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<CMOData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCMO(input.trim().toUpperCase());
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
          Chande Momentum Oscillator · CMO (14)
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

              {/* CMO gauge */}
              {data.cmo_value != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>CMO 值（−100 … +100）</div>
                  <CMOGauge value={data.cmo_value} />
                  {data.signal_value != null && (
                    <div style={{ fontSize:10, color:"#6c7086", marginTop:6 }}>
                      信号线（SMA9）: <span style={{ color:"#89b4fa" }}>{data.signal_value.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Badges */}
              <div style={{ display:"flex", gap:8, marginBottom:10 }}>
                {data.cmo_above_signal != null && (
                  <div style={{
                    background: data.cmo_above_signal ? "#a6e3a122" : "#f38ba822",
                    borderRadius:8, padding:"8px 12px", flex:1,
                  }}>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:3 }}>CMO vs 信号线</div>
                    <div style={{ fontSize:12, fontWeight:700, color: data.cmo_above_signal ? "#a6e3a1" : "#f38ba8" }}>
                      {data.cmo_above_signal ? "▲ 高于信号线" : "▼ 低于信号线"}
                    </div>
                  </div>
                )}
                {data.cmo_positive != null && (
                  <div style={{
                    background: data.cmo_positive ? "#a6e3a122" : "#f38ba822",
                    borderRadius:8, padding:"8px 12px", flex:1,
                  }}>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:3 }}>净动量</div>
                    <div style={{ fontSize:12, fontWeight:700, color: data.cmo_positive ? "#a6e3a1" : "#f38ba8" }}>
                      {data.cmo_positive ? "▲ 净买入（>0）" : "▼ 净卖出（<0）"}
                    </div>
                  </div>
                )}
              </div>

              {/* Score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>综合得分（0–100）</div>
                <ScoreBar score={data.cmo_score} />
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
