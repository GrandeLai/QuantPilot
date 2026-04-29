/**
 * BollingerPanel — 布林带挤压面板
 *
 * 功能（需用户输入 ticker）：
 * - BB 评分条（0-100）
 * - 信号徽章（strong_bull / bull / neutral / bear / strong_bear）
 * - %B 位置指示器（0 = 下轨，0.5 = 中轨，1 = 上轨）
 * - 布林带宽度百分位（6 个月历史对比）
 * - 挤压状态徽章（squeeze_active）
 * - 均值、上轨、下轨数值
 * - 解读文字
 *
 * Phase F.38 — Bollinger Band Squeeze Panel
 * 数据来源：yfinance 1 年日线（免费）
 */

import { useState } from "react";
import {
  type BollingerData,
  type BBSignal,
  fetchBollinger,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: BBSignal): string {
  if (s === "strong_bull") return "#00C087";
  if (s === "bull") return "#34d399";
  if (s === "neutral") return "#94a3b8";
  if (s === "bear") return "#f59e0b";
  if (s === "strong_bear") return "#ef4444";
  return "#475569";
}

function signalLabel(s: BBSignal): string {
  const labels: Record<BBSignal, string> = {
    strong_bull: "🟢 强势多头（价格近上轨）",
    bull: "✅ 多头（价格高于中轨）",
    neutral: "⚪ 中性（价格近中轨）",
    bear: "⚠ 空头（价格低于中轨）",
    strong_bear: "🔴 强势空头（价格近下轨）",
    no_data: "— 无数据",
  };
  return labels[s];
}

function fmtPrice(v: number | null): string {
  return v == null ? "—" : v.toFixed(2);
}

function fmtPct(v: number | null): string {
  return v == null ? "—" : `${(v * 100).toFixed(1)}%`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function BBScoreBar({ score, signal }: { score: number; signal: BBSignal }) {
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
        <span style={{ color: "#ef4444" }}>0 强空</span>
        <span style={{ fontSize: 16, fontWeight: 800, color }}>{score.toFixed(0)}</span>
        <span style={{ color: "#00C087" }}>100 强多</span>
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

/** %B visual: horizontal slider 0 → 1 with band labels */
function PctBIndicator({ pctB }: { pctB: number | null }) {
  if (pctB == null) return null;
  // Clamp for visual (can exceed 0-1 if price outside bands)
  const displayPct = Math.max(0, Math.min(100, pctB * 100));
  const color = pctB >= 0.8 ? "#00C087" : pctB >= 0.5 ? "#34d399" : pctB >= 0.2 ? "#f59e0b" : "#ef4444";

  return (
    <div style={{ margin: "12px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#64748b", marginBottom: 4 }}>
        <span>下轨 (0)</span>
        <span>中轨 (0.5)</span>
        <span>上轨 (1.0)</span>
      </div>
      <div style={{ position: "relative", background: "#1a1d24", borderRadius: 4, height: 10 }}>
        {/* Center marker */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: 0,
            bottom: 0,
            width: 1,
            background: "#2a2d35",
          }}
        />
        {/* Fill from 0 to pctB */}
        <div
          style={{
            position: "absolute",
            top: 1,
            bottom: 1,
            left: 0,
            width: `${displayPct}%`,
            background: `${color}66`,
            borderRadius: 3,
          }}
        />
        {/* Cursor */}
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: `${displayPct}%`,
            transform: "translateX(-50%)",
            width: 3,
            background: color,
            borderRadius: 2,
          }}
        />
      </div>
      <div style={{ textAlign: "center", fontSize: 11, color, fontWeight: 600, marginTop: 4 }}>
        %B = {pctB.toFixed(2)}
      </div>
    </div>
  );
}

/** Bandwidth percentile bar */
function BWPercentileBar({ percentile }: { percentile: number | null }) {
  if (percentile == null) return null;
  const color = percentile < 20 ? "#f59e0b" : percentile > 80 ? "#60a5fa" : "#94a3b8";
  return (
    <div style={{ margin: "8px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#64748b", marginBottom: 3 }}>
        <span>窄（挤压）</span>
        <span style={{ color, fontWeight: 600, fontSize: 11 }}>带宽百分位 {percentile.toFixed(0)}%</span>
        <span>宽（扩张）</span>
      </div>
      <div style={{ background: "#1a1d24", borderRadius: 4, height: 8, overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${percentile}%`,
            background: color,
            borderRadius: 3,
            transition: "width 0.4s",
          }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function BollingerPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BollingerData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBollinger(ticker.trim().toUpperCase());
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
        <span>布林带挤压面板</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          SMA20 ± 2σ · %B · Squeeze
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

          {/* 信号徽章 + 挤压标志 */}
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
            {result.squeeze_active && (
              <span
                style={{
                  display: "inline-block",
                  background: "#f59e0b22",
                  border: "1px solid #f59e0b55",
                  color: "#f59e0b",
                  borderRadius: 5,
                  padding: "3px 8px",
                  fontSize: 11,
                }}
              >
                ⚡ 布林挤压中（低波动）
              </span>
            )}
          </div>

          {/* 评分条 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <BBScoreBar score={result.bb_score} signal={result.signal} />
            <PctBIndicator pctB={result.pct_b} />
          </div>

          {/* 带宽百分位 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <BWPercentileBar percentile={result.bandwidth_percentile} />
            <div style={{ fontSize: 10, color: "#64748b", marginTop: 4 }}>
              带宽：<span style={{ color: "#e2e8f0", fontWeight: 600 }}>{result.bandwidth?.toFixed(2)}%</span>
              　│
              带宽百分位基于近 6 个月历史（0 = 历史最窄，100 = 历史最宽）
            </div>
          </div>

          {/* 均线和轨道数值 */}
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
              { label: "上轨", value: result.upper, color: "#00C087" },
              { label: "中轨 (SMA20)", value: result.middle, color: "#60a5fa" },
              { label: "下轨", value: result.lower, color: "#ef4444" },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                style={{
                  display: "grid",
                  gridTemplateColumns: "100px 1fr 1fr",
                  gap: 8,
                  padding: "4px 0",
                  borderBottom: "1px solid #1a1d24",
                  fontSize: 12,
                  alignItems: "center",
                }}
              >
                <span style={{ color, fontWeight: 600 }}>{label}</span>
                <span style={{ color: "#94a3b8" }}>{fmtPrice(value)}</span>
                <span style={{ color: "#64748b", textAlign: "right", fontSize: 11 }}>
                  {result.price != null && value != null
                    ? `${((result.price - value) / value * 100).toFixed(1)}%`
                    : "—"}
                </span>
              </div>
            ))}
            {/* %B row */}
            <div style={{ padding: "4px 0", fontSize: 11, color: "#64748b", marginTop: 4 }}>
              %B = {result.pct_b != null ? result.pct_b.toFixed(2) : "—"}
              　（{fmtPct(result.pct_b)} 位置，0=下轨 / 0.5=中轨 / 1=上轨）
            </div>
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
            数据日期：{result.as_of_date}　│　SMA20 ± 2σ，1 年日线　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
