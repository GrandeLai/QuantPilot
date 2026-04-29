/**
 * MACDPanel — MACD 信号面板
 *
 * 功能（需用户输入 ticker）：
 * - MACD 评分条（0-100）
 * - 信号徽章（strong_bull / bull / neutral / bear / strong_bear）
 * - MACD / Signal / Histogram 数值显示
 * - 金叉/死叉检测（近期 3 根 K 线）
 * - 柱状图扩张/收缩状态
 * - 解读文字
 *
 * Phase F.37 — MACD Signal Panel
 * 数据来源：yfinance 1 年日线（免费）
 */

import { useState } from "react";
import {
  type MACDData,
  type MACDSignal,
  fetchMACD,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: MACDSignal): string {
  if (s === "strong_bull") return "#00C087";
  if (s === "bull") return "#34d399";
  if (s === "neutral") return "#94a3b8";
  if (s === "bear") return "#f59e0b";
  if (s === "strong_bear") return "#ef4444";
  return "#475569";
}

function signalLabel(s: MACDSignal): string {
  const labels: Record<MACDSignal, string> = {
    strong_bull: "🟢 强势多头（评分 ≥ 80）",
    bull: "✅ 多头（60-79）",
    neutral: "⚪ 中性（40-59）",
    bear: "⚠ 空头（20-39）",
    strong_bear: "🔴 强势空头（< 20）",
    no_data: "— 无数据",
  };
  return labels[s];
}

function fmtVal(v: number | null, decimals = 4): string {
  return v == null ? "—" : v.toFixed(decimals);
}

function histColor(v: number | null): string {
  if (v == null) return "#475569";
  return v >= 0 ? "#00C087" : "#ef4444";
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MACDScoreBar({ score, signal }: { score: number; signal: MACDSignal }) {
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
        <span style={{ color: "#ef4444" }}>0 强势空头</span>
        <span style={{ fontSize: 16, fontWeight: 800, color }}>{score.toFixed(0)}</span>
        <span style={{ color: "#00C087" }}>100 强势多头</span>
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
              top: 0,
              bottom: 0,
              width: 1,
              background: "#2a2d35",
            }}
          />
        ))}
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
    </div>
  );
}

/** Histogram bar chart: show current vs previous histogram value */
function HistogramVisual({
  histogram,
  prevHistogram,
}: {
  histogram: number | null;
  prevHistogram: number | null;
}) {
  if (histogram == null) return null;

  const maxAbs = Math.max(
    Math.abs(histogram),
    prevHistogram != null ? Math.abs(prevHistogram) : 0,
    0.0001,
  );

  const bars = [
    { label: "前", value: prevHistogram, key: "prev" },
    { label: "当前", value: histogram, key: "curr" },
  ];

  return (
    <div
      style={{
        display: "flex",
        gap: 16,
        alignItems: "flex-end",
        height: 48,
        padding: "0 8px",
        marginTop: 8,
      }}
    >
      {bars.map(({ label, value, key }) => {
        if (value == null) return null;
        const heightPct = (Math.abs(value) / maxAbs) * 100;
        const color = value >= 0 ? "#00C087" : "#ef4444";
        return (
          <div
            key={key}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}
          >
            <div
              style={{
                width: 20,
                height: `${Math.max(4, heightPct * 0.4)}px`,
                background: color,
                borderRadius: 2,
                opacity: key === "prev" ? 0.5 : 1,
              }}
            />
            <span style={{ fontSize: 9, color: "#64748b" }}>{label}</span>
          </div>
        );
      })}
      <div style={{ fontSize: 10, color: "#64748b", marginLeft: 4, alignSelf: "center" }}>
        {histogram > 0 ? "柱状图 ↑" : "柱状图 ↓"}
        {prevHistogram != null && (
          <span style={{ marginLeft: 4, color: Math.abs(histogram) > Math.abs(prevHistogram) ? "#00C087" : "#f59e0b" }}>
            {Math.abs(histogram) > Math.abs(prevHistogram) ? "扩张" : "收缩"}
          </span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function MACDPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MACDData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMACD(ticker.trim().toUpperCase());
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
        <span>MACD 信号面板</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          EMA12/26 · Signal9 · Histogram
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

          {/* 信号徽章 + 金叉/死叉 */}
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
            {result.recent_crossover && (
              <span
                style={{
                  display: "inline-block",
                  background: result.crossover_direction === "bull" ? "#00C08722" : "#ef444422",
                  border: `1px solid ${result.crossover_direction === "bull" ? "#00C08755" : "#ef444455"}`,
                  color: result.crossover_direction === "bull" ? "#00C087" : "#ef4444",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                {result.crossover_direction === "bull" ? "✓ 近期金叉" : "✗ 近期死叉"}
              </span>
            )}
          </div>

          {/* MACD 评分条 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <MACDScoreBar score={result.macd_score} signal={result.signal} />
            <HistogramVisual histogram={result.histogram} prevHistogram={result.prev_histogram} />
          </div>

          {/* MACD 数值表 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            {[
              { label: "MACD 线", value: result.macd, color: "#60a5fa" },
              { label: "Signal 线", value: result.signal_line, color: "#a78bfa" },
              { label: "Histogram", value: result.histogram, color: histColor(result.histogram) },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                style={{
                  display: "grid",
                  gridTemplateColumns: "90px 1fr",
                  gap: 8,
                  padding: "4px 0",
                  borderBottom: "1px solid #1a1d24",
                  fontSize: 12,
                  alignItems: "center",
                }}
              >
                <span style={{ color: "#94a3b8" }}>{label}</span>
                <span style={{ color, fontWeight: 600 }}>{fmtVal(value)}</span>
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
            数据日期：{result.as_of_date}　│　EMA12/26/9 · 日线　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
