import { useState } from "react";
import { fetchMassIndex, type MassIndexData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "市场极度平静 — 趋势延续概率高",
  bull:        "波动平稳 — 多头环境",
  neutral:     "波动中性",
  bear:        "波动偏大 — 警惕反转风险",
  strong_bear: "波动极大 — 反转风险高",
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

/** MI gauge: range ~24–28+, threshold lines at 26.5 and 27. */
function MIGauge({ value }: { value: number }) {
  const min = 24.0; const max = 29.0;
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const color = value > 27 ? "#dc2626" : value > 26.5 ? "#f97316" : "#a6e3a1";
  const t265 = ((26.5 - min) / (max - min)) * 100;
  const t27  = ((27.0 - min) / (max - min)) * 100;

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#6c7086", marginBottom:3 }}>
        <span>24</span>
        <span style={{ color, fontWeight:700 }}>{value.toFixed(3)}</span>
        <span>29</span>
      </div>
      <div style={{ background:"#374151", borderRadius:4, height:8, position:"relative" }}>
        <div style={{ position:"absolute", left:0, top:0, height:"100%", width:`${pct}%`, background:color, borderRadius:4, transition:"width 0.4s ease" }} />
        {/* threshold lines */}
        <div style={{ position:"absolute", left:`${t265}%`, top:0, height:"100%", width:1, background:"#f97316", opacity:0.8 }} />
        <div style={{ position:"absolute", left:`${t27}%`,  top:0, height:"100%", width:1, background:"#dc2626", opacity:0.8 }} />
      </div>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:9, color:"#6c7086", marginTop:2 }}>
        <span style={{ position:"relative", left:`${t265}%`, transform:"translateX(-50%)", color:"#f97316" }}>26.5</span>
        <span style={{ position:"relative", left:`${t27 - t265}%`, transform:"translateX(-50%)", color:"#dc2626" }}>27</span>
      </div>
    </div>
  );
}

export function MassIndexPanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<MassIndexData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMassIndex(input.trim().toUpperCase());
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
          Mass Index · 反转波动指标 (9/25)
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
                {data.reversal_signal && (
                  <span style={{ marginLeft:"auto", fontSize:12, color:"#f38ba8", fontWeight:700 }}>⚠ 反转信号</span>
                )}
              </div>

              {/* MI gauge */}
              {data.mass_index != null && (
                <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                  <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>Mass Index（阈值：26.5 / 27）</div>
                  <MIGauge value={data.mass_index} />
                </div>
              )}

              {/* Badges */}
              <div style={{ display:"flex", gap:8, marginBottom:10 }}>
                {data.in_bulge != null && (
                  <div style={{
                    background: data.in_bulge ? "#dc262622" : "#a6e3a122",
                    borderRadius:8, padding:"8px 12px", flex:1,
                  }}>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:3 }}>波动区间</div>
                    <div style={{ fontSize:12, fontWeight:700, color: data.in_bulge ? "#f38ba8" : "#a6e3a1" }}>
                      {data.in_bulge ? "🔴 高峰区（>27）" : "🟢 平静区（<27）"}
                    </div>
                  </div>
                )}
                {data.trending_down != null && (
                  <div style={{
                    background: data.trending_down ? "#a6e3a122" : "#f38ba822",
                    borderRadius:8, padding:"8px 12px", flex:1,
                  }}>
                    <div style={{ fontSize:10, color:"#6c7086", marginBottom:3 }}>MI 趋势</div>
                    <div style={{ fontSize:12, fontWeight:700, color: data.trending_down ? "#a6e3a1" : "#f38ba8" }}>
                      {data.trending_down ? "▼ 向下（波动收敛）" : "▲ 向上（波动扩张）"}
                    </div>
                  </div>
                )}
              </div>

              {/* Score bar */}
              <div style={{ background:"#313244", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
                <div style={{ fontSize:10, color:"#6c7086", marginBottom:6 }}>综合得分（0–100）</div>
                <ScoreBar score={data.mi_score} />
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
