/**
 * 多策略组合管理面板.
 * UI 设计来自 sample/quantpilot-portfolio-manager，API 逻辑保留自原项目.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  TrendingUp,
  Activity,
  PieChart,
  LayoutGrid,
  Info,
  RefreshCw,
  Search,
  Filter,
  Wallet,
  BarChart2,
  ShieldCheck,
  Plus,
  X,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import MetricCard from "./ui/MetricCard";
import { cn } from "../lib/utils";

// ── 数据类型（与后端 API 对应）────────────────────────────────────────────────

interface StrategyInfo {
  name: string;
  symbol: string;
  allocation: number;
  portfolio_value: number;
  pnl: number;
  pnl_pct: number;
  bars_processed: number;
  trades_count: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

interface PortfolioSummary {
  total_cash: number;
  total_allocated: number;
  total_portfolio_value: number;
  strategies: StrategyInfo[];
  daily_pnl: number;
  daily_pnl_pct: number;
}

interface EquityPoint {
  timestamp: string;
  value: number;
  date: string;
}

// ── 可用模板策略（用于"添加策略"弹窗）────────────────────────────────────────

interface AvailableStrategy {
  id: string;
  name: string;
  description: string;
  default_params: Record<string, unknown>;
}

// ── 添加策略弹窗 ─────────────────────────────────────────────────────────────

interface AddStrategyModalProps {
  onClose: () => void;
  onAdded: () => void;
}

function AddStrategyModal({ onClose, onAdded }: AddStrategyModalProps) {
  const [availableStrategies, setAvailableStrategies] = useState<AvailableStrategy[]>([]);
  const [strategyClass, setStrategyClass] = useState("");
  const [name, setName] = useState("");
  const [symbol, setSymbol] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1d");
  const [allocation, setAllocation] = useState(1_000_000);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch("/api/portfolio/available-strategies");
        if (res.ok) {
          const data = (await res.json()) as { strategies: AvailableStrategy[] };
          setAvailableStrategies(data.strategies);
          if (data.strategies.length > 0) {
            setStrategyClass(data.strategies[0].id);
            setName(data.strategies[0].name);
          }
        }
      } catch { /* 静默 */ }
    })();
  }, []);

  const handleStrategyChange = (id: string) => {
    setStrategyClass(id);
    const s = availableStrategies.find((s) => s.id === id);
    if (s) setName(s.name);
  };

  const handleSubmit = async () => {
    if (!strategyClass || !name.trim() || !symbol.trim()) {
      setError("请填写所有必填字段");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch("/api/portfolio/strategies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          strategy_class: strategyClass,
          symbol: symbol.trim().toUpperCase(),
          timeframe,
          allocation,
          params: {},
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }
      onAdded();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "添加失败");
    } finally {
      setSubmitting(false);
    }
  };

  const INPUT_CLS =
    "w-full h-9 bg-[#1C1E22] border border-[#2A2D35] rounded-lg px-3 text-sm text-white outline-none focus:border-[#00C087]/50 transition-colors placeholder-[#4A4D55]";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-[#151619] border border-[#2A2D35] rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#2A2D35]">
          <h2 className="text-white font-semibold">添加策略到组合</h2>
          <button onClick={onClose} className="text-[#8E9299] hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* 表单 */}
        <div className="px-6 py-5 space-y-4">

          {/* 策略模板选择 */}
          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-[#8E9299] tracking-wider block">策略模板</label>
            <select
              value={strategyClass}
              onChange={(e) => handleStrategyChange(e.target.value)}
              className={cn(INPUT_CLS, "appearance-none cursor-pointer")}
            >
              {availableStrategies.length === 0 ? (
                <option value="">加载中…</option>
              ) : (
                availableStrategies.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))
              )}
            </select>
            {availableStrategies.find((s) => s.id === strategyClass)?.description && (
              <p className="text-[10px] text-[#8E9299]">
                {availableStrategies.find((s) => s.id === strategyClass)?.description}
              </p>
            )}
          </div>

          {/* 策略名称 */}
          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-[#8E9299] tracking-wider block">槽位名称</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={INPUT_CLS}
              placeholder="如: 我的均线策略"
            />
          </div>

          {/* 标的 + 时间周期 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase font-bold text-[#8E9299] tracking-wider block">标的代码</label>
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className={INPUT_CLS}
                placeholder="AAPL"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase font-bold text-[#8E9299] tracking-wider block">K 线周期</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className={cn(INPUT_CLS, "appearance-none cursor-pointer")}
              >
                {["1m","5m","15m","1h","4h","1d","1w"].map((tf) => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 资金分配 */}
          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-[#8E9299] tracking-wider block">
              分配资金 ($)
            </label>
            <input
              type="number"
              value={allocation}
              onChange={(e) => setAllocation(Number(e.target.value))}
              className={INPUT_CLS}
              step={100000}
              min={10000}
            />
          </div>

          {error && (
            <p className="text-xs text-[#FF4D4D] bg-[#FF4D4D]/10 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-[#2A2D35]">
          <button
            onClick={onClose}
            className="h-9 px-4 text-sm text-[#8E9299] hover:text-white border border-[#2A2D35] rounded-lg hover:bg-[#1C1E22] transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => void handleSubmit()}
            disabled={submitting}
            className="h-9 px-4 text-sm font-semibold bg-[#00C087] hover:bg-[#00C087]/90 text-black rounded-lg disabled:opacity-50 transition-colors flex items-center gap-1.5"
          >
            {submitting ? <RefreshCw size={13} className="animate-spin" /> : <Plus size={13} />}
            {submitting ? "添加中…" : "添加策略"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── 相关性热力图（动态行列数，仿 studio 设计）───────────────────────────────

function getCellClass(val: number) {
  if (val === 1) return "bg-[#00C087]/20 text-[#00C087] border-[#00C087]/30";
  const abs = Math.abs(val);
  if (val > 0) {
    if (abs > 0.7) return "bg-[#FF4D4D]/15 text-[#FF4D4D] border-[#FF4D4D]/20";
    if (abs > 0.3) return "bg-[#FF4D4D]/8 text-[#FF4D4D]/80 border-[#2A2D35]";
    return "bg-[#1C1E22] text-[#8E9299] border-[#2A2D35]";
  } else {
    if (abs > 0.7) return "bg-[#00C087]/15 text-[#00C087] border-[#00C087]/20";
    if (abs > 0.3) return "bg-[#00C087]/8 text-[#00C087]/80 border-[#2A2D35]";
    return "bg-[#1C1E22] text-[#8E9299] border-[#2A2D35]";
  }
}

interface CorrelationHeatmapProps {
  names: string[];
  matrix: number[][];
  onRefresh: () => void;
}

function CorrelationHeatmap({ names, matrix, onRefresh }: CorrelationHeatmapProps) {
  const n = names.length;
  const short = (name: string) => name.split(/[\s_-]/)[0].slice(0, 6).toUpperCase();

  return (
    <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <LayoutGrid size={18} className="text-[#00C087]" />
          <h3 className="text-white font-semibold">相关性矩阵</h3>
          <div className="group/tooltip relative">
            <Info size={14} className="text-[#8E9299] cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-52 p-2 bg-[#1C1E22] border border-[#2A2D35] rounded text-[10px] text-[#8E9299] opacity-0 group-hover/tooltip:opacity-100 pointer-events-none transition-opacity z-10">
              衡量策略间盈亏的相关程度。1 为完全同步，0 为不相关，-1 为完全对冲。
            </div>
          </div>
        </div>
        <button
          onClick={onRefresh}
          className="text-[#8E9299] hover:text-white transition-colors"
          title="刷新"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {n < 2 ? (
        <p className="text-[#8E9299] text-xs text-center py-6">
          需至少 2 个策略才能显示相关性矩阵
        </p>
      ) : (
        <div className="overflow-x-auto">
          {/* 列表头 */}
          <div
            className="grid gap-2 mb-2"
            style={{ gridTemplateColumns: `56px repeat(${n}, 1fr)` }}
          >
            <div />
            {names.map((name) => (
              <div
                key={name}
                className="text-[9px] font-bold text-[#8E9299] font-mono uppercase text-center truncate"
                title={name}
              >
                {short(name)}
              </div>
            ))}
          </div>

          {/* 数据行 */}
          {matrix.map((row, i) => (
            <div
              key={names[i]}
              className="grid gap-2 mb-2 items-center"
              style={{ gridTemplateColumns: `56px repeat(${n}, 1fr)` }}
            >
              <div
                className="text-[9px] font-bold text-[#8E9299] font-mono uppercase truncate"
                title={names[i]}
              >
                {short(names[i])}
              </div>
              {row.map((val, j) => (
                <div
                  key={j}
                  className={cn(
                    "aspect-square flex items-center justify-center rounded text-[11px] font-mono border cursor-default hover:scale-105 transition-transform",
                    getCellClass(val),
                  )}
                >
                  {val.toFixed(2)}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <div className="mt-5 flex items-center gap-5">
        <div className="flex items-center gap-2 text-[10px] text-[#8E9299]">
          <div className="w-2 h-2 rounded-full bg-[#FF4D4D]" />
          高相关
        </div>
        <div className="flex items-center gap-2 text-[10px] text-[#8E9299]">
          <div className="w-2 h-2 rounded-full bg-[#00C087]" />
          低相关/对冲
        </div>
        <div className="flex items-center gap-2 text-[10px] text-[#8E9299]">
          <div className="w-2 h-2 rounded-full bg-[#00C087] opacity-60" />
          对角线 = 1.00
        </div>
      </div>
    </div>
  );
}

// ── 状态小点 ─────────────────────────────────────────────────────────────────

function StatusDot({ status }: { status: "active" | "paused" | "error" }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "w-1.5 h-1.5 rounded-full",
          status === "active" ? "bg-[#00C087] animate-pulse" :
          status === "paused" ? "bg-[#FFB800]" : "bg-[#FF4D4D]",
        )}
      />
      <span className="text-xs text-[#8E9299] capitalize">{status}</span>
    </div>
  );
}

// ── 主组件 ────────────────────────────────────────────────────────────────────

const PERIOD_OPTIONS = ["1D", "1W", "1M", "ALL"] as const;

export default function PortfolioPanel() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [correlation, setCorrelation] = useState<Record<string, Record<string, number>>>({});
  const [equityData, setEquityData] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [activePeriod, setActivePeriod] = useState<(typeof PERIOD_OPTIONS)[number]>("1M");
  const [showAddModal, setShowAddModal] = useState(false);
  const [showFilter, setShowFilter] = useState(false);
  const [filterPnl, setFilterPnl] = useState<"all" | "positive" | "negative">("all");

  const loadEquity = useCallback(async (period: (typeof PERIOD_OPTIONS)[number]) => {
    try {
      const res = await fetch(`/api/portfolio/equity?period=${period}`);
      if (res.ok) {
        const d = (await res.json()) as { points: EquityPoint[] };
        setEquityData(d.points);
      }
    } catch (_) { /* 静默 */ }
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, corrRes] = await Promise.all([
        fetch("/api/portfolio/summary"),
        fetch("/api/portfolio/correlation"),
      ]);
      if (sumRes.ok) setSummary((await sumRes.json()) as PortfolioSummary);
      if (corrRes.ok) {
        const d = (await corrRes.json()) as { correlation: Record<string, Record<string, number>> };
        setCorrelation(d.correlation);
      }
    } catch (_) {
      // 静默处理网络错误
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void loadEquity(activePeriod);
  }, [loadData, loadEquity]); // eslint-disable-line react-hooks/exhaustive-deps

  const removeStrategy = async (name: string) => {
    await fetch(`/api/portfolio/strategies/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
    void loadData();
  };

  // ── 派生数据
  const strategies = summary?.strategies ?? [];

  const totalPnl = strategies.reduce((s, x) => s + x.pnl, 0);
  const totalPnlPct =
    summary && summary.total_portfolio_value > 0
      ? (totalPnl / (summary.total_portfolio_value - totalPnl + 1)) * 100
      : 0;

  const dailyPnl = summary?.daily_pnl ?? 0;
  const dailyPnlPct = summary?.daily_pnl_pct ?? 0;

  // 分散化评分：根据相关性均值粗略估算
  const diversificationScore = useMemo(() => {
    const names = Object.keys(correlation);
    if (names.length < 2) return null;
    let sum = 0;
    let count = 0;
    for (const row of names) {
      for (const col of names) {
        if (row !== col) {
          sum += Math.abs(correlation[row]?.[col] ?? 0);
          count++;
        }
      }
    }
    const avgCorr = count > 0 ? sum / count : 0;
    return Math.round((1 - avgCorr) * 100);
  }, [correlation]);

  const filteredStrategies = useMemo(
    () =>
      strategies.filter((s) => {
        const matchSearch =
          s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          s.symbol.toLowerCase().includes(searchTerm.toLowerCase());
        const matchPnl =
          filterPnl === "all" ||
          (filterPnl === "positive" && s.pnl >= 0) ||
          (filterPnl === "negative" && s.pnl < 0);
        return matchSearch && matchPnl;
      }),
    [strategies, searchTerm, filterPnl],
  );

  // 相关性矩阵转换
  const corrNames = useMemo(() => Object.keys(correlation), [correlation]);
  const corrMatrix = useMemo(
    () => corrNames.map((row) => corrNames.map((col) => correlation[row]?.[col] ?? 0)),
    [corrNames, correlation],
  );

  return (
    <>
      {showAddModal && (
        <AddStrategyModal
          onClose={() => setShowAddModal(false)}
          onAdded={() => void loadData()}
        />
      )}
    <div className="text-[#E1E4E8] font-sans selection:bg-white/10">
      <div className="space-y-6">

        {/* ── 页头 ──────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[#8E9299] mb-1">
              <PieChart size={16} />
              <span className="text-xs font-mono uppercase tracking-[0.2em]">
                Portfolio Management
              </span>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">组合概览</h1>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8E9299]"
                size={14}
              />
              <input
                type="text"
                placeholder="搜索策略 / 标的..."
                className="bg-[#151619] border border-[#2A2D35] rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-[#4A4D55] focus:outline-none focus:border-[#4A4D55] transition-colors w-56"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="relative">
              <button
                onClick={() => setShowFilter((v) => !v)}
                className={cn(
                  "bg-[#151619] border rounded-lg p-2 transition-colors",
                  showFilter
                    ? "border-[#00C087]/50 text-[#00C087]"
                    : "border-[#2A2D35] text-[#8E9299] hover:text-white",
                )}
                title="筛选"
              >
                <Filter size={18} />
              </button>
              {showFilter && (
                <div className="absolute right-0 top-full mt-2 w-40 bg-[#151619] border border-[#2A2D35] rounded-xl shadow-xl z-20 overflow-hidden">
                  <div className="px-3 py-2 text-[10px] font-bold uppercase text-[#8E9299] tracking-wider border-b border-[#2A2D35]">
                    按盈亏筛选
                  </div>
                  {([["all", "全部"], ["positive", "仅盈利"], ["negative", "仅亏损"]] as const).map(([val, label]) => (
                    <button
                      key={val}
                      onClick={() => { setFilterPnl(val); setShowFilter(false); }}
                      className={cn(
                        "w-full text-left px-3 py-2 text-xs transition-colors",
                        filterPnl === val ? "text-[#00C087] bg-[#00C087]/10" : "text-[#8E9299] hover:text-white hover:bg-[#1C1E22]",
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => void loadData()}
              disabled={loading}
              className="bg-[#151619] border border-[#2A2D35] rounded-lg px-3 py-2 text-[#8E9299] hover:text-white transition-colors disabled:opacity-50 flex items-center gap-2 text-sm"
              title="刷新数据"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              刷新
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-white text-black font-semibold text-sm px-4 py-2 rounded-lg hover:bg-[#E1E4E8] transition-colors flex items-center gap-1.5"
            >
              <Plus size={15} />
              添加策略
            </button>
          </div>
        </div>

        {/* ── 指标卡片 (6宫格) ──────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <MetricCard
            title="组合总价值"
            value={summary ? `$${summary.total_portfolio_value.toLocaleString()}` : "—"}
            subValue="账户净值"
            icon={Activity}
          />
          <MetricCard
            title="累计盈亏"
            value={
              strategies.length
                ? `${totalPnl >= 0 ? "+" : ""}$${Math.abs(totalPnl).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                : "—"
            }
            trend={strategies.length ? totalPnlPct : undefined}
            subValue="总回报率"
            icon={TrendingUp}
          />
          <MetricCard
            title="当日盈亏"
            value={`${dailyPnl >= 0 ? "+" : ""}$${Math.abs(dailyPnl).toLocaleString()}`}
            trend={dailyPnlPct}
            subValue="今日变动"
            icon={BarChart2}
          />
          <MetricCard
            title="未分配资金"
            value={summary ? `$${summary.total_cash.toLocaleString()}` : "—"}
            subValue="可用现金"
            icon={Wallet}
          />
          <MetricCard
            title="活跃策略"
            value={strategies.length ? String(strategies.length) : "0"}
            subValue="运行中"
            icon={LayoutGrid}
          />
          <MetricCard
            title="分散化评分"
            value={diversificationScore != null ? `${diversificationScore}/100` : "—"}
            subValue="风险分散程度"
            icon={ShieldCheck}
          />
        </div>

        {/* ── 主内容 3列布局 ────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* 左 2/3：权益曲线 + 策略列表 */}
          <div className="lg:col-span-2 space-y-6">

            {/* 权益曲线 */}
            <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <TrendingUp size={18} className="text-[#00C087]" />
                  净值曲线
                </h3>
                <div className="flex bg-[#1C1E22] rounded-lg p-1">
                  {PERIOD_OPTIONS.map((t) => (
                    <button
                      key={t}
                      onClick={() => { setActivePeriod(t); void loadEquity(t); }}
                      className={cn(
                        "px-3 py-1 text-[10px] font-bold rounded-md transition-all",
                        activePeriod === t
                          ? "bg-[#2A2D35] text-white"
                          : "text-[#8E9299] hover:text-white",
                      )}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-[280px] w-full">
                {equityData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-[#4A4D55] text-sm">
                    暂无历史数据 — 刷新组合后自动记录
                  </div>
                ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={equityData}>
                    <defs>
                      <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00C087" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#00C087" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1C1E22" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#4A4D55"
                      fontSize={10}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v: string) => String(v).split("-").slice(1).join("/")}
                    />
                    <YAxis
                      stroke="#4A4D55"
                      fontSize={10}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v: number) => `$${(v / 1_000_000).toFixed(1)}M`}
                      domain={["dataMin - 50000", "dataMax + 50000"]}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1C1E22",
                        border: "1px solid #2A2D35",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      itemStyle={{ color: "#00C087" }}
                      formatter={(v) =>
                        v != null
                          ? [`$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, "净值"]
                          : ["—", "净值"]
                      }
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#00C087"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorPortfolio)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* 策略列表 */}
            <div className="bg-[#151619] border border-[#2A2D35] rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-[#2A2D35] flex items-center justify-between">
                <h3 className="text-white font-semibold">
                  策略列表
                  <span className="ml-2 text-xs text-[#8E9299] font-mono">
                    ({filteredStrategies.length})
                  </span>
                </h3>
                <span className="text-[10px] text-[#4A4D55] font-mono">
                  总分配 ${summary?.total_allocated.toLocaleString() ?? "—"}
                </span>
              </div>

              {filteredStrategies.length === 0 ? (
                <div className="px-6 py-12 text-center text-[#8E9299] text-sm">
                  {strategies.length === 0
                    ? "暂无策略 — 通过 API 添加策略到组合"
                    : `无匹配结果 "${searchTerm}"`}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-[#1C1E22]/50 border-y border-[#2A2D35]">
                        {["策略名称", "状态", "分配资金", "盈亏", "回撤", "夏普", ""].map((h) => (
                          <th
                            key={h}
                            className="px-5 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299] whitespace-nowrap"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#2A2D35]">
                      {filteredStrategies.map((s) => (
                        <tr
                          key={s.name}
                          className="hover:bg-[#1C1E22]/30 transition-colors group cursor-default"
                        >
                          {/* 策略名 + 标的 */}
                          <td className="px-5 py-4">
                            <div className="flex flex-col">
                              <span className="text-sm font-medium text-white group-hover:text-[#00C087] transition-colors">
                                {s.name}
                              </span>
                              <span className="text-[10px] text-[#8E9299] font-mono">
                                {s.symbol} · {s.bars_processed}K · {s.trades_count}T
                              </span>
                            </div>
                          </td>

                          {/* 状态 */}
                          <td className="px-5 py-4">
                            <StatusDot status="active" />
                          </td>

                          {/* 分配资金 */}
                          <td className="px-5 py-4 text-sm font-mono text-[#E1E4E8]">
                            ${(s.allocation / 1000).toLocaleString()}K
                          </td>

                          {/* 盈亏 */}
                          <td className="px-5 py-4">
                            <div className="flex flex-col">
                              <span
                                className={cn(
                                  "text-sm font-mono",
                                  s.pnl >= 0 ? "text-[#00C087]" : "text-[#FF4D4D]",
                                )}
                              >
                                {s.pnl >= 0 ? "+" : ""}
                                {s.pnl.toFixed(2)}
                              </span>
                              <span
                                className={cn(
                                  "text-[10px] font-mono",
                                  s.pnl_pct >= 0
                                    ? "text-[#00C087]/70"
                                    : "text-[#FF4D4D]/70",
                                )}
                              >
                                {s.pnl_pct >= 0 ? "+" : ""}
                                {s.pnl_pct.toFixed(2)}%
                              </span>
                            </div>
                          </td>

                          {/* 最大回撤 */}
                          <td className="px-5 py-4 text-sm font-mono text-[#FF4D4D]">
                            {s.max_drawdown !== 0
                              ? `${s.max_drawdown.toFixed(2)}%`
                              : <span className="text-[#4A4D55]">—</span>}
                          </td>

                          {/* 夏普比率 */}
                          <td className="px-5 py-4 text-sm font-mono text-[#8E9299]">
                            {s.sharpe_ratio !== 0
                              ? <span className={s.sharpe_ratio >= 1 ? "text-[#00C087]" : s.sharpe_ratio >= 0 ? "text-[#FFB800]" : "text-[#FF4D4D]"}>{s.sharpe_ratio.toFixed(2)}</span>
                              : <span className="text-[#4A4D55]">—</span>}
                          </td>

                          {/* 移除 */}
                          <td className="px-5 py-4 text-right">
                            <button
                              onClick={() => void removeStrategy(s.name)}
                              className="text-[#8E9299] hover:text-[#FF4D4D] transition-colors text-xs px-2 py-1 rounded hover:bg-[#FF4D4D]/10"
                            >
                              移除
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* 右 1/3：相关性矩阵 + 风险洞察 */}
          <div className="space-y-6">
            <CorrelationHeatmap
              names={corrNames}
              matrix={corrMatrix}
              onRefresh={loadData}
            />

            {/* 风险洞察 */}
            <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <Info size={18} className="text-[#FFB800]" />
                风险洞察
              </h3>
              <div className="space-y-3">
                {strategies.length === 0 ? (
                  <p className="text-[#8E9299] text-xs">添加策略后自动生成风险分析。</p>
                ) : (
                  <>
                    {totalPnl < 0 && (
                      <div className="p-3 bg-[#1C1E22] rounded-lg border-l-2 border-[#FF4D4D]">
                        <p className="text-xs text-[#E1E4E8] leading-relaxed">
                          <span className="font-bold text-[#FF4D4D]">警报</span>：组合整体盈亏为负 (
                          {totalPnlPct.toFixed(2)}%)，请关注亏损策略并及时调整仓位。
                        </p>
                      </div>
                    )}
                    <div className="p-3 bg-[#1C1E22] rounded-lg border-l-2 border-[#00C087]">
                      <p className="text-xs text-[#E1E4E8] leading-relaxed">
                        <span className="font-bold text-[#00C087]">建议</span>：当前共{" "}
                        {strategies.length} 个策略，总分配{" "}
                        ${summary?.total_allocated.toLocaleString()}。
                        {corrNames.length >= 2
                          ? " 相关性矩阵已就绪，请检查高相关策略对的风险集中情况。"
                          : " 添加更多策略后可查看相关性分析。"}
                      </p>
                    </div>
                    {diversificationScore != null && diversificationScore < 70 && (
                      <div className="p-3 bg-[#1C1E22] rounded-lg border-l-2 border-[#FFB800]">
                        <p className="text-xs text-[#E1E4E8] leading-relaxed">
                          <span className="font-bold text-[#FFB800]">提示</span>：分散化评分{" "}
                          {diversificationScore}/100，策略间相关性偏高，建议引入对冲型策略。
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* 组合分配饼图（占位） */}
            {strategies.length > 0 && (
              <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4 text-sm">资金分配</h3>
                <div className="space-y-2">
                  {strategies.map((s) => {
                    const pct = summary
                      ? (s.allocation / summary.total_portfolio_value) * 100
                      : 0;
                    return (
                      <div key={s.name} className="flex flex-col gap-1">
                        <div className="flex justify-between text-[10px]">
                          <span className="text-[#8E9299] truncate max-w-[70%]">{s.name}</span>
                          <span className="text-white font-mono">{pct.toFixed(1)}%</span>
                        </div>
                        <div className="h-1 bg-[#1C1E22] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-[#00C087] rounded-full transition-all"
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
    </>
  );
}
