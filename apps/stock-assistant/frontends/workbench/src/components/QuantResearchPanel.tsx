/**
 * QuantResearchPanel — 量化研究中心
 *
 * 标签页：
 *   因子库   — 全量 37 个因子目录（按来源/类别过滤）
 *   模型训练  — 配置并运行 ML 训练，查看特征重要性与 walk-forward 结果
 *   参数优化  — 策略参数网格搜索与最优参数展示
 */

import { useEffect, useRef, useState } from "react";

import {
  fetchCryptoResearchLatestSummary,
  fetchFactorCatalog,
  runQuantResearchOptimize,
  runQuantResearchTrain,
  type CryptoResearchOptimizationSummary,
  type CryptoResearchSummary,
  type FactorInfo,
} from "../api/client";

// ── 常量 ─────────────────────────────────────────────────────────────────────

const SOURCE_LABEL: Record<string, string> = {
  core_crypto: "Core",
  advanced_crypto: "Advanced",
  pandas_ta_crypto: "pandas-ta",
};

const SOURCE_COLOR: Record<string, string> = {
  core_crypto: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  advanced_crypto: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  pandas_ta_crypto: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
};

const CATEGORY_COLOR: Record<string, string> = {
  动量: "text-yellow-400",
  反转: "text-pink-400",
  波动率: "text-orange-400",
  量价: "text-cyan-400",
  形态: "text-indigo-400",
  跨周期: "text-teal-400",
  振荡器: "text-violet-400",
  趋势: "text-blue-400",
};

const REGIME_LABEL: Record<string, { label: string; color: string }> = {
  trend: { label: "趋势行情", color: "text-green-400" },
  high_volatility: { label: "高波动", color: "text-orange-400" },
  range: { label: "震荡区间", color: "text-blue-400" },
};

const SIGNAL_LABEL: Record<number, { label: string; color: string }> = {
  1: { label: "看多", color: "text-green-400" },
  0: { label: "中性", color: "text-[#8b949e]" },
  [-1]: { label: "看空", color: "text-red-400" },
};

type PanelTab = "catalog" | "train" | "optimize";

// ── 小工具函数 ────────────────────────────────────────────────────────────────

const pct = (v: number) => `${(v * 100).toFixed(2)}%`;
const pctAbs = (v: number) => `${(Math.abs(v) * 100).toFixed(1)}%`;

// ── 因子库标签页 ───────────────────────────────────────────────────────────────

