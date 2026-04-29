/**
 * QuantSignalsPanel — 量化信号面板（Beneish M-Score + Russell 调仓预览）
 *
 * 功能：
 * - Beneish M-Score：8 维财务比率盈利操纵检测
 * - Russell 调仓预览：市值排名 → 指数归属 + 年度调仓信号
 *
 * Phase F.5 — #0E1014 / #151619 / #00C087 dark-theme tokens
 */
import React, { useState } from "react";
import {
  type BeneishMScoreData,
  type QuantSignalsSummary,
  type RussellMembershipData,
  fetchQuantSignalsSummary,
} from "../api/client";

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function formatCap(usd: number): string {
  if (usd >= 1e12) return `$${(usd / 1e12).toFixed(2)}T`;
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(2)}B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(1)}M`;
  return `$${usd.toLocaleString()}`;
}

function riskColor(level: BeneishMScoreData["risk_level"]): string {
  if (level === "safe") return "#00C087";
  if (level === "grey") return "#f59e0b";
  return "#ef4444";
}

function riskLabel(level: BeneishMScoreData["risk_level"]): string {
  if (level === "safe") return "安全";
  if (level === "grey") return "灰色区";
  return "高风险";
}

function signalColor(sig: RussellMembershipData["rebalance_signal"]): string {
  if (sig === "likely_add_1000" || sig === "likely_add_2000") return "#00C087";
  if (sig === "likely_drop_1000" || sig === "likely_drop_2000") return "#ef4444";
  if (sig === "stable") return "#64748b";
  return "#94a3b8";
}

function signalLabel(sig: RussellMembershipData["rebalance_signal"]): string {
  const labels: Record<RussellMembershipData["rebalance_signal"], string> = {
    likely_add_1000: "↑ 可能纳入 R1000",
    likely_drop_1000: "↓ 可能移出 R1000",
    likely_add_2000: "↑ 可能纳入 R2000",
    likely_drop_2000: "↓ 可能移出 R2000",
    stable: "稳定",
    unknown: "未知",
  };
  return labels[sig] ?? sig;
}

// ---------------------------------------------------------------------------
// 子组件：信号强度进度条
// ---------------------------------------------------------------------------

function ProximityBar({
  value,
  color = "#f59e0b",
}: {
  value: number;
  color?: string;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
      <div
        style={{
          flex: 1,
          height: 6,
          background: "#2a2d35",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.round(value * 100)}%`,
            height: "100%",
            background: color,
            borderRadius: 3,
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <span style={{ color, minWidth: 36, textAlign: "right" }}>
        {(value * 100).toFixed(0)}%
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 子组件：Beneish M-Score 区块
// ---------------------------------------------------------------------------

