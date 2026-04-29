/**
 * RSISignalPanel — RSI 动量与背离面板
 *
 * 功能（需用户输入 ticker）：
 * - RSI 评分条（0-100，直接映射 RSI 值）
 * - 信号徽章（strong_bull / bull / neutral / bear / strong_bear）
 * - RSI 值仪表盘（0-100 弧形显示）
 * - 超买/超卖区间标注（>70 超买 / <30 超卖）
 * - 看涨/看跌背离检测徽章
 * - RSI 方向（rising / falling / flat）
 * - 解读文字
 *
 * Phase F.39 — RSI Divergence Panel
 * 数据来源：yfinance 1 年日线（免费）
 */

import { useState } from "react";
import {
  type RSIData,
  type RSISignal,
  fetchRSISignal,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: RSISignal): string {
  if (s === "strong_bull") return "#00C087";
  if (s === "bull") return "#34d399";
  if (s === "neutral") return "#94a3b8";
  if (s === "bear") return "#f59e0b";
  if (s === "strong_bear") return "#ef4444";
  return "#475569";
}

function signalLabel(s: RSISignal): string {
  const labels: Record<RSISignal, string> = {
    strong_bull: "🟢 强势多头动能（RSI ≥ 80）",
    bull: "✅ 多头动能（60-79）",
    neutral: "⚪ 中性（40-59）",
    bear: "⚠ 空头动能（20-39）",
    strong_bear: "🔴 强势空头动能（< 20）",
    no_data: "— 无数据",
  };
  return labels[s];
}

function rsiZoneColor(rsi: number): string {
  if (rsi > 70) return "#f59e0b"; // overbought
  if (rsi < 30) return "#60a5fa"; // oversold
  if (rsi > 50) return "#34d399"; // bull
  return "#94a3b8";               // neutral/bear
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function RSIScoreBar({ score, signal }: { score: number; signal: RSISignal }) {
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
        {/* Zone markers at 30 and 70 */}
        {[20, 30, 40, 60, 70, 80].map((t) => (
          <div
            key={t}
            style={{
              position: "absolute",
              left: `${t}%`,
              top: 0,
              bottom: 0,
              width: 1,
              background: t === 30 || t === 70 ? "#475569" : "#2a2d35",
            }}
          />
        ))}
        {/* Oversold zone background */}
        <div
          style={{
            position: "absolute",
            left: 0,
            width: "30%",
            top: 0,
            bottom: 0,
            background: "#60a5fa11",
          }}
        />
        {/* Overbought zone background */}
        <div
          style={{
            position: "absolute",
            left: "70%",
            right: 0,
            top: 0,
            bottom: 0,
            background: "#f59e0b11",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 1,
            bottom: 1,
            left: 0,
            width: `${pct}%`,
            background: color,
            borderRadius: 3,
            transition: "width 0.4s",
          }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#475569", marginTop: 3 }}>
        <span style={{ color: "#60a5fa" }}>← 超卖 (30)</span>
        <span style={{ color: "#f59e0b" }}>超买 (70) →</span>
      </div>
    </div>
  );
}

/** RSI Gauge: horizontal bar 0-100 with value cursor */
function RSIGauge({ rsi, prevRsi }: { rsi: number | null; prevRsi: number | null }) {
  if (rsi == null) return null;
  const color = rsiZoneColor(rsi);

  return (
    <div style={{ margin: "10px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: "#64748b" }}>RSI(14)</span>
        <span style={{ fontSize: 22, fontWeight: 800, color }}>{rsi.toFixed(1)}</span>
        {prevRsi != null && (
          <span style={{ fontSize: 10, color: rsi > prevRsi ? "#00C087" : "#ef4444" }}>
            {rsi > prevRsi ? "↑" : "↓"} {Math.abs(rsi - prevRsi).toFixed(1)}
          </span>
        )}
      </div>
      <div style={{ position: "relative", background: "#1a1d24", borderRadius: 6, height: 16, overflow: "hidden" }}>
        {/* Color gradient background: red → yellow → green */}
        <div style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(to right, #ef444444 0%, #f59e0b44 30%, #94a3b844 50%, #34d39944 70%, #00C08744 100%)",
        }} />
        {/* Threshold lines */}
        {[30, 50, 70].map((t) => (
          <div key={t} style={{
            position: "absolute",
            left: `${t}%`,
            top: 0, bottom: 0,
            width: 1,
            background: "#2a2d35",
          }} />
        ))}
        {/* RSI cursor */}
        <div style={{
          position: "absolute",
          left: `${rsi}%`,
          top: 1,
          bottom: 1,
          width: 3,
          background: color,
          borderRadius: 2,
          transform: "translateX(-50%)",
          boxShadow: `0 0 6px ${color}`,
        }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#475569", marginTop: 3 }}>
        <span>0</span><span>30</span><span>50</span><span>70</span><span>100</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function RSISignalPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RSIData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRSISignal(ticker.trim().toUpperCase());
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
        <span>RSI 动量与背离</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          RSI(14) · 超买/超卖 · 背离检测
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

          {/* 信号徽章 + 区间 + 背离 */}
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
              <span
                style={{
                  background: "#f59e0b22",
                  border: "1px solid #f59e0b55",
                  color: "#f59e0b",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                ⚠ 超买（RSI &gt; 70）
              </span>
            )}
            {result.oversold && (
              <span
                style={{
                  background: "#60a5fa22",
                  border: "1px solid #60a5fa55",
                  color: "#60a5fa",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                ✦ 超卖（RSI &lt; 30）
              </span>
            )}
            {result.bullish_divergence && (
              <span
                style={{
                  background: "#00C08722",
                  border: "1px solid #00C08755",
                  color: "#00C087",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                ↗ 看涨背离
              </span>
            )}
            {result.bearish_divergence && (
              <span
                style={{
                  background: "#ef444422",
                  border: "1px solid #ef444455",
                  color: "#ef4444",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                ↘ 看跌背离
              </span>
            )}
            {result.rsi_direction && result.rsi_direction !== "flat" && (
              <span style={{ fontSize: 11, color: result.rsi_direction === "rising" ? "#00C087" : "#f59e0b" }}>
                {result.rsi_direction === "rising" ? "RSI 上升 ↑" : "RSI 下降 ↓"}
              </span>
            )}
          </div>

          {/* RSI 评分条 + 仪表 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <RSIScoreBar score={result.rsi_score} signal={result.signal} />
            <RSIGauge rsi={result.rsi} prevRsi={result.prev_rsi} />
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
            数据日期：{result.as_of_date}　│　RSI(14) · Wilder 平滑 · 背离检测窗口 20 根　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
