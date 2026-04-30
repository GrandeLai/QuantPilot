import { useState } from "react";
import { fetchTRIX, type TRIXData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极强多头动量",
  bull:        "多头偏强",
  neutral:     "动量中性",
  bear:        "空头偏强",
  strong_bear: "极强空头动量",
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

/** TRIX vs Signal gauge — shows the spread between TRIX and its signal line. */
function TRIXCrossGauge({ trix, signalLine, trixAboveSignal }: {
  trix: number;
  signalLine: number;
  trixAboveSignal: boolean;
}) {
  const spread = trix - signalLine;
  const maxSpread = Math.max(Math.abs(spread) * 2, 0.001);
  const pct = Math.min(Math.abs(spread) / maxSpread, 1) * 40; // up to 40% of half-width
  const bullColor = "#a6e3a1";
  const bearColor = "#f38ba8";
  const color = trixAboveSignal ? bullColor : bearColor;

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:4 }}>
        <span>TRIX 低于信号线</span>
        <span>零轴</span>
        <span>TRIX 高于信号线</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:12, position:"relative" }}>
        {/* center line */}
        <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:2, background:"#6b7280" }} />
        {trixAboveSignal ? (
          <div style={{ position:"absolute", left:"50%", top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:"0 4px 4px 0" }} />
        ) : (
          <div style={{ position:"absolute", right:"50%", top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:"4px 0 0 4px",
            left:`${50 - pct}%` }} />
        )}
      </div>
    </div>
  );
}

export function TRIXPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<TRIXData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTRIX(input.trim().toUpperCase());
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

  const fmtTrix = (v: number | null) => v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(4)}%`;

  return (
    <div style={{ background:"#1e1e2e", border:"1px solid #313244", borderRadius:12, padding:20, color:"#cdd6f4", fontFamily:"sans-serif" }}>
      {/* Header */}
      <div style={{ marginBottom:14 }}>
        <div style={{ fontSize:11, color:"#6c7086", textTransform:"uppercase", letterSpacing:1 }}>
          TRIX · 三重指数平滑动量
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
                  {data.trix_positive ? "▲ 零线上方" : "▼ 零线下方"}
                </span>
              </div>

              {/* TRIX value + Signal Line */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086" }}>TRIX 值</div>
                  <div style={{ fontSize:18, fontWeight:700, marginTop:2, color: data.trix_positive ? "#a6e3a1" : "#f38ba8" }}>
                    {fmtTrix(data.trix)}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086" }}>信号线 (EMA-9)</div>
                  <div style={{ fontSize:18, fontWeight:700, marginTop:2, color:"#89b4fa" }}>
                    {fmtTrix(data.signal_line)}
                  </div>
                </div>
              </div>

              {/* Crossover badges */}
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>零线位置</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.trix_positive ? "#a6e3a1" : "#f38ba8",
                    background: data.trix_positive ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.trix_positive ? "▲ 正区间（看涨）" : "▼ 负区间（看跌）"}
                  </div>
                </div>
                <div style={{ background:"#313244", borderRadius:8, padding:"8px 12px" }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:4 }}>信号线位置</div>
                  <div style={{ fontSize:12, fontWeight:700,
                    color: data.trix_above_signal ? "#a6e3a1" : "#f38ba8",
                    background: data.trix_above_signal ? "#a6e3a122" : "#f38ba822",
                    borderRadius:6, padding:"2px 8px", display:"inline-block" }}>
                    {data.trix_above_signal ? "▲ 高于信号线" : "▼ 低于信号线"}
                  </div>
                </div>
              </div>

              {/* TRIX vs Signal cross gauge */}
              {data.trix != null && data.signal_line != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>TRIX 与信号线偏离</div>
                  <TRIXCrossGauge
                    trix={data.trix}
                    signalLine={data.signal_line}
                    trixAboveSignal={data.trix_above_signal}
                  />
                </div>
              )}

              {/* Percentile score */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>历史百分位得分（过去252日）</div>
                <ScoreBar score={data.trix_score} />
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
