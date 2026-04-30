/**
 * ElderImpulsePanel — Elder Impulse System (F.80)
 *
 * Shows impulse color (Green/Red/Blue), EMA13, MACD histogram,
 * composite score bar, and interpretation.
 */

import { useState } from "react";
import { fetchImpulse, type ImpulseData } from "../api/client";

const SIGNAL_COLORS: Record<string, string> = {
  strong_bull: "#22c55e",
  bull:        "#86efac",
  neutral:     "#facc15",
  bear:        "#f87171",
  strong_bear: "#dc2626",
  no_data:     "#6b7280",
};

const SIGNAL_LABELS: Record<string, string> = {
  strong_bull: "极佳 — 双重多头冲量",
  bull:        "偏强 — EMA+MACD偏多",
  neutral:     "中性 — 冲量信号混合",
  bear:        "偏弱 — EMA+MACD偏空",
  strong_bear: "极弱 — 双重空头冲量",
  no_data:     "数据不足",
};

const IMPULSE_COLOR_MAP: Record<string, { bg: string; border: string; label: string }> = {
  green: { bg: "#22c55e22", border: "#22c55e44", label: "🟢 绿柱 — 买入冲量" },
  red:   { bg: "#dc262622", border: "#dc262644", label: "🔴 红柱 — 卖出冲量" },
  blue:  { bg: "#89b4fa22", border: "#89b4fa44", label: "🔵 蓝柱 — 中性信号" },
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
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#9ca3af", marginBottom: 3 }}>
        <span>0</span>
        <span style={{ color, fontWeight: 700 }}>{pct.toFixed(1)}</span>
        <span>100</span>
      </div>
      <div style={{ background: "#374151", borderRadius: 4, height: 8, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${pct}%`, background: color, borderRadius: 4, transition: "width 0.4s ease" }} />
        {[20, 40, 60, 80].map(t => (
          <div key={t} style={{ position: "absolute", left: `${t}%`, top: 0, height: "100%", width: 1, background: "#4b5563" }} />
        ))}
      </div>
    </div>
  );
}

export function ElderImpulsePanel() {
  const [input,   setInput]   = useState("AAPL");
  const [ticker,  setTicker]  = useState("AAPL");
  const [data,    setData]    = useState<ImpulseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchImpulse(input.trim().toUpperCase());
      setData(result);
      setTicker(input.trim().toUpperCase());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  const sigColor = data ? (SIGNAL_COLORS[data.signal] ?? "#6b7280") : "#6b7280";
  const sigLabel = data ? (SIGNAL_LABELS[data.signal] ?? data.signal) : "—";
  const impulseStyle = data?.impulse_color ? IMPULSE_COLOR_MAP[data.impulse_color] : null;

  return (
    <div style={{ background: "#1e1e2e", border: "1px solid #313244", borderRadius: 12, padding: 20, color: "#cdd6f4", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: "#6c7086", textTransform: "uppercase", letterSpacing: 1 }}>
          Elder Impulse · EMA(13) + MACD(12/26/9)
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#cdd6f4", marginTop: 2 }}>{ticker}</div>
      </div>

      {/* Ticker input */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === "Enter" && handleFetch()}
          placeholder="股票代码"
          style={{ flex: 1, background: "#313244", border: "1px solid #45475a", borderRadius: 6, padding: "6px 10px", color: "#cdd6f4", fontSize: 13 }}
        />
        <button
          onClick={handleFetch}
          disabled={loading}
          style={{ background: "#89b4fa", color: "#1e1e2e", border: "none", borderRadius: 6, padding: "6px 14px", fontWeight: 700, cursor: "pointer", fontSize: 13 }}
        >
          {loading ? "…" : "查询"}
        </button>
      </div>

      {error && (
        <div style={{ color: "#f38ba8", fontSize: 12, marginBottom: 10 }}>错误：{error}</div>
      )}

      {data && (
        <>
          {/* Impulse color badge */}
          {impulseStyle && (
            <div style={{
              display: "inline-block",
              background: impulseStyle.bg,
              border: `1px solid ${impulseStyle.border}`,
              borderRadius: 8, padding: "6px 14px", fontSize: 14, fontWeight: 700,
              color: "#cdd6f4", marginBottom: 10,
            }}>
              {impulseStyle.label}
            </div>
          )}

          <div style={{ marginBottom: 14 }}>
            <div style={{
              display: "inline-block",
              background: sigColor + "22",
              border: `1px solid ${sigColor}44`,
              borderRadius: 8, padding: "6px 14px", fontSize: 13, fontWeight: 700, color: sigColor,
            }}>
              {sigLabel}
            </div>
          </div>

          {data.data_available && data.ema13 !== null && (
            <>
              {/* EMA + MACD hist values */}
              <div style={{ background: "#313244", borderRadius: 8, padding: "12px 16px", marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-around", marginBottom: 8 }}>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>EMA(13)</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: "#89b4fa" }}>
                      {(data.ema13 ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 10, color: "#6c7086", marginBottom: 2 }}>MACD 柱</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: (data.macd_hist ?? 0) >= 0 ? "#a6e3a1" : "#f38ba8" }}>
                      {(data.macd_hist ?? 0).toFixed(4)}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: data.ema_rising ? "#22c55e" : "#f38ba8" }}>
                    EMA {data.ema_rising ? "↑ 上升" : "↓ 下降"}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: data.hist_rising ? "#22c55e" : "#f38ba8" }}>
                    MACD柱 {data.hist_rising ? "↑ 增强" : "↓ 减弱"}
                  </span>
                </div>
              </div>

              {/* Context tip */}
              <div style={{ background: "#181825", borderRadius: 6, padding: "6px 10px", fontSize: 11, color: "#6c7086", marginBottom: 10 }}>
                💡 绿柱=禁止做空，红柱=禁止做多，蓝柱=方向不明等待；绿→红的转变是出场信号
              </div>

              {/* Score bar */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: "#6c7086", marginBottom: 4 }}>综合得分 (0–100)</div>
                <ScoreBar score={data.impulse_score} />
              </div>
            </>
          )}

          {!data.data_available && (
            <div style={{ color: "#6c7086", fontSize: 13, marginBottom: 10 }}>数据不可用（yfinance 异常）</div>
          )}

          {data.interpretation && (
            <div style={{ background: "#313244", borderRadius: 8, padding: "8px 12px", fontSize: 12, color: "#a6adc8", lineHeight: 1.6, marginBottom: 8 }}>
              {data.interpretation}
            </div>
          )}

          <div style={{ fontSize: 10, color: "#6c7086", textAlign: "right" }}>
            {ticker} · {data.as_of_date}
          </div>
        </>
      )}
    </div>
  );
}