function BeneishSection({ b }: { b: BeneishMScoreData }) {
  const rc = riskColor(b.risk_level);
  const rl = riskLabel(b.risk_level);

  const RATIO_LABELS: Record<string, string> = {
    DSRI: "应收账款天数指数",
    GMI: "毛利率指数",
    AQI: "资产质量指数",
    SGI: "收入增长指数",
    DEPI: "折旧率指数",
    SGAI: "销售费用指数",
    LVGI: "杠杆指数",
    TATA: "总应计项目/总资产",
  };

  return (
    <div
      style={{
        background: "#151619",
        border: "1px solid #2a2d35",
        borderRadius: 8,
        padding: "12px 14px",
        marginBottom: 10,
      }}
    >
      {/* 小标题 */}
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: "#94a3b8",
          marginBottom: 10,
          textTransform: "uppercase",
          letterSpacing: 1,
        }}
      >
        Beneish M-Score — 盈利操纵检测
      </div>

      {/* 评分 + 风险等级 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 10,
        }}
      >
        <div>
          <span style={{ fontSize: 30, fontWeight: 700, color: rc }}>
            {b.m_score.toFixed(3)}
          </span>
          <span
            style={{
              marginLeft: 10,
              fontSize: 12,
              padding: "2px 10px",
              borderRadius: 4,
              background: rc + "22",
              color: rc,
              fontWeight: 700,
            }}
          >
            {rl}
          </span>
        </div>
        <div
          style={{
            fontSize: 11,
            color: "#64748b",
            maxWidth: 220,
            textAlign: "right",
            lineHeight: 1.4,
          }}
        >
          {b.interpretation}
        </div>
      </div>

      {/* 阈值说明 */}
      <div
        style={{
          display: "flex",
          gap: 6,
          marginBottom: 12,
          fontSize: 10,
          color: "#475569",
        }}
      >
        <span style={{ color: "#00C087" }}>安全 &lt; -2.22</span>
        <span>│</span>
        <span style={{ color: "#f59e0b" }}>灰色 -2.22~-1.78</span>
        <span>│</span>
        <span style={{ color: "#ef4444" }}>高风险 &gt; -1.78</span>
      </div>

      {/* 8 个比率明细 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 5,
        }}
      >
        {Object.entries(b.ratios).map(([key, val]) => (
          <div
            key={key}
            style={{
              background: "#0E1014",
              border: "1px solid #2a2d35",
              borderRadius: 5,
              padding: "5px 9px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#e2e8f0" }}>
                {key}
              </div>
              <div style={{ fontSize: 9, color: "#475569" }}>
                {RATIO_LABELS[key] ?? key}
              </div>
            </div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#94a3b8" }}>
              {val.toFixed(4)}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 8, fontSize: 10, color: "#475569" }}>
        数据日期：{b.as_of_date}　│　来源：yfinance　│　不构成投资建议
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 子组件：Russell 调仓预览区块
// ---------------------------------------------------------------------------

function RussellSection({ r }: { r: RussellMembershipData }) {
  const sc = signalColor(r.rebalance_signal);
  const sl = signalLabel(r.rebalance_signal);

  const indexColor =
    r.current_index === "Russell 1000"
      ? "#00C087"
      : r.current_index === "Russell 2000"
      ? "#3b82f6"
      : "#64748b";

  return (
    <div
      style={{
        background: "#151619",
        border: "1px solid #2a2d35",
        borderRadius: 8,
        padding: "12px 14px",
      }}
    >
      {/* 小标题 */}
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: "#94a3b8",
          marginBottom: 10,
          textTransform: "uppercase",
          letterSpacing: 1,
        }}
      >
        Russell 指数调仓预览
      </div>

      {/* 当前归属 + 市值 */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 12,
        }}
      >
        <div>
          <span
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: indexColor,
            }}
          >
            {r.current_index}
          </span>
          {r.estimated_rank && (
            <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
              估算排名 #{r.estimated_rank.toLocaleString()}
            </div>
          )}
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#e2e8f0" }}>
            {formatCap(r.market_cap_usd)}
          </div>
          <div style={{ fontSize: 10, color: "#64748b" }}>市值（USD）</div>
        </div>
      </div>

      {/* 边界接近度 */}
      <div style={{ marginBottom: 12 }}>
        <div
          style={{
            fontSize: 11,
            color: "#64748b",
            marginBottom: 4,
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>边界接近度（越高越接近调仓线）</span>
        </div>
        <ProximityBar value={r.proximity_score} color="#f59e0b" />
      </div>

      {/* 调仓信号 */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 10,
        }}
      >
        <div style={{ fontSize: 11, color: "#64748b" }}>调仓信号：</div>
        <div
          style={{
            fontSize: 13,
            fontWeight: 700,
            padding: "3px 12px",
            borderRadius: 4,
            background: sc + "22",
            color: sc,
          }}
        >
          {sl}
        </div>
      </div>

      {/* 规则说明 */}
      <div
        style={{
          background: "#0E1014",
          border: "1px solid #2a2d35",
          borderRadius: 6,
          padding: "7px 10px",
          fontSize: 10,
          color: "#475569",
          lineHeight: 1.6,
        }}
      >
        <div>Russell 规则：每年 6 月末市值重排 → R1000=排名 1-1000，R2000=1001-3000</div>
        <div>调入前 5-10 日历史超额 1-3%（被动资金被迫追仓）</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主组件
// ---------------------------------------------------------------------------

export default function QuantSignalsPanel() {
  const [inputTicker, setInputTicker] = useState("AAPL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuantSignalsSummary | null>(null);

  async function handleQuery() {
    if (!inputTicker.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await fetchQuantSignalsSummary(inputTicker.trim().toUpperCase());
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "查询失败");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    background: "#0E1014",
    border: "1px solid #2a2d35",
    borderRadius: 4,
    color: "#e2e8f0",
    padding: "6px 10px",
    fontSize: 13,
    outline: "none",
    width: 120,
  };

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
        <span>量化信号（Beneish M-Score + Russell 调仓预览）</span>
        <span style={{ fontSize: 10, color: "#475569", fontWeight: 400 }}>
          数据来源：yfinance
        </span>
      </div>

      {/* 查询栏 */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 14,
          alignItems: "center",
        }}
      >
        <input
          value={inputTicker}
          onChange={(e) => setInputTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleQuery()}
          placeholder="AAPL"
          style={inputStyle}
        />
        <button
          onClick={handleQuery}
          disabled={loading}
          style={{
            background: loading ? "#1f2937" : "#00C087",
            color: loading ? "#94a3b8" : "#0E1014",
            border: "none",
            borderRadius: 6,
            padding: "6px 18px",
            fontWeight: 700,
            fontSize: 13,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "查询中..." : "查询"}
        </button>
      </div>

      {/* 错误提示 */}
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

      {/* 结果区 */}
      {result && (
        <>
          {result.beneish ? (
            <BeneishSection b={result.beneish} />
          ) : (
            <div
              style={{
                background: "#151619",
                border: "1px solid #2a2d35",
                borderRadius: 8,
                padding: "10px 14px",
                marginBottom: 10,
                fontSize: 12,
                color: "#64748b",
              }}
            >
              Beneish M-Score：暂无财务报表数据（需 ≥2 年历史数据）
            </div>
          )}

          {result.russell ? (
            <RussellSection r={result.russell} />
          ) : (
            <div
              style={{
                background: "#151619",
                border: "1px solid #2a2d35",
                borderRadius: 8,
                padding: "10px 14px",
                fontSize: 12,
                color: "#64748b",
              }}
            >
              Russell 归属：暂无市值数据
            </div>
          )}
        </>
      )}

      {/* 空态提示 */}
      {!result && !loading && !error && (
        <div
          style={{
            textAlign: "center",
            color: "#475569",
            fontSize: 12,
            padding: "20px 0",
          }}
        >
          输入股票代码后点击"查询"，获取 Beneish M-Score 和 Russell 调仓预览
        </div>
      )}
    </div>
  );
}
