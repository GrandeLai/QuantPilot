/**
 * MAAlignmentPanel — 均线多空排列评分面板
 *
 * 功能（需用户输入 ticker）：
 * - MA 评分条（0-100）
 * - 信号徽章（full_bull / partial_bull / neutral / partial_bear / full_bear）
 * - 均线价格水位图（价格 vs SMA20/50/200 位置）
 * - 距各均线偏差百分比
 * - 金叉/死叉状态
 * - 解读文字
 *
 * Phase F.36 — Moving Average Alignment Score
 * 数据来源：yfinance 1 年日线（免费）
 */

import { useState } from "react";
import {
  type MAAlignmentData,
  type MASignal,
  fetchMAAlignment,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: MASignal): string {
  if (s === "full_bull") return "#00C087";
  if (s === "partial_bull") return "#34d399";
  if (s === "neutral") return "#94a3b8";
  if (s === "partial_bear") return "#f59e0b";
  if (s === "full_bear") return "#ef4444";
  return "#475569";
}

function signalLabel(s: MASignal): string {
  const labels: Record<MASignal, string> = {
    full_bull: "🟢 完美多头排列（评分 ≥ 80）",
    partial_bull: "✅ 部分多头排列（60-79）",
    neutral: "⚪ 中性（40-59）",
    partial_bear: "⚠ 部分空头排列（20-39）",
    full_bear: "🔴 完美空头排列（< 20）",
    no_data: "— 无数据",
  };
  return labels[s];
}

function fmtPrice(v: number | null): string {
  return v == null ? "—" : v.toFixed(2);
}

function fmtDist(v: number | null): string {
  if (v == null) return "—";
  const s = (v * 100).toFixed(1);
  return v >= 0 ? `+${s}%` : `${s}%`;
}

function distColor(v: number | null): string {
  if (v == null) return "#475569";
  if (v > 0.05) return "#00C087";
  if (v > 0) return "#6ee7b7";
  if (v > -0.05) return "#fca5a5";
  return "#ef4444";
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MAScoreBar({ score, signal }: { score: number; signal: MASignal }) {
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
        <span style={{ color: "#ef4444" }}>0 完美空头</span>
        <span style={{ fontSize: 16, fontWeight: 800, color }}>{score.toFixed(0)}</span>
        <span style={{ color: "#00C087" }}>100 完美多头</span>
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
        {/* Threshold markers at 20/40/60/80 */}
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

/** Visual MA level chart: show price and MAs as labeled price levels */
function MAPriceChart({
  price,
  sma20,
  sma50,
  sma200,
}: {
  price: number | null;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
}) {
  const allValues = [price, sma20, sma50, sma200].filter((v) => v != null) as number[];
  if (!price || allValues.length < 2) return null;

  const min = Math.min(...allValues) * 0.995;
  const max = Math.max(...allValues) * 1.005;
  const range = max - min;

  function pct(v: number): string {
    return `${Math.round(((v - min) / range) * 100)}%`;
  }

  const levels: Array<{ label: string; value: number; color: string; bold?: boolean }> = [
    { label: "价格", value: price, color: "#e2e8f0", bold: true },
    ...(sma20 ? [{ label: "SMA20", value: sma20, color: "#60a5fa" }] : []),
    ...(sma50 ? [{ label: "SMA50", value: sma50, color: "#a78bfa" }] : []),
    ...(sma200 ? [{ label: "SMA200", value: sma200, color: "#f59e0b" }] : []),
  ].sort((a, b) => b.value - a.value);

  return (
    <div
      style={{
        position: "relative",
        height: 80,
        background: "#0E1014",
        borderRadius: 6,
        border: "1px solid #1a1d24",
        margin: "8px 0",
        overflow: "hidden",
      }}
    >
      {levels.map(({ label, value, color, bold }) => (
        <div
          key={label}
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: pct(value),
            borderTop: `1px ${bold ? "solid" : "dashed"} ${color}`,
            display: "flex",
            justifyContent: "flex-end",
            paddingRight: 6,
          }}
        >
          <span
            style={{
              fontSize: 9,
              color,
              fontWeight: bold ? 700 : 400,
              background: "#0E1014",
              paddingLeft: 2,
            }}
          >
            {label} {fmtPrice(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function MAAlignmentPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MAAlignmentData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMAAlignment(ticker.trim().toUpperCase());
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
        <span>均线多空排列评分</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          SMA 20/50/200 · 金叉/死叉
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
            {result.sma50 != null && result.sma200 != null && (
              <span
                style={{
                  display: "inline-block",
                  background: result.golden_cross ? "#00C08722" : "#ef444422",
                  border: `1px solid ${result.golden_cross ? "#00C08755" : "#ef444455"}`,
                  color: result.golden_cross ? "#00C087" : "#ef4444",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                {result.golden_cross ? "✓ 金叉" : "✗ 死叉"}（SMA50 vs SMA200）
              </span>
            )}
          </div>

          {/* MA 评分条 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <MAScoreBar score={result.ma_score} signal={result.signal} />
            <MAPriceChart
              price={result.price}
              sma20={result.sma20}
              sma50={result.sma50}
              sma200={result.sma200}
            />
          </div>

          {/* 均线偏差表 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <div style={{ fontSize: 10, color: "#475569", marginBottom: 6 }}>
              当前价格：<span style={{ color: "#e2e8f0", fontWeight: 700 }}>{fmtPrice(result.price)}</span>
            </div>
            {[
              { label: "SMA20", value: result.sma20, dist: result.dist_from_20, color: "#60a5fa" },
              { label: "SMA50", value: result.sma50, dist: result.dist_from_50, color: "#a78bfa" },
              { label: "SMA200", value: result.sma200, dist: result.dist_from_200, color: "#f59e0b" },
            ].map(({ label, value, dist, color }) => (
              <div
                key={label}
                style={{
                  display: "grid",
                  gridTemplateColumns: "60px 1fr 1fr",
                  gap: 8,
                  padding: "4px 0",
                  borderBottom: "1px solid #1a1d24",
                  fontSize: 12,
                  alignItems: "center",
                }}
              >
                <span style={{ color, fontWeight: 600 }}>{label}</span>
                <span style={{ color: "#94a3b8" }}>{fmtPrice(value)}</span>
                <span style={{ color: distColor(dist), fontWeight: 600, textAlign: "right" }}>
                  {fmtDist(dist)}
                </span>
              </div>
            ))}
          </div>

          {/* 全排列状态 */}
          {(result.full_bull_align || result.full_bear_align) && (
            <div
              style={{
                background: result.full_bull_align ? "#00C08711" : "#ef444411",
                border: `1px solid ${result.full_bull_align ? "#00C08744" : "#ef444444"}`,
                borderRadius: 6,
                padding: "6px 12px",
                fontSize: 11,
                color: result.full_bull_align ? "#00C087" : "#ef4444",
                marginBottom: 10,
              }}
            >
              {result.full_bull_align
                ? "✦ 完美多头排列：SMA20 > SMA50 > SMA200，价格在最高均线上方"
                : "✦ 完美空头排列：SMA200 > SMA50 > SMA20，价格在最低均线下方"}
            </div>
          )}

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
            数据日期：{result.as_of_date}　│　SMA=简单移动均线，1 年日线　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
