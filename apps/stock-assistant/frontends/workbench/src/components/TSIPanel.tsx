import { useState } from "react";
import { fetchTSI, type TSIData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "双重平滑动量极强",
  bull:        "双重动量偏强",
  neutral:     "双重动量中性",
  bear:        "双重动量偏弱",
  strong_bear: "双重平滑动量极弱",
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

/** TSI gauge — bipolar bar from -100 to +100 with ±25 zone markers. */
function TSIGauge({ tsi, signalLine }: { tsi: number; signalLine: number }) {
  // Map -100..+100 → 0..100%
  const tsiPct  = (tsi + 100) / 200 * 100;
  const sigPct  = (signalLine + 100) / 200 * 100;
  const color   = tsi >= 0 ? "#a6e3a1" : "#f38ba8";
  const sigColor = "#89b4fa";

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:4 }}>
        <span>−100</span>
        <span style={{ color:"#9ca3af" }}>−25 | 0 | +25</span>
        <span>+100</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:12, position:"relative" }}>
        {/* Oversold zone */}
        <div style={{ position:"absolute", left:0, top:0, height:"100%", width:"37.5%", background:"#dc262618", borderRadius:"4px 0 0 4px" }} />
        {/* Overbought zone */}
        <div style={{ position:"absolute", left:"62.5%", top:0, height:"100%", width:"37.5%", background:"#ef444418", borderRadius:"0 4px 4px 0" }} />
        {/* Reference lines at -25, 0, +25 */}
        {[37.5, 50, 62.5].map(p => (
          <div key={p} style={{ position:"absolute", left:`${p}%`, top:0, height:"100%", width:1, background:"#6b7280" }} />
        ))}
        {/* TSI value marker */}
        <div style={{ position:"absolute", left:`${Math.max(0, Math.min(100, tsiPct))}%`, top:0, height:"100%", width:3, background:color, transform:"translateX(-50%)", borderRadius:2 }} />
        {/* Signal line marker */}
        <div style={{ position:"absolute", left:`${Math.max(0, Math.min(100, sigPct))}%`, top:0, height:"100%", width:2, background:sigColor, transform:"translateX(-50%)", opacity:0.7 }} />
      </div>
      <div style={{ display:"flex", gap:12, marginTop:4, fontSize:10 }}>
        <span style={{ color }}> TSI: {tsi >= 0 ? "+" : ""}{tsi.toFixed(2)}</span>
        <span style={{ color:sigColor }}>Signal: {signalLine >= 0 ? "+" : ""}{signalLine.toFixed(2)}</span>
      </div>
    </div>
  );
}

export function TSIPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<TSIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTSI(input.trim().toUpperCase());
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
          TSI · 真实强度指数 (25/13/7)
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
                  {data.tsi_positive ? "▲ 正区间" : "▼ 负区间"}
                  {" · "}
                  {data.tsi_above_signal ? "高于信号线" : "低于信号线"}
                </span>
              </div>

              {/* TSI gauge with signal line */}
              {data.tsi_value != null && data.signal_line != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"12px 14px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:8 }}>TSI vs 信号线（−100 到 +100）</div>
                  <TSIGauge tsi={data.tsi_value} signalLine={data.signal_line} />
                </div>
              )}

              {/* Cross badges */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>零线位置</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.tsi_positive ? "#a6e3a1" : "#f38ba8",
                    background: data.tsi_positive ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.tsi_positive ? "▲ 正区间（看涨）" : "▼ 负区间（看跌）"}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>信号线位置</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.tsi_above_signal ? "#a6e3a1" : "#f38ba8",
                    background: data.tsi_above_signal ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.tsi_above_signal ? "▲ 高于信号线" : "▼ 低于信号线"}
                  </div>
                </div>
              </div>

              {/* Percentile score */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.tsi_score} />
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
