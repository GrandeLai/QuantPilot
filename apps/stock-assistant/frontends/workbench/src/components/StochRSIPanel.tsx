import { useState } from "react";
import { fetchStochRSI, type StochRSIData } from "../api/client";

const SIG_LABEL: Record<string, string> = {
  strong_bull: "极强",
  bull: "偏强",
  neutral: "中性",
  bear: "偏弱",
  strong_bear: "极弱",
  no_data: "数据不足",
};

const SIG_COLOR: Record<string, string> = {
  strong_bull: "#00c853",
  bull: "#69f0ae",
  neutral: "#ffd740",
  bear: "#ff6d00",
  strong_bear: "#f44336",
  no_data: "#9e9e9e",
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const color = pct >= 80 ? "#00c853" : pct >= 60 ? "#69f0ae" : pct >= 40 ? "#ffd740" : pct >= 20 ? "#ff6d00" : "#f44336";
  return (
    <div style={{ background: "#333", borderRadius: 4, height: 8, width: "100%", margin: "4px 0" }}>
      <div style={{ width: `${pct}%`, height: "100%", borderRadius: 4, background: color, transition: "width 0.4s" }} />
    </div>
  );
}

function KDGauge({ k, d }: { k: number; d: number }) {
  const kColor = k > 80 ? "#f44336" : k < 20 ? "#69f0ae" : "#ffd740";
  const dColor = "#888";
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#666", marginBottom: 2 }}>
        <span>0</span>
        <span style={{ color: "#aaa" }}>超卖 20</span>
        <span style={{ color: "#aaa" }}>50</span>
        <span style={{ color: "#aaa" }}>80 超买</span>
        <span>100</span>
      </div>
      <div style={{ position: "relative", background: "#2a2a2a", borderRadius: 4, height: 14 }}>
        {/* Threshold lines */}
        <div style={{ position: "absolute", left: "20%", top: 0, bottom: 0, width: 1, background: "#444" }} />
        <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 1, background: "#555" }} />
        <div style={{ position: "absolute", left: "80%", top: 0, bottom: 0, width: 1, background: "#444" }} />
        {/* D marker */}
        <div style={{
          position: "absolute",
          left: `${d}%`,
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: dColor,
          border: "2px solid #1e1e1e",
        }} />
        {/* K marker */}
        <div style={{
          position: "absolute",
          left: `${k}%`,
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: 12,
          height: 12,
          borderRadius: "50%",
          background: kColor,
          border: "2px solid #1e1e1e",
        }} />
      </div>
      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#666", marginTop: 2 }}>
        <span style={{ color: kColor }}>● %K</span>
        <span style={{ color: dColor }}>● %D</span>
      </div>
    </div>
  );
}

export function StochRSIPanel() {
  const [input, setInput] = useState("AAPL");
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<StochRSIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (t: string) => {
    setLoading(true);
    setError(null);
    try {
      const d = await fetchStochRSI(t);
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = () => {
    const t = input.trim().toUpperCase();
    if (!t) return;
    setTicker(t);
    load(t);
  };

  const sig = data?.signal ?? "no_data";

  return (
    <div style={{ background: "#1e1e1e", border: "1px solid #333", borderRadius: 8, padding: 16, color: "#eee", fontFamily: "monospace" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{ fontWeight: 700, fontSize: 15 }}>Stochastic RSI</span>
        <div style={{ display: "flex", gap: 6 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === "Enter" && handleQuery()}
            style={{ background: "#333", border: "1px solid #555", borderRadius: 4, color: "#eee", padding: "3px 8px", width: 90, fontFamily: "monospace" }}
          />
          <button
            onClick={handleQuery}
            style={{ background: "#1976d2", border: "none", borderRadius: 4, color: "#fff", padding: "3px 10px", cursor: "pointer" }}
          >
            查询
          </button>
        </div>
      </div>

      {loading && <div style={{ color: "#aaa", fontSize: 13 }}>加载中...</div>}
      {error && <div style={{ color: "#f44336", fontSize: 13 }}>错误：{error}</div>}

      {data && !loading && (
        <div>
          {!data.data_available && (
            <div style={{ color: "#f44336", fontSize: 13, marginBottom: 8 }}>数据获取失败</div>
          )}
          {data.data_available && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <span style={{ background: SIG_COLOR[sig], color: "#111", borderRadius: 4, padding: "2px 10px", fontWeight: 700, fontSize: 13 }}>
                  {SIG_LABEL[sig]}
                </span>
                <span style={{ fontSize: 13, color: "#bbb" }}>{ticker} · {data.as_of_date}</span>
              </div>

              <div style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#aaa" }}>
                  <span>综合评分</span>
                  <span>{data.stoch_rsi_score.toFixed(1)} / 100</span>
                </div>
                <ScoreBar score={data.stoch_rsi_score} />
              </div>

              {data.k_value !== null && data.d_value !== null && (
                <KDGauge k={data.k_value} d={data.d_value} />
              )}

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
                <div style={{ background: "#2a2a2a", borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "#aaa", marginBottom: 4 }}>%K（快线）</div>
                  <div style={{
                    fontSize: 16, fontWeight: 700,
                    color: (data.k_value ?? 50) > 80 ? "#f44336" : (data.k_value ?? 50) < 20 ? "#69f0ae" : "#ffd740",
                  }}>
                    {data.k_value !== null ? data.k_value.toFixed(1) : "—"}
                  </div>
                </div>
                <div style={{ background: "#2a2a2a", borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "#aaa", marginBottom: 4 }}>%D（慢线）</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: "#aaa" }}>
                    {data.d_value !== null ? data.d_value.toFixed(1) : "—"}
                  </div>
                </div>
              </div>

              {data.k_value !== null && data.d_value !== null && (
                <div style={{ fontSize: 12, marginBottom: 8, color: data.k_value > data.d_value ? "#69f0ae" : "#f44336" }}>
                  {data.k_value > data.d_value ? "▲ %K 高于 %D（多头占优）" : "▼ %K 低于 %D（空头占优）"}
                </div>
              )}

              <div style={{ fontSize: 12, color: "#aaa", lineHeight: 1.6, borderTop: "1px solid #333", paddingTop: 8 }}>
                {data.interpretation}
              </div>
            </>
          )}
        </div>
      )}

      {!data && !loading && !error && (
        <div style={{ color: "#666", fontSize: 13 }}>输入股票代码查询 Stochastic RSI</div>
      )}
    </div>
  );
}
