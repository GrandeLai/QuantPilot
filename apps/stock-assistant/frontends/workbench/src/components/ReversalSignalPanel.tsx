/**
 * ReversalSignalPanel — 短期反转信号面板
 *
 * 功能（需用户输入 ticker）：
 * - 信号徽章（strong_reversal_up / reversal_up / neutral / reversal_down / strong_reversal_down）
 * - 反转评分仪表条（-100 到 +100）
 * - 1W / 4W 相对 SPY 表现对比
 * - 成交量比值（量比）
 * - 解读文字
 *
 * Phase F.34 — Short-Term Reversal Signal
 * 理论基础：Jegadeesh (1990) 短期反转效应（1-4 周反转，与长期动量相反）
 * 数据来源：yfinance 2 年日线（免费）
 */

import { useState } from "react";
import {
  type ReversalData,
  type ReversalSignal,
  fetchReversalSignal,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: ReversalSignal): string {
  if (s === "strong_reversal_up") return "#00C087";
  if (s === "reversal_up") return "#34d399";
  if (s === "neutral") return "#94a3b8";
  if (s === "reversal_down") return "#f59e0b";
  if (s === "strong_reversal_down") return "#ef4444";
  return "#475569";
}

function signalLabel(s: ReversalSignal): string {
  const labels: Record<ReversalSignal, string> = {
    strong_reversal_up: "🟢 强多头反转（分数 ≥ 60）",
    reversal_up: "✅ 多头反转倾向（30-59）",
    neutral: "⚪ 中性（-29 to +29）",
    reversal_down: "⚠ 空头反转倾向（-59 to -30）",
    strong_reversal_down: "🔴 强空头反转（分数 ≤ -60）",
    no_data: "— 无数据",
  };
  return labels[s];
}

function fmtPct(v: number | null): string {
  if (v == null) return "—";
  const s = (v * 100).toFixed(1);
  return v >= 0 ? `+${s}%` : `${s}%`;
}

function retColor(v: number | null): string {
  if (v == null) return "#475569";
  if (v > 0.05) return "#ef4444";   // outperformed → reversal risk
  if (v > 0.01) return "#f59e0b";
  if (v > -0.01) return "#94a3b8";
  if (v > -0.05) return "#6ee7b7";
  return "#00C087";                  // deeply underperformed → reversal opportunity
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Score bar: -100 to +100 with center at 0 */
function ReversalScoreBar({ score, signal }: { score: number; signal: ReversalSignal }) {
  const color = signalColor(signal);
  const absPct = Math.abs(score) / 2;  // map to 0-50%
  const isPositive = score >= 0;

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
        <span style={{ color: "#ef4444" }}>-100 空头反转</span>
        <span style={{ fontSize: 16, fontWeight: 800, color }}>
          {score >= 0 ? "+" : ""}{score.toFixed(0)}
        </span>
        <span style={{ color: "#00C087" }}>+100 多头反转</span>
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
        {/* Center marker */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: 0,
            bottom: 0,
            width: 2,
            background: "#2a2d35",
          }}
        />
        {/* Fill bar */}
        {score !== 0 && (
          <div
            style={{
              position: "absolute",
              top: 1,
              bottom: 1,
              left: isPositive ? "50%" : `${50 - absPct}%`,
              width: `${absPct}%`,
              background: color,
              borderRadius: 3,
              transition: "all 0.4s",
            }}
          />
        )}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 8,
          color: "#475569",
          marginTop: 2,
        }}
      >
        <span>强空头</span>
        <span>中性</span>
        <span>强多头</span>
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  color,
  sub,
}: {
  label: string;
  value: string;
  color?: string;
  sub?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "5px 0",
        borderBottom: "1px solid #1a1d24",
        fontSize: 12,
      }}
    >
      <span style={{ color: "#64748b" }}>{label}</span>
      <div style={{ textAlign: "right" }}>
        <span style={{ color: color ?? "#e2e8f0", fontWeight: 600 }}>{value}</span>
        {sub && (
          <div style={{ fontSize: 9, color: "#475569" }}>{sub}</div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function ReversalSignalPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReversalData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReversalSignal(ticker.trim().toUpperCase());
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
        <span>短期反转信号</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          Jegadeesh 短期反转效应 · 1W/4W vs SPY
        </span>
      </div>

      {/* 输入 */}
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Ticker（如 AAPL、NVDA、TSLA）"
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
              ⚠ 数据不可用（yfinance 暂时无法获取）。
            </div>
          )}

          {/* 信号徽章 */}
          <div style={{ marginBottom: 10 }}>
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
          </div>

          {/* 分数仪表条 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <ReversalScoreBar score={result.reversal_score} signal={result.signal} />
          </div>

          {/* 指标明细 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <MetricRow
              label="1周相对 SPY 超额"
              value={fmtPct(result.rel_1w)}
              color={retColor(result.rel_1w)}
              sub={result.rel_1w != null && result.rel_1w < -0.02 ? "↓ 跑输 → 反转机会" : result.rel_1w != null && result.rel_1w > 0.02 ? "↑ 跑赢 → 回归风险" : undefined}
            />
            <MetricRow
              label="4周相对 SPY 超额"
              value={fmtPct(result.rel_4w)}
              color={retColor(result.rel_4w)}
              sub={result.rel_4w != null && result.rel_4w < -0.05 ? "↓ 跑输明显" : result.rel_4w != null && result.rel_4w > 0.05 ? "↑ 跑赢明显" : undefined}
            />
            <MetricRow
              label="1W 股票收益率"
              value={fmtPct(result.ret_1w)}
              color={result.ret_1w != null && result.ret_1w >= 0 ? "#6ee7b7" : "#fca5a5"}
            />
            <MetricRow
              label="4W 股票收益率"
              value={fmtPct(result.ret_4w)}
              color={result.ret_4w != null && result.ret_4w >= 0 ? "#6ee7b7" : "#fca5a5"}
            />
            <MetricRow
              label="量比（5D / 20D 均量）"
              value={result.vol_ratio != null ? `${result.vol_ratio.toFixed(2)}×` : "—"}
              color={result.vol_ratio != null && result.vol_ratio < 0.7 ? "#00C087" : result.vol_ratio != null && result.vol_ratio > 1.5 ? "#ef4444" : "#94a3b8"}
              sub={result.vol_ratio != null && result.vol_ratio < 0.7 ? "缩量 → 增强反转" : result.vol_ratio != null && result.vol_ratio > 1.5 ? "放量 → 趋势更强" : undefined}
            />
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

          {/* 说明 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 6,
              padding: "6px 10px",
              fontSize: 10,
              color: "#475569",
              lineHeight: 1.6,
            }}
          >
            <div>反转分数 = 1W超额（±40）+ 4W超额（±40）+ 量比确认（±20），clip [-100,+100]。</div>
            <div>理论：Jegadeesh (1990) 短期反转效应；与 F.33 RS 长期动量方向相反。</div>
          </div>

          <div style={{ marginTop: 8, fontSize: 10, color: "#475569" }}>
            数据日期：{result.as_of_date}　│　Benchmark: SPY　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
