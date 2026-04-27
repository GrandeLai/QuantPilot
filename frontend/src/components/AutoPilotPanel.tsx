/**
 * AutoPilotPanel — 一键 AutoPilot 流水线面板
 *
 * 左侧：配置表单（symbol / timeframe / date range / initial cash）
 * 右侧：流程进度 + 复盘报告（或空状态提示）
 */

import { useEffect, useRef, useState } from "react";
import {
  Activity,
  Brain,
  CheckCircle2,
  ChevronRight,
  Circle,
  Loader2,
  XCircle,
  Zap,
} from "lucide-react";
import {
  getPipelineJob,
  startPipeline,
  type PipelineJobState,
  type PipelineResult,
  type PipelineRunRequest,
} from "../api/client";

// ── 常量 ─────────────────────────────────────────────────────────────────────

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  buy: { label: "买入", color: "text-green-400" },
  sell: { label: "卖出", color: "text-red-400" },
  hold: { label: "观望", color: "text-[#8b949e]" },
};

const REGIME_LABELS: Record<string, string> = {
  trend: "趋势行情",
  range: "震荡行情",
  high_volatility: "高波动",
};

const SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT"];
const TIMEFRAMES = ["1h", "4h", "1d", "1w"];

// ── 工具函数 ──────────────────────────────────────────────────────────────────

const pct = (v: number) => `${(v * 100).toFixed(2)}%`;

// ── 子组件 ─────────────────────────────────────────────────────────────────────

function StepIcon({ status }: { status: string }) {
  if (status === "done" || status === "skipped")
    return <CheckCircle2 size={16} className="text-green-400 shrink-0" />;
  if (status === "running")
    return <Loader2 size={16} className="text-[#2962ff] animate-spin shrink-0" />;
  if (status === "error")
    return <XCircle size={16} className="text-red-400 shrink-0" />;
  return <Circle size={16} className="text-[#434651] shrink-0" />;
}

