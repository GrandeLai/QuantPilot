import { useState } from "react";
import { fetchPPO, type PPOData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "PPO 极强 — 快线大幅高于慢线",
  bull:        "PPO 偏强 — 多头趋势延续",
  neutral:     "PPO 中性",
  bear:        "PPO 偏弱 — 空头趋势延续",
  strong_bear: "PPO 极弱 — 快线大幅低于慢线",
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

/** Histogram bar: centred at 0, coloured by sign. */
function HistBar({ value }: { value: number }) {
  const isPos = value >= 0;
  const pct   = Math.min(Math.abs(value) * 5, 50);  // scale: 10% PPO → full half
  const color = isPos ? "#a6e3a1" : "#f38ba8";
  return (
    <div style={{ background:"#374151", borderRadius:4, height:8, position:"relative" }}>
      <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:2, background:"#6b7280" }} />
      <div style={{
        position:"absolute", top:0, height:"100%",
        left: isPos ? "50%" : `${50 - pct}%`,
        width: `${pct}%`,
        background: color,
        borderRadius: isPos ? "0 4px 4px 0" : "4px 0 0 4px",
        transition: "width 0.4s ease",
      }} />
    </div>
  );
}

export function PPOPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<PPOData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchPPO(input.trim().toUpperCase());
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
          Percentage Price Oscillator · PPO (12/26/9)
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

              {/* PPO / Signal / Histogram */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, marginBottom:8 }}>
                  {data.ppo_value != null && (
                    <span>PPO <b style={{ color: data.ppo_positive ? "#a6e3a1" : "#f38ba8" }}>{data.ppo_value.toFixed(4)}%</b></span>
                  )}
                  {data.signal_value != null && (
                    <span style={{ color:"#6c7086" }}>信号线 <b style={{ color:"#89b4fa" }}>{data.signal_value.toFixed(4)}%</b></span>
                  )}
                  {data.histogram != null && (
                    <span style={{ color:"#6c7086" }}>柱状 <b style={{ color: data.histogram >= 0 ? "#a6e3a1" : "#f38ba8" }}>{data.histogram.toFixed(4)}</b></span>
                  )}
                </div>
                {data.histogram != null && (
                  <>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>柱状图（PPO − 信号线）</div>
                    <HistBar value={data.histogram} />
                  </>
                )}
              </div>

              {/* Badges */}
              <div style={{ display:"flex", gap:8, marginBottom:10 }}>
                {data.ppo_above_signal != null && (
                  <div style={{
                    background: data.ppo_above_signal ? "#a6e3a122" : "#f38ba822",
                    borderRadius:8, padding:"8px 12px", flex:1,
                  }}>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:3 }}>PPO vs 信号线</div>
                    <div style={{ fontSize:12, fontWeight:700, color: data.ppo_above_signal ? "#a6e3a1" : "#f38ba8" }}>
                      {data.ppo_above_signal ? "▲ 高于信号线" : "▼ 低于信号线"}
                    </div>
                  </div>
                )}
                {data.ppo_positive != null && (
                  <div style={{
                    background: data.ppo_positive ? "#a6e3a122" : "#f38ba822",
                    borderRadius:8, padding:"8px 12px", flex:1,
                  }}>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:3 }}>EMA 位置</div>
                    <div style={{ fontSize:12, fontWeight:700, color: data.ppo_positive ? "#a6e3a1" : "#f38ba8" }}>
                      {data.ppo_positive ? "▲ 快线>慢线（多头）" : "▼ 快线<慢线（空头）"}
                    </div>
                  </div>
                )}
              </div>

              {/* Score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>综合得分（0–100）</div>
                <ScoreBar score={data.ppo_score} />
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