function CatalogTab() {
  const [factors, setFactors] = useState<FactorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  useEffect(() => {
    fetchFactorCatalog()
      .then(setFactors)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const sources = ["all", "core_crypto", "advanced_crypto", "pandas_ta_crypto"];
  const categories = [
    "all",
    ...Array.from(new Set(factors.map((f) => f.category))).sort(),
  ];

  const visible = factors.filter((f) => {
    if (sourceFilter !== "all" && f.source !== sourceFilter) return false;
    if (categoryFilter !== "all" && f.category !== categoryFilter) return false;
    return true;
  });

  if (loading)
    return <div className="py-8 text-center text-sm text-[#8b949e]">加载因子目录…</div>;
  if (error)
    return <div className="py-4 text-sm text-red-400">{error}</div>;

  return (
    <div className="space-y-3">
      {/* 汇总统计 */}
      <div className="flex gap-4 text-xs text-[#8b949e]">
        <span>共 <strong className="text-white">{factors.length}</strong> 个因子</span>
        <span className="text-blue-400">Core: {factors.filter((f) => f.source === "core_crypto").length}</span>
        <span className="text-purple-400">Advanced: {factors.filter((f) => f.source === "advanced_crypto").length}</span>
        <span className="text-emerald-400">pandas-ta: {factors.filter((f) => f.source === "pandas_ta_crypto").length}</span>
      </div>

      {/* 来源过滤 */}
      <div className="flex flex-wrap gap-1.5">
        {sources.map((s) => (
          <button
            key={s}
            onClick={() => setSourceFilter(s)}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
              sourceFilter === s
                ? "bg-[#2962ff]/20 border-[#2962ff] text-[#2962ff]"
                : "border-[#2a2e39] text-[#8b949e] hover:text-white"
            }`}
          >
            {s === "all" ? "全部来源" : SOURCE_LABEL[s]}
          </button>
        ))}
        <span className="mx-1 text-[#2a2e39]">|</span>
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setCategoryFilter(c)}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
              categoryFilter === c
                ? "bg-[#2962ff]/20 border-[#2962ff] text-[#2962ff]"
                : "border-[#2a2e39] text-[#8b949e] hover:text-white"
            }`}
          >
            {c === "all" ? "全部类别" : c}
          </button>
        ))}
      </div>

      {/* 因子表格 */}
      <div className="overflow-x-auto rounded-xl border border-[#2a2e39]">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#2a2e39] bg-[#161b22]">
              <th className="px-3 py-2 text-left text-[#8b949e] font-medium w-36">因子名</th>
              <th className="px-3 py-2 text-left text-[#8b949e] font-medium w-16">来源</th>
              <th className="px-3 py-2 text-left text-[#8b949e] font-medium w-16">类别</th>
              <th className="px-3 py-2 text-left text-[#8b949e] font-medium w-12">窗口</th>
              <th className="px-3 py-2 text-left text-[#8b949e] font-medium w-20">范围</th>
              <th className="px-3 py-2 text-left text-[#8b949e] font-medium">说明</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((f, i) => (
              <tr
                key={f.name}
                className={`border-b border-[#2a2e39]/50 ${i % 2 === 0 ? "bg-[#0d1117]" : "bg-[#161b22]/40"} hover:bg-[#1c2128]`}
              >
                <td className="px-3 py-2 font-mono text-white">{f.name}</td>
                <td className="px-3 py-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] border ${SOURCE_COLOR[f.source] ?? ""}`}>
                    {SOURCE_LABEL[f.source] ?? f.source}
                  </span>
                </td>
                <td className={`px-3 py-2 font-medium ${CATEGORY_COLOR[f.category] ?? "text-[#8b949e]"}`}>
                  {f.category}
                </td>
                <td className="px-3 py-2 text-[#8b949e] font-mono">
                  {f.window ?? "—"}
                </td>
                <td className="px-3 py-2 text-[#8b949e] font-mono text-[10px]">
                  {f.range_hint ?? "—"}
                </td>
                <td className="px-3 py-2 text-[#8b949e] leading-relaxed">{f.description}</td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-[#8b949e]">
                  无匹配因子
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── 模型训练标签页 ─────────────────────────────────────────────────────────────

function TrainTab() {
  const [symbol, setSymbol] = useState("BTC-USDT");
  const [limit, setLimit] = useState(500);
  const [trainSize, setTrainSize] = useState(200);
  const [testSize, setTestSize] = useState(50);
  const [stepSize, setStepSize] = useState(50);
  const [embargoSize, setEmbargoSize] = useState(2);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<CryptoResearchSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  // 尝试加载缓存结果
  useEffect(() => {
    fetchCryptoResearchLatestSummary(symbol)
      .then((r) => { if (mountedRef.current) setResult(r); })
      .catch(() => {});
    return () => { mountedRef.current = false; };
  }, []);

  async function handleTrain() {
    setLoading(true);
    setError(null);
    setStatus("计算因子特征（CoreCrypto + AdvancedCrypto + pandas-ta）…");
    try {
      const r = await runQuantResearchTrain({
        symbol,
        limit,
        validation: { train_size: trainSize, test_size: testSize, step_size: stepSize, embargo_size: embargoSize },
      });
      setResult(r);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
      setStatus("");
    }
  }

  const topFactors = result
    ? Object.entries(result.feature_importance)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 15)
    : [];

  const maxImp = topFactors[0]?.[1] ?? 1;

  const regime = result ? (REGIME_LABEL[result.market_regime] ?? { label: result.market_regime, color: "text-white" }) : null;
  const signal = result ? (SIGNAL_LABEL[result.latest_class_signal] ?? { label: String(result.latest_class_signal), color: "text-white" }) : null;

  return (
    <div className="flex gap-6">
      {/* 左侧配置 */}
      <div className="w-56 flex-shrink-0 space-y-4">
        <div className="space-y-1">
          <label className="text-xs text-[#8b949e]">交易对</label>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="BTC-USDT"
            className="w-full bg-[#1e222d] border border-[#2a2e39] rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-[#2962ff]"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-[#8b949e]">K 线数量 <span className="text-white font-mono">{limit}</span></label>
          <input type="range" min={200} max={2000} step={100} value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="w-full accent-[#2962ff]"
          />
          <div className="flex justify-between text-[10px] text-[#4a5568]"><span>200</span><span>2000</span></div>
        </div>

        <div className="space-y-2 bg-[#161b22] border border-[#2a2e39] rounded-xl p-3">
          <div className="text-xs text-[#8b949e] font-medium">Walk-Forward 配置</div>
          {(
            [
              ["训练窗口", trainSize, setTrainSize, 50, 500],
              ["测试窗口", testSize, setTestSize, 10, 200],
              ["步进大小", stepSize, setStepSize, 10, 200],
              ["隔离带", embargoSize, setEmbargoSize, 0, 20],
            ] as [string, number, (v: number) => void, number, number][]
          ).map(([label, val, setter, min, max]) => (
            <div key={label} className="space-y-0.5">
              <div className="flex justify-between text-[10px] text-[#8b949e]">
                <span>{label}</span><span className="font-mono text-white">{val}</span>
              </div>
              <input type="range" min={min} max={max} step={label === "隔离带" ? 1 : 10} value={val}
                onChange={(e) => setter(Number(e.target.value))}
                className="w-full accent-[#2962ff]"
              />
            </div>
          ))}
        </div>

        {error && (
          <div className="px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">{error}</div>
        )}
        {status && <div className="text-xs text-[#8b949e] animate-pulse">{status}</div>}

        <button
          onClick={() => void handleTrain()}
          disabled={loading}
          className="w-full py-2.5 rounded-lg text-sm font-semibold bg-[#2962ff]/20 hover:bg-[#2962ff]/30 text-[#2962ff] border border-[#2962ff]/40 transition-colors disabled:opacity-50"
        >
          {loading ? "训练中…" : "开始训练"}
        </button>

        {result && (
          <button
            onClick={() => {
              setLoading(true);
              setStatus("加载最新缓存结果…");
              fetchCryptoResearchLatestSummary(symbol)
                .then(setResult)
                .catch((e: unknown) => setError(String(e)))
                .finally(() => { setLoading(false); setStatus(""); });
            }}
            className="w-full py-1.5 rounded-lg text-xs text-[#8b949e] hover:text-white border border-[#2a2e39] transition-colors"
          >
            读取缓存结果
          </button>
        )}
      </div>

      {/* 右侧结果 */}
      <div className="flex-1 min-w-0 space-y-4">
        {!result ? (
          <div className="flex items-center justify-center h-full py-20 text-[#8b949e] text-sm">
            {loading ? "训练中，首次运行需 30~120 秒…" : "配置左侧参数后点击「开始训练」"}
          </div>
        ) : (
          <>
            {/* 摘要卡片 */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "特征数", value: String(result.feature_count), color: "text-white" },
                { label: "均值准确率", value: `${(result.mean_accuracy * 100).toFixed(1)}%`, color: "text-white" },
                { label: "均值策略收益", value: pct(result.mean_strategy_return), color: result.mean_strategy_return >= 0 ? "text-green-400" : "text-red-400" },
                { label: "验证窗口", value: String(result.validation_windows), color: "text-white" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-3">
                  <div className="text-[10px] text-[#434651] mb-1">{label}</div>
                  <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
                </div>
              ))}
            </div>

            {/* 市场状态 + 信号 */}
            <div className="flex gap-3">
              <div className="flex-1 bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-1">
                <div className="text-[10px] text-[#434651]">市场状态</div>
                <div className={`text-sm font-semibold ${regime?.color ?? "text-white"}`}>{regime?.label}</div>
              </div>
              <div className="flex-1 bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-1">
                <div className="text-[10px] text-[#434651]">最新信号</div>
                <div className={`text-sm font-semibold ${signal?.color ?? "text-white"}`}>{signal?.label}</div>
              </div>
              <div className="flex-1 bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-1">
                <div className="text-[10px] text-[#434651]">反转概率</div>
                <div className={`text-sm font-semibold ${result.reversal_probability >= 0.5 ? "text-orange-400" : "text-[#8b949e]"}`}>
                  {pctAbs(result.reversal_probability)}
                </div>
              </div>
              <div className="flex-1 bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-1">
                <div className="text-[10px] text-[#434651]">样本行数</div>
                <div className="text-sm font-semibold text-white">{result.rows}</div>
              </div>
            </div>

            {/* 信号概率条 */}
            <div className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-2">
              <div className="text-xs text-[#8b949e] font-medium">最新分类概率</div>
              {(
                [
                  { key: "-1", label: "看空", color: "bg-red-500" },
                  { key: "0", label: "中性", color: "bg-[#434651]" },
                  { key: "1", label: "看多", color: "bg-green-500" },
                ] as const
              ).map(({ key, label, color }) => {
                const prob = result.latest_class_probabilities[key] ?? 0;
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className="w-8 text-xs text-[#8b949e]">{label}</span>
                    <div className="flex-1 bg-[#0d1117] rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${color} transition-all`}
                        style={{ width: `${prob * 100}%` }}
                      />
                    </div>
                    <span className="w-10 text-right text-xs font-mono text-white">
                      {(prob * 100).toFixed(1)}%
                    </span>
                  </div>
                );
              })}
            </div>

            {/* 特征重要性 */}
            {topFactors.length > 0 && (
              <div className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-2">
                <div className="text-xs text-[#8b949e] font-medium">特征重要性（Top {topFactors.length}）</div>
                <div className="space-y-1.5">
                  {topFactors.map(([name, imp]) => (
                    <div key={name} className="flex items-center gap-2">
                      <span className="w-36 text-[10px] font-mono text-[#8b949e] truncate">{name}</span>
                      <div className="flex-1 bg-[#0d1117] rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full bg-[#2962ff] transition-all"
                          style={{ width: `${(imp / maxImp) * 100}%` }}
                        />
                      </div>
                      <span className="w-8 text-right text-[10px] font-mono text-white">
                        {(imp * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Walk-Forward 窗口明细 */}
            <div className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-2">
              <div className="text-xs text-[#8b949e] font-medium">Walk-Forward 窗口明细</div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[#434651] border-b border-[#2a2e39]">
                      <th className="pb-1 text-left pr-3">窗口</th>
                      <th className="pb-1 text-right pr-3">训练区间</th>
                      <th className="pb-1 text-right pr-3">测试区间</th>
                      <th className="pb-1 text-right pr-3">准确率</th>
                      <th className="pb-1 text-right">策略收益</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.window_metrics.map((w, i) => (
                      <tr key={i} className="border-b border-[#2a2e39]/30">
                        <td className="py-1 pr-3 text-[#8b949e]">#{i + 1}</td>
                        <td className="py-1 pr-3 font-mono text-right text-[#8b949e]">
                          {w.train_start}~{w.train_end}
                        </td>
                        <td className="py-1 pr-3 font-mono text-right text-[#8b949e]">
                          {w.test_start}~{w.test_end}
                        </td>
                        <td className="py-1 pr-3 font-mono text-right text-white">
                          {(w.accuracy * 100).toFixed(1)}%
                        </td>
                        <td className={`py-1 font-mono text-right ${w.strategy_return >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {pct(w.strategy_return)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 推荐信息 */}
            <div className="flex gap-2 text-xs text-[#8b949e]">
              <span>推荐策略：</span>
              {result.recommended_strategy_ids.map((s) => (
                <span key={s} className="px-2 py-0.5 bg-[#1e222d] border border-[#2a2e39] rounded font-mono text-white">{s}</span>
              ))}
              <span className="ml-2">推荐周期：</span>
              {result.recommended_timeframes.map((t) => (
                <span key={t} className="px-2 py-0.5 bg-[#1e222d] border border-[#2a2e39] rounded font-mono text-white">{t}</span>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── 参数优化标签页 ─────────────────────────────────────────────────────────────

const DEFAULT_PARAM_GRID = `fast_period: 5, 8, 10
slow_period: 20, 30, 40
vwap_window: 10, 20
trailing_stop_pct: 0.02, 0.03
max_hold_bars: 24, 48`;

function parseParamGrid(text: string): Record<string, number[]> | null {
  const grid: Record<string, number[]> = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const colonIdx = trimmed.indexOf(":");
    if (colonIdx < 0) return null;
    const key = trimmed.slice(0, colonIdx).trim();
    const vals = trimmed
      .slice(colonIdx + 1)
      .split(",")
      .map((v) => parseFloat(v.trim()))
      .filter((v) => !isNaN(v));
    if (!key || vals.length === 0) return null;
    grid[key] = vals;
  }
  return Object.keys(grid).length > 0 ? grid : null;
}

function OptimizeTab() {
  const [symbol, setSymbol] = useState("BTC-USDT");
  const [limit, setLimit] = useState(300);
  const [gridText, setGridText] = useState(DEFAULT_PARAM_GRID);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CryptoResearchOptimizationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const grid = parseParamGrid(gridText);
  const totalCombinations = grid
    ? Object.values(grid).reduce((acc, v) => acc * v.length, 1)
    : 0;

  async function handleOptimize() {
    if (!grid) { setParseError("参数网格格式有误，请检查"); return; }
    setLoading(true);
    setError(null);
    setParseError(null);
    try {
      const r = await runQuantResearchOptimize({ symbol, limit, param_grid: grid });
      setResult(r);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-6">
      {/* 配置列 */}
      <div className="w-64 flex-shrink-0 space-y-4">
        <div className="space-y-1">
          <label className="text-xs text-[#8b949e]">交易对</label>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full bg-[#1e222d] border border-[#2a2e39] rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-[#2962ff]"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs text-[#8b949e]">K 线数量 <span className="font-mono text-white">{limit}</span></label>
          <input type="range" min={100} max={1000} step={50} value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="w-full accent-[#2962ff]"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between">
            <label className="text-xs text-[#8b949e]">参数网格</label>
            <span className="text-[10px] text-[#8b949e]">组合数: <strong className="text-white">{totalCombinations}</strong></span>
          </div>
          <div className="text-[10px] text-[#434651] mb-1">每行格式: <code className="text-[#8b949e]">参数名: 值1, 值2, ...</code></div>
          <textarea
            value={gridText}
            onChange={(e) => { setGridText(e.target.value); setParseError(null); }}
            rows={8}
            className="w-full bg-[#1e222d] border border-[#2a2e39] rounded-lg px-3 py-2 text-white text-xs font-mono focus:outline-none focus:border-[#2962ff] resize-none"
          />
          {parseError && <div className="text-xs text-red-400">{parseError}</div>}
        </div>

        {error && (
          <div className="px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">{error}</div>
        )}

        <button
          onClick={() => void handleOptimize()}
          disabled={loading || !grid}
          className="w-full py-2.5 rounded-lg text-sm font-semibold bg-[#2962ff]/20 hover:bg-[#2962ff]/30 text-[#2962ff] border border-[#2962ff]/40 transition-colors disabled:opacity-50"
        >
          {loading ? `搜索中 (${totalCombinations} 组合)…` : "运行参数优化"}
        </button>

        <div className="text-[10px] text-[#434651] leading-relaxed">
          当前策略：VWAP_EMA_Trend<br />
          方法：网格搜索 + Sharpe 排序<br />
          优化指标：总收益率
        </div>
      </div>

      {/* 结果列 */}
      <div className="flex-1 min-w-0">
        {!result ? (
          <div className="flex items-center justify-center h-full py-20 text-[#8b949e] text-sm">
            {loading ? `网格搜索中（${totalCombinations} 个参数组合）…` : "配置参数网格后点击「运行参数优化」"}
          </div>
        ) : (
          <div className="space-y-4">
            {/* 最优参数卡片 */}
            <div className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-4 space-y-3">
              <div className="text-xs text-[#8b949e] font-medium">最优参数</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(result.best_params).map(([k, v]) => (
                  <div key={k} className="px-3 py-1.5 bg-[#0d1117] border border-[#2962ff]/30 rounded-lg">
                    <span className="text-[10px] text-[#8b949e]">{k}</span>
                    <span className="ml-2 text-sm font-mono font-bold text-[#2962ff]">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 汇总指标 */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "均值策略收益", value: pct(result.mean_strategy_return), color: result.mean_strategy_return >= 0 ? "text-green-400" : "text-red-400" },
                { label: "最大回撤", value: pct(Math.abs(result.max_drawdown)), color: "text-red-400" },
                { label: "优化窗口数", value: String(result.window_count), color: "text-white" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-3">
                  <div className="text-[10px] text-[#434651] mb-1">{label}</div>
                  <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
                </div>
              ))}
            </div>

            {/* 窗口明细 */}
            <div className="bg-[#161b22] border border-[#2a2e39] rounded-xl p-3 space-y-2">
              <div className="text-xs text-[#8b949e] font-medium">窗口策略收益明细</div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[#434651] border-b border-[#2a2e39]">
                      <th className="pb-1 text-left pr-3">窗口</th>
                      <th className="pb-1 text-right pr-3">测试区间</th>
                      <th className="pb-1 text-right">策略收益</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.window_metrics.map((w, i) => (
                      <tr key={i} className="border-b border-[#2a2e39]/30">
                        <td className="py-1 pr-3 text-[#8b949e]">#{i + 1}</td>
                        <td className="py-1 pr-3 font-mono text-right text-[#8b949e]">
                          {w.test_start}~{w.test_end}
                        </td>
                        <td className={`py-1 font-mono text-right ${w.strategy_return >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {pct(w.strategy_return)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── 主面板 ────────────────────────────────────────────────────────────────────

const TABS: { key: PanelTab; label: string }[] = [
  { key: "catalog", label: "因子库" },
  { key: "train",   label: "模型训练" },
  { key: "optimize", label: "参数优化" },
];

export default function QuantResearchPanel() {
  const [activeTab, setActiveTab] = useState<PanelTab>("catalog");

  return (
    <section className="rounded-xl border border-[#30363d] bg-[#0d1117] p-5 space-y-4">
      {/* 标题 */}
      <div>
        <h2 className="text-lg font-semibold text-white">量化研究中心</h2>
        <p className="text-sm text-[#8b949e]">
          37 个因子 · CoreCrypto / AdvancedCrypto / pandas-ta · Walk-Forward 训练 · 参数优化
        </p>
      </div>

      {/* Tab 导航 */}
      <div className="flex gap-1 border-b border-[#2a2e39]">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === key
                ? "border-[#2962ff] text-[#2962ff]"
                : "border-transparent text-[#8b949e] hover:text-white"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab 内容 */}
      <div>
        {activeTab === "catalog"  && <CatalogTab />}
        {activeTab === "train"    && <TrainTab />}
        {activeTab === "optimize" && <OptimizeTab />}
      </div>
    </section>
  );
}