function ReviewReport({ result }: { result: PipelineResult }) {
  // ── 1. 核心 ML 指标 ────────────────────────────────────────────────────────
  const mlMetrics = [
    { label: "特征数量", value: result.feature_count?.toString() ?? "—" },
    { label: "验证窗口", value: result.validation_windows?.toString() ?? "—" },
    {
      label: "平均精度",
      value: result.mean_accuracy != null ? pct(result.mean_accuracy) : "—",
    },
    {
      label: "平均策略收益",
      value:
        result.mean_strategy_return != null
          ? pct(result.mean_strategy_return)
          : "—",
    },
  ];

  // ── 2. 信号 + 市场状态 ────────────────────────────────────────────────────
  const actionInfo = result.signal_action
    ? (ACTION_LABELS[result.signal_action] ?? { label: result.signal_action, color: "text-[#8b949e]" })
    : null;

  // ── 3. 因子重要度 ─────────────────────────────────────────────────────────
  const featureEntries = result.feature_importance
    ? Object.entries(result.feature_importance)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 8)
    : [];
  const maxFeatureVal = featureEntries.length > 0 ? featureEntries[0][1] : 1;

  // ── 4. Walk-forward 窗口表 ────────────────────────────────────────────────
  const windowMetrics = result.window_metrics ?? [];

  // ── 5. 推荐策略 ──────────────────────────────────────────────────────────
  const recommendedStrategies = result.recommended_strategy_ids ?? [];

  return (
    <div className="flex flex-col gap-4">
      {/* 1. 核心 ML 指标 2×2 */}
      <div className="grid grid-cols-2 gap-3">
        {mlMetrics.map((m) => (
          <div
            key={m.label}
            className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-3"
          >
            <div className="text-xs text-[#8b949e] mb-1">{m.label}</div>
            <div className="text-sm font-semibold text-white">{m.value}</div>
          </div>
        ))}
      </div>

      {/* 2. 信号 + 市场状态 */}
      <div className="bg-[#1e222d] border border-[#2a2e39] rounded-xl p-4 flex flex-col gap-3">
        <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-1">
          信号 · 市场状态
        </div>

        <div className="flex flex-wrap gap-4">
          {/* 信号动作 */}
          {actionInfo && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-[#8b949e]">信号</span>
              <span className={`text-base font-bold ${actionInfo.color}`}>
                {actionInfo.label}
              </span>
            </div>
          )}

          {/* 置信度 */}
          {result.signal_confidence != null && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-[#8b949e]">置信度</span>
              <span className="text-base font-bold text-white">
                {pct(result.signal_confidence)}
              </span>
            </div>
          )}

          {/* 市场状态 */}
          {result.market_regime && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-[#8b949e]">市场状态</span>
              <span className="text-base font-semibold text-white">
                {REGIME_LABELS[result.market_regime] ?? result.market_regime}
              </span>
            </div>
          )}

          {/* 反转概率 */}
          {result.reversal_probability != null && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-[#8b949e]">反转概率</span>
              <span className="text-base font-semibold text-white">
                {pct(result.reversal_probability)}
              </span>
            </div>
          )}
        </div>

        {/* 反转证据 */}
        {result.reversal_evidence && result.reversal_evidence.length > 0 && (
          <ul className="mt-1 flex flex-col gap-1">
            {result.reversal_evidence.slice(0, 3).map((ev, i) => (
              <li key={i} className="text-xs text-[#8b949e] flex gap-1.5">
                <span className="text-[#2962ff] shrink-0">•</span>
                {ev}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 3. 因子重要度条形图 */}
      {featureEntries.length > 0 && (
        <div className="bg-[#1e222d] border border-[#2a2e39] rounded-xl p-4">
          <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
            因子重要度 Top {featureEntries.length}
          </div>
          <div className="flex flex-col gap-2">
            {featureEntries.map(([name, val]) => (
              <div key={name} className="flex items-center gap-2">
                <span
                  className="text-xs text-[#8b949e] shrink-0 truncate"
                  style={{ width: "6rem" }}
                  title={name}
                >
                  {name}
                </span>
                <div className="flex-1 h-1.5 bg-[#2a2e39] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#2962ff] rounded-full"
                    style={{
                      width: `${((val / maxFeatureVal) * 100).toFixed(1)}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-white shrink-0 w-10 text-right">
                  {val.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Walk-forward 窗口表 */}
      {windowMetrics.length > 0 && (
        <div className="bg-[#1e222d] border border-[#2a2e39] rounded-xl p-4">
          <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
            Walk-Forward 窗口结果
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[#8b949e]">
                <th className="text-left pb-2 font-normal">窗口</th>
                <th className="text-right pb-2 font-normal">精度</th>
                <th className="text-right pb-2 font-normal">收益</th>
                <th className="text-right pb-2 font-normal">训练</th>
                <th className="text-right pb-2 font-normal">测试</th>
              </tr>
            </thead>
            <tbody>
              {windowMetrics.map((w) => (
                <tr
                  key={w.window}
                  className="border-t border-[#2a2e39]"
                >
                  <td className="py-1.5 text-[#8b949e]">#{w.window}</td>
                  <td className="py-1.5 text-right text-white">
                    {pct(w.accuracy)}
                  </td>
                  <td
                    className={`py-1.5 text-right font-semibold ${
                      w.strategy_return >= 0
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    {pct(w.strategy_return)}
                  </td>
                  <td className="py-1.5 text-right text-[#8b949e]">
                    {w.train_size}
                  </td>
                  <td className="py-1.5 text-right text-[#8b949e]">
                    {w.test_size}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 5. 推荐策略 */}
      {recommendedStrategies.length > 0 && (
        <div className="bg-[#1e222d] border border-[#2a2e39] rounded-xl p-4">
          <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
            推荐策略
          </div>
          <div className="flex flex-wrap gap-2">
            {recommendedStrategies.map((id) => (
              <span
                key={id}
                className="px-3 py-1 rounded-full bg-[#2962ff]/20 text-[#2962ff] text-xs font-medium border border-[#2962ff]/30"
              >
                {id}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── 主组件 ─────────────────────────────────────────────────────────────────────

export default function AutoPilotPanel() {
  // 表单状态
  const [symbol, setSymbol] = useState("BTC-USDT");
  const [timeframe, setTimeframe] = useState("1d");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [initialCash, setInitialCash] = useState("10000");

  // 运行状态
  const [launching, setLaunching] = useState(false);
  const [job, setJob] = useState<PipelineJobState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isRunning =
    job !== null && (job.status === "pending" || job.status === "running");

  // ── 清理 ────────────────────────────────────────────────────────────────────
  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  // ── 轮询 ────────────────────────────────────────────────────────────────────
  async function pollJob(jobId: string) {
    try {
      const state = await getPipelineJob(jobId);
      setJob(state);
      if (state.status === "done" || state.status === "error") stopPolling();
    } catch (e) {
      setError(String(e));
      stopPolling();
    }
  }

  // ── 启动 ────────────────────────────────────────────────────────────────────
  async function handleStart() {
    setLaunching(true);
    setError(null);
    setJob(null);
    stopPolling();

    const req: PipelineRunRequest = {
      symbol,
      timeframe,
      start_date: startDate,
      end_date: endDate,
      initial_cash: Number(initialCash),
    };

    try {
      const { job_id } = await startPipeline(req);
      await pollJob(job_id); // immediate first poll
      pollRef.current = setInterval(() => void pollJob(job_id), 2000);
    } catch (e) {
      setError(String(e));
    } finally {
      setLaunching(false);
    }
  }

  // ── 状态徽章 ────────────────────────────────────────────────────────────────
  function StatusBadge() {
    if (!job) return null;
    if (job.status === "done")
      return (
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs font-medium">
          <CheckCircle2 size={11} />
          全部完成
        </span>
      );
    if (job.status === "error")
      return (
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-xs font-medium">
          <XCircle size={11} />
          执行失败
        </span>
      );
    return (
      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#2962ff]/20 text-[#2962ff] text-xs font-medium">
        <Loader2 size={11} className="animate-spin" />
        进行中
      </span>
    );
  }

  // ── 是否有复盘报告可展示 ──────────────────────────────────────────────────────
  const hasResult = job?.result != null && Object.keys(job.result).length > 0;

  // ── 渲染 ────────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-full gap-4 p-4 min-h-0">
      {/* ───────── 左侧：配置表单 ───────── */}
      <aside className="w-60 shrink-0 flex flex-col gap-4">
        {/* 标题 */}
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-[#2962ff]" />
          <span className="text-sm font-semibold text-white">AutoPilot 配置</span>
        </div>

        {/* Symbol */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-[#8b949e]">交易对</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full bg-[#1e222d] border border-[#2a2e39] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#2962ff]"
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Timeframe */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-[#8b949e]">时间周期</label>
          <div className="grid grid-cols-4 gap-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`text-xs py-1.5 rounded-lg border transition-colors ${
                  timeframe === tf
                    ? "bg-[#2962ff]/20 border-[#2962ff] text-[#2962ff]"
                    : "border-[#2a2e39] text-[#8b949e] hover:border-[#434651]"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Date range */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-[#8b949e]">开始日期</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full bg-[#1e222d] border border-[#2a2e39] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#2962ff]"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-[#8b949e]">结束日期</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full bg-[#1e222d] border border-[#2a2e39] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#2962ff]"
          />
        </div>

        {/* Initial cash */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-[#8b949e]">初始资金 (USDT)</label>
          <input
            type="number"
            value={initialCash}
            min={100}
            step={100}
            onChange={(e) => setInitialCash(e.target.value)}
            className="w-full bg-[#1e222d] border border-[#2a2e39] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#2962ff]"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-400">
            {error}
          </div>
        )}

        {/* Start button */}
        <button
          onClick={() => void handleStart()}
          disabled={launching || isRunning}
          className={`flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-semibold transition-colors ${
            launching || isRunning
              ? "bg-[#2962ff]/40 text-[#2962ff]/60 cursor-not-allowed"
              : "bg-[#2962ff] text-white hover:bg-[#2962ff]/80 active:bg-[#2962ff]/60"
          }`}
        >
          {launching || isRunning ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              运行中
            </>
          ) : (
            <>
              <Zap size={15} />
              一键启动
            </>
          )}
        </button>
      </aside>

      {/* ───────── 右侧：进度 + 报告 ───────── */}
      <div className="flex-1 flex flex-col gap-4 min-w-0 overflow-y-auto">
        {job === null ? (
          /* 空状态 */
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
            <Brain size={64} className="text-white opacity-20" />
            <p className="text-sm font-medium text-white">
              配置参数后点击「一键启动」
            </p>
            <p className="text-xs text-[#8b949e] max-w-xs leading-relaxed">
              AutoPilot 将自动完成数据拉取、模型训练、信号生成与回测复盘，全程无需干预。
            </p>
          </div>
        ) : (
          <>
            {/* 流程进度卡片 */}
            <div className="bg-[#1e222d] border border-[#2a2e39] rounded-xl p-4">
              {/* 标题行 */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold text-white">流程进度</span>
                <StatusBadge />
              </div>

              {/* 步骤列表 */}
              <div className="flex flex-wrap items-center gap-1">
                {job.steps.map((step, idx) => (
                  <div key={step.name} className="flex items-center gap-1">
                    {/* 分隔符 */}
                    {idx > 0 && (
                      <ChevronRight size={12} className="text-[#434651] shrink-0" />
                    )}

                    <div className="flex items-center gap-1.5">
                      <StepIcon status={step.status} />
                      <div className="flex flex-col">
                        <span className="text-xs text-white leading-tight">
                          {step.label}
                        </span>
                        {step.message && (
                          <span className="text-[10px] text-[#8b949e] leading-tight">
                            {step.message}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 全局错误 */}
              {job.error && (
                <div className="mt-3 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                  {job.error}
                </div>
              )}
            </div>

            {/* 复盘报告卡片 */}
            {job.status === "done" && hasResult && (
              <div className="bg-[#0f1117] rounded-xl flex flex-col gap-4">
                {/* 报告头 */}
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-[#2962ff]/20">
                    <Activity size={16} className="text-[#2962ff]" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">复盘报告</div>
                    <div className="text-xs text-[#8b949e] mt-0.5">
                      {symbol} · {timeframe} · {startDate} ~ {endDate}
                    </div>
                  </div>
                </div>

                <ReviewReport result={job.result} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
