/**
 * StochasticPanel — 随机指标面板
 *
 * 功能（需用户输入 ticker）：
 * - 随机评分条（0-100）
 * - 信号徽章（strong_bull / bull / neutral / bear / strong_bear）
 * - %K / %D 双轨可视化
 * - 超买（>80）/ 超卖（<20）区间标注
 * - %K 上穿/下穿 %D 金叉/死叉检测
 * - 解读文字
 *
 * Phase F.40 — Stochastic Oscillator Panel
 * 数据来源：yfinance 1 年日线（免费）
 */

import { useState } from "react";
import {
  type StochasticData,
  type StochasticSignal,
  fetchStochastic,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: StochasticSignal): string {
  if (s === "strong_bull") return "#00C087";
  if (s === "bull") return "#34d399";
  if (s === "neutral") return "#94a3b8";
  if (s === "bear") return "#f59e0b";
  if (s === "strong_bear") return "#ef4444";
  return "#475569";
}

function signalLabel(s: StochasticSignal): string {
  const labels: Record<StochasticSignal, string> = {
    strong_bull: "🟢 强势多头（%K ≥ 80）",
    bull: "✅ 多头（60-79）",
    neutral: "⚪ 中性（40-59）",
    bear: "⚠ 空头（20-39）",
    strong_bear: "🔴 强势空头（%K < 20）",
    no_data: "— 无数据",
  };
  return labels[s];
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StochScoreBar({ score, signal }: { score: number; signal: StochasticSignal }) {
  const color = signalColor(signal);
  const pct = Math.max(0, Math.min(100, score));

  return (
    <div style={{ margin: "8px 0" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 4,
          fontSize: 10,
          color: "#64748b",
        }}
      >
        <span style={{ color: "#ef4444" }}>0</span>
        <span style={{ fontSize: 16, fontWeight: 800, color }}>{score.toFixed(0)}</span>
        <span style={{ color: "#00C087" }}>100</span>
      </div>
      <div
        style={{
          position: "relative",
          background: "#1a1d24",
          borderRadius: 4,
          height: 12,
          overflow: "hidden",
        }}
      >
        {[20, 40, 60, 80].map((t) => (
          <div
            key={t}
            style={{
              position: "absolute",
              left: `${t}%`,
              top: 0, bottom: 0, width: 1,
              background: t === 20 || t === 80 ? "#475569" : "#2a2d35",
            }}
          />
        ))}
        {/* Oversold zone */}
        <div style={{ position: "absolute", left: 0, width: "20%", top: 0, bottom: 0, background: "#60a5fa11" }} />
        {/* Overbought zone */}
        <div style={{ position: "absolute", left: "80%", right: 0, top: 0, bottom: 0, background: "#f59e0b11" }} />
        <div
          style={{
            position: "absolute",
            top: 1, bottom: 1, left: 0,
            width: `${pct}%`,
            background: color,
            borderRadius: 3,
            transition: "width 0.4s",
          }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#475569", marginTop: 3 }}>
        <span style={{ color: "#60a5fa" }}>← 超卖 (20)</span>
        <span style={{ color: "#f59e0b" }}>超买 (80) →</span>
      </div>
    </div>
  );
}

/** %K and %D dual cursor bar */
function KDBar({ k, d }: { k: number | null; d: number | null }) {
  if (k == null) return null;

  const kColor = k > 80 ? "#f59e0b" : k < 20 ? "#60a5fa" : k > 50 ? "#00C087" : "#94a3b8";
  const dColor = "#a78bfa";

  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#64748b", marginBottom: 4 }}>
        <span>随机指标 0 — 100</span>
        <div style={{ display: "flex", gap: 12 }}>
          <span style={{ color: kColor }}>%K = {k.toFixed(1)}</span>
          {d != null && <span style={{ color: dColor }}>%D = {d.toFixed(1)}</span>}
        </div>
      </div>
      <div style={{ position: "relative", background: "#1a1d24", borderRadius: 4, height: 14, overflow: "hidden" }}>
        {/* Zone markers */}
        {[20, 50, 80].map((t) => (
          <div key={t} style={{
            position: "absolute", left: `${t}%`, top: 0, bottom: 0,
            width: 1, background: "#2a2d35",
          }} />
        ))}
        {/* K cursor */}
        <div style={{
          position: "absolute",
          left: `${k}%`,
          top: 1, bottom: 1,
          width: 3,
          background: kColor,
          borderRadius: 2,
          transform: "translateX(-50%)",
          zIndex: 2,
        }} />
        {/* D cursor */}
        {d != null && (
          <div style={{
            position: "absolute",
            left: `${d}%`,
            top: 3, bottom: 3,
            width: 2,
            background: dColor,
            borderRadius: 1,
            transform: "translateX(-50%)",
            opacity: 0.8,
            zIndex: 1,
          }} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function StochasticPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StochasticData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStochastic(ticker.trim().toUpperCase());
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        background: "#0E1014",
        border: "1px solid #2a2d35",
        borderRadius: 10,
        padding: 16,
        marginBottom: 16,
        fontFamily: "ui-monospace, monospace",
      }}
    >
      {/* 标题 */}
      <div
        style={{
          fontWeight: 700,
          fontSize: 14,
          color: "#e2e8f0",
          marginBottom: 12,
          borderBottom: "1px solid #2a2d35",
          paddingBottom: 8,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span>随机指标面板</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          %K(14) · %D(3) · 超买/超卖
        </span>
      </div>

      {/* 输入 */}
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Ticker（如 AAPL、SPY、NVDA）"
          style={{
            flex: 1,
            background: "#151619",
            border: "1px solid #2a2d35",
            borderRadius: 5,
            color: "#e2e8f0",
            padding: "5px 10px",
            fontSize: 12,
            fontFamily: "ui-monospace, monospace",
          }}
        />
        <button
          type="submit"
          disabled={loading || !ticker.trim()}
          style={{
            background: loading ? "#1a1d24" : "#1a2a3a",
            border: "1px solid #2a2d35",
            borderRadius: 5,
            color: loading ? "#475569" : "#60a5fa",
            padding: "5px 14px",
            fontSize: 12,
            cursor: loading || !ticker.trim() ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "计算中..." : "分析"}
        </button>
      </form>

      {/* 错误 */}
      {error && (
        <div
          style={{
            background: "#ef444422",
            border: "1px solid #ef444455",
            borderRadius: 6,
            padding: "8px 12px",
            color: "#ef4444",
            fontSize: 12,
            marginBottom: 12,
          }}
        >
          {error}
        </div>
      )}

      {/* 结果 */}
      {result && (
        <div>
          {!result.data_available && (
            <div
              style={{
                background: "#ef444422",
                border: "1px solid #ef444455",
                borderRadius: 6,
                padding: "8px 12px",
                color: "#ef4444",
                fontSize: 12,
                marginBottom: 12,
              }}
            >
              ⚠ 数据不可用。
            </div>
          )}

          {/* 信号徽章 */}
          <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap", alignItems: "center" }}>
            <span
              style={{
                display: "inline-block",
                background: signalColor(result.signal) + "22",
                border: `1px solid ${signalColor(result.signal)}55`,
                color: signalColor(result.signal),
                borderRadius: 5,
                padding: "3px 10px",
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              {signalLabel(result.signal)}
            </span>
            {result.overbought && (
              <span style={{ background: "#f59e0b22", border: "1px solid #f59e0b55", color: "#f59e0b", borderRadius: 5, padding: "3px 8px", fontSize: 11 }}>
                ⚠ 超买（%K &gt; 80）
              </span>
            )}
            {result.oversold && (
              <span style={{ background: "#60a5fa22", border: "1px solid #60a5fa55", color: "#60a5fa", borderRadius: 5, padding: "3px 8px", fontSize: 11 }}>
                ✦ 超卖（%K &lt; 20）
              </span>
            )}
            {result.recent_bull_cross && (
              <span style={{ background: "#00C08722", border: "1px solid #00C08755", color: "#00C087", borderRadius: 5, padding: "3px 8px", fontSize: 11 }}>
                ✓ 金叉（%K 上穿 %D）
              </span>
            )}
            {result.recent_bear_cross && (
              <span style={{ background: "#ef444422", border: "1px solid #ef444455", color: "#ef4444", borderRadius: 5, padding: "3px 8px", fontSize: 11 }}>
                ✗ 死叉（%K 下穿 %D）
              </span>
            )}
          </div>

          {/* 评分条 + KD 双轨 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <StochScoreBar score={result.stoch_score} signal={result.signal} />
            <KDBar k={result.k} d={result.d} />
          </div>

          {/* %K / %D 数值 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 8,
            }}
          >
            {[
              { label: "%K（快线）", value: result.k, color: "#60a5fa" },
              { label: "%D（慢线）", value: result.d, color: "#a78bfa" },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ padding: "6px 10px", background: "#0E1014", borderRadius: 6 }}>
                <div style={{ fontSize: 10, color: "#475569", marginBottom: 2 }}>{label}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color }}>
                  {value != null ? value.toFixed(1) : "—"}
                </div>
              </div>
            ))}
          </div>

          {/* 解读 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 6,
              padding: "8px 12px",
              fontSize: 11,
              color: "#94a3b8",
              lineHeight: 1.6,
              marginBottom: 10,
            }}
          >
            {result.interpretation}
          </div>

          <div style={{ fontSize: 10, color: "#475569" }}>
            数据日期：{result.as_of_date}　│　Full Stochastic %K(14) %D(3)，1 年日线　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
