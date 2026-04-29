/**
 * ADXTrendPanel — ADX 趋势强度面板
 *
 * 功能（需用户输入 ticker）：
 * - ADX 仪表条（0-100，15/25/40 阈值线）
 * - 信号徽章（strong_uptrend / uptrend / ranging / downtrend / strong_downtrend）
 * - +DI / -DI / ATR 指标卡
 * - 趋势强度等级标注
 * - 解读文字
 *
 * Phase F.35 — ADX Trend Strength Indicator
 * 理论：Wilder (1978) ADX，纯趋势强度指标（不区分方向，配合 +DI/-DI 方向确认）
 * 数据来源：yfinance 1 年日线（免费）
 */

import { useState } from "react";
import {
  type ADXData,
  type TrendSignal,
  fetchADXTrend,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function signalColor(s: TrendSignal): string {
  if (s === "strong_uptrend") return "#00C087";
  if (s === "uptrend") return "#34d399";
  if (s === "ranging") return "#94a3b8";
  if (s === "downtrend") return "#f59e0b";
  if (s === "strong_downtrend") return "#ef4444";
  return "#475569";
}

function signalLabel(s: TrendSignal): string {
  const labels: Record<TrendSignal, string> = {
    strong_uptrend: "🟢 强上升趋势（ADX ≥ 40, +DI 主导）",
    uptrend: "✅ 上升趋势（ADX ≥ 20, +DI 主导）",
    ranging: "⚪ 盘整（ADX < 20，趋势不明）",
    downtrend: "⚠ 下降趋势（ADX ≥ 20, -DI 主导）",
    strong_downtrend: "🔴 强下降趋势（ADX ≥ 40, -DI 主导）",
    no_data: "— 无数据",
  };
  return labels[s];
}

function strengthLabel(s: string | null): string {
  const labels: Record<string, string> = {
    strong: "🔥 极强趋势",
    moderate: "📈 中等趋势",
    weak: "〜 弱趋势",
    none: "— 无趋势",
  };
  return s ? (labels[s] ?? "—") : "—";
}

function fmtNum(v: number | null, dec = 2): string {
  return v == null ? "—" : v.toFixed(dec);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** ADX gauge bar with threshold lines at 15, 25, 40 */
function ADXBar({ adx, signal }: { adx: number | null; signal: TrendSignal }) {
  if (adx == null) return null;
  const pct = Math.max(0, Math.min(100, adx));
  const color = signalColor(signal);

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
        <span>ADX 0</span>
        <span style={{ fontSize: 16, fontWeight: 800, color }}>{adx.toFixed(1)}</span>
        <span>ADX 100</span>
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
        {/* Threshold markers at 15%, 25%, 40% */}
        {[15, 25, 40].map((t) => (
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
        {/* Fill bar */}
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
      <div
        style={{
          display: "flex",
          fontSize: 8,
          color: "#475569",
          marginTop: 2,
          gap: 0,
        }}
      >
        <span style={{ flex: 15 }}>弱</span>
        <span style={{ flex: 10 }}>盘整</span>
        <span style={{ flex: 15 }}>趋势</span>
        <span style={{ flex: 60, textAlign: "right" }}>强趋势</span>
      </div>
    </div>
  );
}

function DiBar({
  plusDi,
  minusDi,
}: {
  plusDi: number | null;
  minusDi: number | null;
}) {
  if (plusDi == null || minusDi == null) return null;
  const total = plusDi + minusDi;
  if (total <= 0) return null;
  const plusPct = (plusDi / total) * 100;

  return (
    <div style={{ margin: "8px 0" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 10,
          color: "#64748b",
          marginBottom: 3,
        }}
      >
        <span style={{ color: "#00C087" }}>+DI {plusDi.toFixed(1)}</span>
        <span style={{ color: "#ef4444" }}>-DI {minusDi.toFixed(1)}</span>
      </div>
      <div
        style={{
          display: "flex",
          height: 8,
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <div style={{ width: `${plusPct}%`, background: "#00C087" }} />
        <div style={{ width: `${100 - plusPct}%`, background: "#ef4444" }} />
      </div>
      <div style={{ fontSize: 9, color: "#475569", marginTop: 1 }}>
        {plusDi > minusDi ? "+DI 主导 → 多头方向" : "-DI 主导 → 空头方向"}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function ADXTrendPanel() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ADXData | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchADXTrend(ticker.trim().toUpperCase());
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
        <span>ADX 趋势强度</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          ADX · +DI · -DI · ATR（Wilder 1978）
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
              ⚠ 数据不可用（yfinance 暂时无法获取）。
            </div>
          )}

          {/* 信号徽章 + 趋势强度 */}
          <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
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
            <span
              style={{
                display: "inline-block",
                background: "#1a1d24",
                border: "1px solid #2a2d35",
                color: "#94a3b8",
                borderRadius: 5,
                padding: "3px 10px",
                fontSize: 11,
              }}
            >
              {strengthLabel(result.trend_strength)}
            </span>
          </div>

          {/* ADX 仪表条 */}
          <div
            style={{
              background: "#151619",
              border: "1px solid #2a2d35",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 10,
            }}
          >
            <ADXBar adx={result.adx} signal={result.signal} />
            <DiBar plusDi={result.plus_di} minusDi={result.minus_di} />
          </div>

          {/* 指标卡 */}
          <div
            style={{
              display: "flex",
              gap: 8,
              marginBottom: 10,
              flexWrap: "wrap",
            }}
          >
            {[
              { label: "+DI（多头方向强度）", value: fmtNum(result.plus_di), color: "#00C087" },
              { label: "-DI（空头方向强度）", value: fmtNum(result.minus_di), color: "#ef4444" },
              { label: "ATR（平均真实波幅）", value: fmtNum(result.atr, 3), color: "#94a3b8" },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                style={{
                  flex: 1,
                  background: "#0E1014",
                  border: "1px solid #2a2d35",
                  borderRadius: 6,
                  padding: "8px 10px",
                  textAlign: "center",
                  minWidth: 80,
                }}
              >
                <div style={{ fontSize: 16, fontWeight: 700, color }}>{value}</div>
                <div style={{ fontSize: 9, color: "#475569", marginTop: 2 }}>{label}</div>
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
            <div>ADX &lt; 20：盘整，均值回归 │ ADX 20-40：趋势 │ ADX &gt; 40：强趋势</div>
            <div>+DI &gt; -DI：多头方向 │ -DI &gt; +DI：空头方向（ADX 只测强度）</div>
          </div>

          <div style={{ marginTop: 8, fontSize: 10, color: "#475569" }}>
            数据日期：{result.as_of_date}　│　Period=14（Wilder 标准）　│　不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
