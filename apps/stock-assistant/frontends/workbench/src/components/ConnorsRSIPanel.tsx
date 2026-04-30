import { useState } from "react";
import { fetchCRSI, type CRSIData } from "../api/client";

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

export function ConnorsRSIPanel() {
  const [ticker, setTicker] = useState("AAPL");
  const [input, setInput] = useState("AAPL");
  const [data, setData] = useState<CRSIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (t: string) => {
    setLoading(true);
    setError(null);
    try {
      const d = await fetchCRSI(t);
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
        <span style={{ fontWeight: 700, fontSize: 15 }}>Connors RSI (CRSI)</span>
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
              {/* Signal badge */}
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <span style={{ background: SIG_COLOR[sig], color: "#111", borderRadius: 4, padding: "2px 10px", fontWeight: 700, fontSize: 13 }}>
                  {SIG_LABEL[sig]}
                </span>
                <span style={{ fontSize: 13, color: "#bbb" }}>{ticker} · {data.as_of_date}</span>
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#aaa" }}>
                  <span>综合评分</span>
                  <span>{data.crsi_score.toFixed(1)} / 100</span>
                </div>
                <ScoreBar score={data.crsi_score} />
              </div>

              {/* Component values */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8, marginBottom: 10 }}>
                {[
                  { label: "CRSI", value: data.crsi_value },
                  { label: "RSI(3)", value: data.rsi3 },
                  { label: "连涨跌RSI", value: data.streak_rsi },
                  { label: "百分位", value: data.percent_rank },
                ].map(({ label, value }) => (
                  <div key={label} style={{ background: "#2a2a2a", borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
                    <div style={{ fontSize: 11, color: "#aaa", marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: value !== null && value > 50 ? "#69f0ae" : "#f44336" }}>
                      {value !== null ? value.toFixed(1) : "—"}
                    </div>
                  </div>
                ))}
              </div>

              {/* CRSI thresholds annotation */}
              {data.crsi_value !== null && (
                <div style={{ fontSize: 12, color: data.crsi_value > 70 ? "#ff6d00" : data.crsi_value < 30 ? "#69f0ae" : "#bbb", marginBottom: 8 }}>
                  {data.crsi_value > 70 ? "⚠ 超买区间（>70）" : data.crsi_value < 30 ? "✓ 超卖区间（<30）" : "中性区间（30~70）"}
                </div>
              )}

              {/* Interpretation */}
              <div style={{ fontSize: 12, color: "#aaa", lineHeight: 1.6, borderTop: "1px solid #333", paddingTop: 8 }}>
                {data.interpretation}
              </div>
            </>
          )}
        </div>
      )}

      {!data && !loading && !error && (
        <div style={{ color: "#666", fontSize: 13 }}>输入股票代码查询 Connors RSI</div>
      )}
    </div>
  );
}
