/**
 * 策略工坊 — 策略全生命周期管理（代码编辑 → LLM 生成 → 参数优化 → 实盘运行）
 * 合并了原 StrategyPanel + PortfolioPanel 的全部功能，去除独立「组合」导航入口。
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { editor as MonacoEditor } from "monaco-editor";
import {
  Activity,
  BarChart2,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Code2,
  Database,
  FileCode,
  LayoutGrid,
  Layers,
  Play,
  PieChart,
  Plus,
  RefreshCw,
  Save,
  Settings,
  ShieldCheck,
  Terminal,
  Trash2,
  TrendingUp,
  Wallet,
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
import {
  listStrategies,
  listTemplates,
  getStrategy,
  getTemplateCode,
  createStrategy,
  updateStrategy,
  deleteStrategy,
} from "../api/client";
import FeatureGuideButton from "@/components/guides/FeatureGuideButton";
import { useStrategyStore } from "../store/strategyStore";
import { cn } from "../lib/utils";
import StrategyEditor from "./StrategyEditor";
import MLStrategyPanel from "./MLStrategyPanel";
import OptimizationPanel from "./OptimizationPanel";
import StrategyGeneratorPanel from "./StrategyGeneratorPanel";
import MetricCard from "./ui/MetricCard";

// ── 数据类型 ──────────────────────────────────────────────────────────────────

interface StrategySlotInfo {
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
  strategies: StrategySlotInfo[];
  daily_pnl: number;
  daily_pnl_pct: number;
}

interface EquityPoint {
  timestamp: string;
  value: number;
  date: string;
}

interface AvailableStrategy {
  id: string;
  name: string;
  description: string;
  default_params: Record<string, unknown>;
  source?: "template" | "user";
}

// ── 子标签 ────────────────────────────────────────────────────────────────────

type Sub = "code" | "generate" | "live" | "optimize" | "ml";

const SUBS: { key: Sub; label: string }[] = [
  { key: "code",     label: "代码编辑" },
  { key: "generate", label: "LLM 生成" },
  { key: "live",     label: "实盘运行" },
  { key: "optimize", label: "参数优化" },
  { key: "ml",       label: "机器学习" },
];

// ── 侧栏条目 ──────────────────────────────────────────────────────────────────

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  active?: boolean;
  indent?: number;
  hasChildren?: boolean;
  isOpen?: boolean;
  badge?: string;
  onClick?: () => void;
  children?: React.ReactNode;
}

function SidebarItem({
  icon: Icon,
  label,
  active,
  indent = 0,
  hasChildren,
  isOpen,
  badge,
  onClick,
  children,
}: SidebarItemProps) {
  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-3 py-2 text-sm cursor-pointer transition-all hover:bg-[#161b22] group",
          active
            ? "bg-blue-600/10 text-blue-400 font-semibold border-r-2 border-blue-500"
            : "text-[#8b949e] hover:text-white",
        )}
        style={{ paddingLeft: indent > 0 ? `${indent * 16 + 24}px` : "24px", paddingRight: "16px" }}
        onClick={onClick}
      >
        <Icon
          className={cn(
            "w-4 h-4 shrink-0 transition-transform group-hover:scale-110",
            active ? "text-blue-400" : "text-[#8b949e] group-hover:text-white",
          )}
        />
        <span className="truncate flex-1">{label}</span>
        {badge && (
          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 shrink-0">
            {badge}
          </span>
        )}
        {hasChildren && (
          <ChevronRight
            className={cn(
              "w-3.5 h-3.5 text-[#8b949e] transition-transform duration-200",
              isOpen && "rotate-90",
            )}
          />
        )}
      </div>
      {hasChildren && isOpen && children}
    </div>
  );
}

// ── 控制台 ────────────────────────────────────────────────────────────────────

interface LogLine { level: "INFO" | "SUCCESS" | "WARN" | "ERROR"; text: string; }
const LOG_COLOR: Record<string, string> = {
  INFO:    "text-blue-400",
  SUCCESS: "text-green-400",
  WARN:    "text-yellow-400",
  ERROR:   "text-red-400",
};

// ── 部署表单（内联）──────────────────────────────────────────────────────────

interface DeployFormProps {
  defaultStrategyId?: string;
  onAdded: () => void;
  onCancel: () => void;
}

function DeployForm({ defaultStrategyId, onAdded, onCancel }: DeployFormProps) {
  const [available, setAvailable] = useState<AvailableStrategy[]>([]);
  const [strategyClass, setStrategyClass] = useState(defaultStrategyId ?? "");
  const [name, setName] = useState("");
  const [symbol, setSymbol] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1d");
  const [allocation, setAllocation] = useState(1_000_000);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void fetch("/api/portfolio/available-strategies")
      .then((r) => r.json())
      .then((d: { strategies: AvailableStrategy[] }) => {
        setAvailable(d.strategies);
        if (!defaultStrategyId && d.strategies.length > 0) {
          setStrategyClass(d.strategies[0].id);
          setName(d.strategies[0].name);
        }
      })
      .catch(() => {});
  }, [defaultStrategyId]);

  useEffect(() => {
    if (defaultStrategyId) {
      const s = available.find((a) => a.id === defaultStrategyId);
      if (s) setName(s.name);
    }
  }, [available, defaultStrategyId]);

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
      if (!res.ok) throw new Error(await res.text());
      onAdded();
    } catch (e) {
      setError(e instanceof Error ? e.message : "部署失败");
    } finally {
      setSubmitting(false);
    }
  };

  const INPUT = "w-full h-9 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 text-sm text-white outline-none focus:border-blue-500/50 transition-colors placeholder-[#8b949e]/40";

  return (
    <div className="bg-[#161b22]/60 border border-[#30363d] rounded-xl p-5 space-y-4">
      <h3 className="text-white font-semibold text-sm flex items-center gap-2">
        <Play size={14} className="text-emerald-400" /> 部署到实盘组合
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5 col-span-2">
          <label className="text-[10px] uppercase font-bold text-[#8b949e] tracking-wider block">策略模板</label>
          <select
            value={strategyClass}
            onChange={(e) => setStrategyClass(e.target.value)}
            className={cn(INPUT, "appearance-none cursor-pointer")}
          >
            {available.length === 0
              ? <option value="">加载中…</option>
              : available.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.source === "user" ? `[用户] ${s.name}` : `[模板] ${s.name}`}
                </option>
              ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] uppercase font-bold text-[#8b949e] tracking-wider block">槽位名称</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className={INPUT} placeholder="如: 我的均线策略" />
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] uppercase font-bold text-[#8b949e] tracking-wider block">标的代码</label>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} className={INPUT} placeholder="AAPL" />
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] uppercase font-bold text-[#8b949e] tracking-wider block">K 线周期</label>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className={cn(INPUT, "appearance-none cursor-pointer")}>
            {["1m", "5m", "15m", "1h", "4h", "1d", "1w"].map((tf) => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] uppercase font-bold text-[#8b949e] tracking-wider block">分配资金 ($)</label>
          <input
            type="number"
            value={allocation}
            onChange={(e) => setAllocation(Number(e.target.value))}
            className={INPUT}
            step={100000}
            min={10000}
          />
        </div>
      </div>

      {error && <p className="text-xs text-red-400 bg-red-400/10 rounded-lg px-3 py-2">{error}</p>}

      <div className="flex items-center justify-end gap-3">
        <button
          onClick={onCancel}
          className="h-8 px-4 text-sm text-[#8b949e] hover:text-white border border-[#30363d] rounded-lg hover:bg-[#21262d] transition-colors"
        >
          取消
        </button>
        <button
          onClick={() => void handleSubmit()}
          disabled={submitting}
          className="h-8 px-4 text-sm font-bold bg-white text-black rounded-lg hover:bg-[#e1e4e8] disabled:opacity-50 transition-colors flex items-center gap-1.5"
        >
          {submitting ? <RefreshCw size={12} className="animate-spin" /> : <Plus size={12} />}
          {submitting ? "部署中…" : "部署策略"}
        </button>
      </div>
    </div>
  );
}

// ── 实盘运行子面板 ────────────────────────────────────────────────────────────

const PERIOD_OPTIONS = ["1D", "1W", "1M", "ALL"] as const;

function LiveTradingTab({ currentStrategyId }: { currentStrategyId: string | null }) {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [equityData, setEquityData] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [activePeriod, setActivePeriod] = useState<(typeof PERIOD_OPTIONS)[number]>("1M");
  const [showDeployForm, setShowDeployForm] = useState(false);

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
      const res = await fetch("/api/portfolio/summary");
      if (res.ok) setSummary((await res.json()) as PortfolioSummary);
    } catch (_) { /* 静默 */ } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void loadEquity(activePeriod);
  }, [loadData, loadEquity]); // eslint-disable-line react-hooks/exhaustive-deps

  const removeSlot = async (slotName: string) => {
    await fetch(`/api/portfolio/strategies/${encodeURIComponent(slotName)}`, { method: "DELETE" });
    void loadData();
  };

  const slots = summary?.strategies ?? [];
  const totalPnl = slots.reduce((s, x) => s + x.pnl, 0);
  const totalPnlPct =
    summary && summary.total_portfolio_value > 0
      ? (totalPnl / (summary.total_portfolio_value - totalPnl + 1)) * 100
      : 0;
  const dailyPnl = summary?.daily_pnl ?? 0;
  const dailyPnlPct = summary?.daily_pnl_pct ?? 0;

  return (
    <div className="space-y-6">
      {/* 面板标题 */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-[#8b949e] mb-1">
            <PieChart size={14} />
            <span className="text-[10px] font-mono uppercase tracking-[0.2em]">Live Portfolio</span>
          </div>
          <h2 className="text-2xl font-bold text-white">组合实盘运行</h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => void loadData()}
            disabled={loading}
            className="flex items-center gap-2 h-9 px-3 border border-[#30363d] rounded-lg text-[#8b949e] hover:text-white text-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            刷新
          </button>
          <button
            onClick={() => setShowDeployForm(true)}
            className="flex items-center gap-2 h-9 px-4 bg-white text-black font-bold text-sm rounded-lg hover:bg-[#e1e4e8] transition-colors"
          >
            <Plus size={13} /> 部署策略
          </button>
        </div>
      </div>

      {/* 指标卡片 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          title="组合总价值"
          value={summary ? `$${summary.total_portfolio_value.toLocaleString()}` : "—"}
          subValue="账户净值"
          icon={Activity}
        />
        <MetricCard
          title="累计盈亏"
          value={slots.length
            ? `${totalPnl >= 0 ? "+" : ""}$${Math.abs(totalPnl).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
            : "—"}
          trend={slots.length ? totalPnlPct : undefined}
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
          value={String(slots.length)}
          subValue="运行中"
          icon={LayoutGrid}
        />
        <MetricCard
          title="已分配"
          value={summary ? `$${summary.total_allocated.toLocaleString()}` : "—"}
          subValue="已部署资金"
          icon={ShieldCheck}
        />
      </div>

      {/* 部署表单 */}
      {showDeployForm && (
        <DeployForm
          defaultStrategyId={currentStrategyId ?? undefined}
          onAdded={() => { setShowDeployForm(false); void loadData(); }}
          onCancel={() => setShowDeployForm(false)}
        />
      )}

      {/* 净值曲线 */}
      <div className="bg-[#161b22]/40 border border-[#30363d] rounded-xl p-5">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <TrendingUp size={15} className="text-emerald-400" /> 净值曲线
          </h3>
          <div className="flex bg-[#0d1117] rounded-lg p-1">
            {PERIOD_OPTIONS.map((t) => (
              <button
                key={t}
                onClick={() => { setActivePeriod(t); void loadEquity(t); }}
                className={cn(
                  "px-3 py-1 text-[10px] font-bold rounded-md transition-all",
                  activePeriod === t ? "bg-[#21262d] text-white" : "text-[#8b949e] hover:text-white",
                )}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <div className="h-52 w-full">
          {equityData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-[#434651] text-sm">
              暂无历史数据 — 刷新组合后自动记录
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityData}>
                <defs>
                  <linearGradient id="wsEquityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00C087" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00C087" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: "#8b949e", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#8b949e", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, color: "#c9d1d9" }}
                />
                <Area type="monotone" dataKey="value" stroke="#00C087" fill="url(#wsEquityGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* 策略槽位表格 */}
      {slots.length > 0 && (
        <div className="bg-[#161b22]/40 border border-[#30363d] rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-[#30363d]">
            <h3 className="text-white font-semibold text-sm">策略槽位</h3>
            <span className="text-xs text-[#8b949e]">{slots.length} 个运行中</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[#8b949e] border-b border-[#30363d]">
                  {["名称", "标的", "分配 ($)", "净值 ($)", "盈亏", "Sharpe", "最大回撤", "操作"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left font-medium whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {slots.map((s) => (
                  <tr key={s.name} className="border-b border-[#21262d] hover:bg-[#21262d]/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-white">{s.name}</td>
                    <td className="px-4 py-3 font-mono text-[#8b949e]">{s.symbol}</td>
                    <td className="px-4 py-3 font-mono text-[#8b949e]">{s.allocation.toLocaleString()}</td>
                    <td className="px-4 py-3 font-mono text-[#c9d1d9]">{s.portfolio_value.toLocaleString()}</td>
                    <td className={cn("px-4 py-3 font-mono font-bold", s.pnl >= 0 ? "text-emerald-400" : "text-red-400")}>
                      {s.pnl >= 0 ? "+" : ""}{s.pnl.toFixed(0)} ({s.pnl_pct >= 0 ? "+" : ""}{s.pnl_pct.toFixed(2)}%)
                    </td>
                    <td className="px-4 py-3 font-mono text-[#8b949e]">{s.sharpe_ratio.toFixed(2)}</td>
                    <td className="px-4 py-3 font-mono text-red-400">{(s.max_drawdown * 100).toFixed(1)}%</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => void removeSlot(s.name)}
                        className="h-6 px-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded text-[10px] transition-colors"
                      >
                        移除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 空状态 */}
      {slots.length === 0 && !showDeployForm && (
        <div className="flex flex-col items-center justify-center py-16 text-[#434651]">
          <Layers size={40} className="mb-4 opacity-30" />
          <p className="text-sm font-medium">组合中暂无策略</p>
          <p className="text-xs mt-1 mb-4">点击「部署策略」将策略加入实盘运行</p>
          <button
            onClick={() => setShowDeployForm(true)}
            className="flex items-center gap-2 h-9 px-4 bg-white text-black font-bold text-sm rounded-lg hover:bg-[#e1e4e8] transition-colors"
          >
            <Plus size={13} /> 部署策略
          </button>
        </div>
      )}
    </div>
  );
}

// ── 顶部组合状态条 ────────────────────────────────────────────────────────────

function PortfolioBar({ summary }: { summary: PortfolioSummary | null }) {
  if (!summary || summary.strategies.length === 0) return null;
  const pos = summary.daily_pnl >= 0;
  return (
    <div className="flex items-center gap-6 px-8 py-2 border-b border-[#30363d] bg-[#0d1117] shrink-0 text-xs">
      <span className="text-[#8b949e] font-bold uppercase tracking-widest text-[9px]">组合</span>
      <div className="flex items-center gap-1.5">
        <span className="text-[#8b949e]">净值</span>
        <span className="font-mono font-bold text-white">${summary.total_portfolio_value.toLocaleString()}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-[#8b949e]">日盈亏</span>
        <span className={cn("font-mono font-bold", pos ? "text-emerald-400" : "text-red-400")}>
          {pos ? "+" : ""}{summary.daily_pnl.toFixed(0)}
          <span className="ml-1 opacity-70">
            ({summary.daily_pnl_pct >= 0 ? "+" : ""}{summary.daily_pnl_pct.toFixed(2)}%)
          </span>
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-[#8b949e]">活跃策略</span>
        <span className="font-mono font-bold text-emerald-400">{summary.strategies.length}</span>
      </div>
    </div>
  );
}

// ── 主组件 ────────────────────────────────────────────────────────────────────

interface Props {
  onNavigate?: (tab: "market" | "strategy" | "validation" | "options" | "screener" | "crypto") => void;
}

export default function StrategyWorkshop({ onNavigate }: Props) {
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null);
  const {
    strategies, templates, selectedId, editorCode, editorName,
    editorDescription, isDirty,
    setStrategies, setTemplates, selectStrategy,
    setEditorCode, setEditorName, setEditorDescription, markClean,
  } = useStrategyStore();

  const [saving, setSaving] = useState(false);
  const [isTemplate, setIsTemplate] = useState(false);
  const [sub, setSub] = useState<Sub>("code");
  const [showConsole, setShowConsole] = useState(true);
  const [logs, setLogs] = useState<LogLine[]>([
    { level: "INFO",    text: "Initializing QuantPilot engine..." },
    { level: "INFO",    text: "Loading strategy definitions..." },
    { level: "SUCCESS", text: "Engine ready. Waiting for backtest command." },
  ]);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    tradingAlgos: true, mlModels: false, analysis: false,
  });
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);

  const toggleSection = (key: string) => setOpenSections((p) => ({ ...p, [key]: !p[key] }));
  const pushLog = (level: LogLine["level"], text: string) =>
    setLogs((prev) => [...prev.slice(-50), { level, text }]);

  useEffect(() => {
    void (async () => {
      try {
        const [strats, tmplts] = await Promise.all([listStrategies(), listTemplates()]);
        setStrategies(strats);
        setTemplates(tmplts);
        pushLog("SUCCESS", `已加载 ${strats.length} 个策略，${tmplts.length} 个模板`);
      } catch {
        pushLog("WARN", "后端未启动，策略列表为空");
      }
    })();
    void fetch("/api/portfolio/summary")
      .then((r) => r.json())
      .then((d) => setPortfolioSummary(d as PortfolioSummary))
      .catch(() => {});
  }, [setStrategies, setTemplates]);

  // 侧栏：已部署的槽位名称集合
  const activeSlotNames = useMemo(
    () => new Set(portfolioSummary?.strategies.map((s) => s.name) ?? []),
    [portfolioSummary],
  );

  const handleSelectStrategy = async (id: string) => {
    setIsTemplate(false);
    selectStrategy(id);
    try {
      const rec = await getStrategy(id);
      setEditorCode(rec.code);
      setEditorName(rec.meta.name);
      setEditorDescription(rec.meta.description);
      markClean();
      setSub("code");
      pushLog("INFO", `已加载策略: ${rec.meta.name}`);
    } catch (e) {
      pushLog("ERROR", e instanceof Error ? e.message : "加载失败");
    }
  };

  const handleLoadTemplate = async (templateId: string) => {
    setIsTemplate(true);
    selectStrategy(null);
    try {
      const code = await getTemplateCode(templateId);
      const tmpl = templates.find((t) => t.id === templateId);
      setEditorCode(code);
      setEditorName(`${tmpl?.name ?? templateId} (副本)`);
      setEditorDescription(tmpl?.description ?? "");
      markClean();
      setSub("code");
      pushLog("INFO", `已加载模板: ${tmpl?.name ?? templateId}`);
    } catch (e) {
      pushLog("ERROR", e instanceof Error ? e.message : "加载失败");
    }
  };

  const handleNewStrategy = () => {
    setIsTemplate(false);
    selectStrategy(null);
    setEditorCode(
      `from quantpilot.strategy.base import BaseStrategy, StrategyContext\nfrom quantpilot.data.models import OHLCVBar\n\n\nclass MyStrategy(BaseStrategy):\n    name = "我的策略"\n    description = ""\n    default_params = {}\n\n    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:\n        pass\n`,
    );
    setEditorName("新策略");
    setEditorDescription("");
    markClean();
    setSub("code");
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (selectedId && !isTemplate) {
        await updateStrategy(selectedId, { name: editorName, description: editorDescription, code: editorCode });
        pushLog("SUCCESS", `已保存: ${editorName}`);
      } else {
        const result = await createStrategy(editorName, editorDescription, editorCode);
        const strats = await listStrategies();
        setStrategies(strats);
        selectStrategy(result.id);
        setIsTemplate(false);
        pushLog("SUCCESS", `已创建策略 (id: ${result.id})`);
      }
      markClean();
    } catch (e) {
      pushLog("ERROR", e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedId || !confirm(`确认删除策略 "${editorName}"？`)) return;
    try {
      await deleteStrategy(selectedId);
      const strats = await listStrategies();
      setStrategies(strats);
      handleNewStrategy();
      pushLog("INFO", `已删除策略: ${editorName}`);
    } catch (e) {
      pushLog("ERROR", e instanceof Error ? e.message : "删除失败");
    }
  };

  const handleRunBacktest = () => {
    pushLog("INFO", `跳转至回测引擎: ${editorName}`);
    onNavigate?.("validation");
  };

  const saveStateLabel = saving ? "Saving…" : isDirty ? "Unsaved changes" : "Saved";
  const saveStateClass = saving ? "text-blue-400" : isDirty ? "text-yellow-500" : "text-green-500";
  const disableSave = saving || (!isDirty && selectedId !== null && !isTemplate);
  const guideKey =
    sub === "code"
      ? "strategy.code"
      : sub === "generate"
        ? "strategy.generate"
        : sub === "live"
          ? "strategy.live"
          : sub === "optimize"
            ? "strategy.optimize"
            : "strategy.ml";

  return (
    <div
      className="relative flex bg-[#0d1117] rounded-xl overflow-hidden border border-[#30363d]"
      style={{ height: "calc(100vh - 120px)" }}
    >
      {/* ── 左侧栏 */}
      <div className="w-64 shrink-0 border-r border-[#30363d] bg-[#0d1117] flex flex-col">
        <div className="flex-1 overflow-y-auto custom-scrollbar py-6">

          <div className="px-6 py-2 flex items-center justify-between text-[10px] font-bold text-[#8b949e] uppercase tracking-[0.2em]">
            <span>我的策略</span>
            <Plus className="w-3.5 h-3.5 cursor-pointer hover:text-white transition-colors" onClick={handleNewStrategy} />
          </div>

          {strategies.length === 0 ? (
            <p className="px-6 py-2 text-xs text-[#8b949e]/50">暂无策略</p>
          ) : (
            strategies.map((s) => (
              <SidebarItem
                key={s.id}
                icon={FileCode}
                label={s.name}
                active={selectedId === s.id && !isTemplate}
                badge={activeSlotNames.has(s.name) ? "实盘" : undefined}
                onClick={() => void handleSelectStrategy(s.id)}
              />
            ))
          )}

          <div className="mt-8">
            <div className="px-6 py-2 text-[10px] font-bold text-[#8b949e] uppercase tracking-[0.2em]">
              Templates
            </div>
            <SidebarItem
              icon={Code2}
              label="Trading Algorithms"
              hasChildren
              isOpen={openSections.tradingAlgos}
              onClick={() => toggleSection("tradingAlgos")}
            >
              {templates.map((t) => (
                <SidebarItem
                  key={t.id}
                  icon={BarChart3}
                  label={t.name}
                  indent={1}
                  active={isTemplate && editorName.startsWith(t.name)}
                  onClick={() => void handleLoadTemplate(t.id)}
                />
              ))}
              {templates.length === 0 && (
                <p className="px-10 py-1.5 text-xs text-[#8b949e]/40">暂无模板</p>
              )}
            </SidebarItem>
            <SidebarItem
              icon={BrainCircuit}
              label="Machine Learning"
              hasChildren
              isOpen={openSections.mlModels}
              onClick={() => toggleSection("mlModels")}
            >
              <SidebarItem icon={BarChart3} label="LSTM Predictor" indent={1} onClick={() => setSub("ml")} />
              <SidebarItem icon={BarChart3} label="XGBoost Classifier" indent={1} onClick={() => setSub("ml")} />
            </SidebarItem>
            <SidebarItem
              icon={Database}
              label="Trading Analyse"
              hasChildren
              isOpen={openSections.analysis}
              onClick={() => toggleSection("analysis")}
            >
              <SidebarItem icon={BarChart3} label="参数优化" indent={1} onClick={() => setSub("optimize")} />
            </SidebarItem>
          </div>
        </div>

        <div className="p-4 border-t border-[#30363d] flex flex-col gap-1">
          <button
            onClick={() => setSub("optimize")}
            className="flex items-center gap-3 h-9 px-3 rounded-md text-sm text-[#8b949e] hover:text-white hover:bg-[#161b22] transition-colors"
          >
            <Settings className="w-4 h-4" /> Settings
          </button>
          <button
            onClick={() => setShowConsole((v) => !v)}
            className={cn(
              "flex items-center gap-3 h-9 px-3 rounded-md text-sm transition-colors",
              showConsole ? "text-white bg-[#161b22]" : "text-[#8b949e] hover:text-white hover:bg-[#161b22]",
            )}
          >
            <Terminal className="w-4 h-4" /> Debug Console
          </button>
        </div>
      </div>

      {/* ── 右侧主区 */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#0d1117]">

        {/* 顶部组合状态条 */}
        <PortfolioBar summary={portfolioSummary} />

        {/* 策略头部 */}
        <div className="px-8 pt-6 pb-0 space-y-4 shrink-0">
          <div className="flex items-end justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-[11px] font-bold text-[#8b949e] uppercase tracking-[0.2em] mb-1">
                <Code2 className="w-3 h-3" /> Strategy Workshop
              </div>
              <h1 className="text-3xl font-bold text-white tracking-tight">
                {editorName || "My Strategy"}
              </h1>
            </div>
            <div className="flex items-center gap-3 pb-1">
              <button
                onClick={handleRunBacktest}
                className="h-10 px-5 bg-white text-black rounded-lg font-bold hover:bg-[#e1e4e8] transition-colors flex items-center gap-2 text-sm whitespace-nowrap"
              >
                <Play className="w-4 h-4 fill-current" /> Run Backtest
              </button>
            </div>
          </div>

          {/* 策略信息卡 */}
          <div className="flex items-center gap-5 px-4 py-3 bg-[#161b22]/40 border border-[#30363d] rounded-xl">
            <div className="flex-none w-56">
              <label className="text-[10px] uppercase font-bold text-[#8b949e] mb-1.5 block tracking-wider">
                Strategy Name
              </label>
              <input
                value={editorName}
                onChange={(e) => setEditorName(e.target.value)}
                className="h-9 w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 text-sm text-white outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
            <div className="flex-1">
              <label className="text-[10px] uppercase font-bold text-[#8b949e] mb-1.5 block tracking-wider">
                Description
              </label>
              <input
                value={editorDescription}
                onChange={(e) => setEditorDescription(e.target.value)}
                placeholder="Strategy description here (optional)"
                className="h-9 w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 text-sm text-[#8b949e] placeholder-[#8b949e]/40 outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
            <div className="flex items-end gap-3 pb-0.5 shrink-0">
              <div className={cn("flex items-center gap-1.5 text-[11px] font-medium whitespace-nowrap", saveStateClass)}>
                <CheckCircle2 className="w-3.5 h-3.5" /> {saveStateLabel}
              </div>
              <button
                onClick={() => void handleSave()}
                disabled={disableSave}
                className="flex items-center gap-1.5 h-8 px-3 text-[#8b949e] hover:text-white text-sm rounded-md hover:bg-[#21262d] transition-colors disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" /> {saving ? "Saving…" : isDirty ? "Save Now" : "Saved"}
              </button>
              {selectedId && !isTemplate && (
                <button
                  onClick={() => void handleDelete()}
                  className="flex items-center gap-1.5 h-8 px-3 text-red-400 hover:text-red-300 text-sm rounded-md hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Delete
                </button>
              )}
            </div>
          </div>

          {/* 子标签栏 */}
          <div className="flex gap-0 border-b border-[#30363d]">
            {SUBS.map((s) => (
              <button
                key={s.key}
                onClick={() => setSub(s.key)}
                className={cn(
                  "px-5 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px",
                  sub === s.key
                    ? "border-white text-white"
                    : "border-transparent text-[#8b949e] hover:text-white",
                )}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── 内容区 */}
        {sub === "code" ? (
          <div className="flex-1 flex flex-col min-h-0 px-8 py-5 gap-4">
            <div className="flex-1 min-h-0 border border-[#30363d] bg-[#161b22]/40 rounded-xl overflow-hidden flex flex-col shadow-2xl">
              <div className="flex items-center justify-between px-4 h-10 border-b border-[#30363d] bg-[#161b22]/60 shrink-0">
                <div className="flex items-center gap-2 text-xs font-bold text-[#8b949e] uppercase tracking-widest">
                  <FileCode className="w-3.5 h-3.5" /> main.py
                </div>
                <div className="flex items-center gap-4 text-[10px] text-[#8b949e]/60 font-mono uppercase tracking-wider">
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500/50" /> Python 3.10
                  </div>
                  <div className="h-3 w-px bg-[#30363d]" />
                  <span>UTF-8</span>
                </div>
              </div>
              <div className="flex-1 min-h-0">
                <StrategyEditor
                  value={editorCode}
                  onChange={setEditorCode}
                  height="100%"
                  onMount={(editor) => { editorRef.current = editor; }}
                />
              </div>
            </div>

            {showConsole && (
              <div className="h-44 border border-[#30363d] bg-[#161b22]/40 rounded-xl flex flex-col overflow-hidden shrink-0">
                <div className="flex items-center justify-between px-4 h-10 border-b border-[#30363d] bg-[#161b22]/60 shrink-0">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#8b949e]">
                    <Terminal className="w-3.5 h-3.5" /> Debug Console
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setLogs([
                        { level: "INFO",    text: "Console cleared." },
                        { level: "SUCCESS", text: "Engine ready." },
                      ])}
                      className="h-7 w-7 flex items-center justify-center text-[#8b949e] hover:text-white rounded transition-colors"
                      title="Clear"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setShowConsole(false)}
                      className="h-7 w-7 flex items-center justify-center text-[#8b949e] hover:text-white rounded transition-colors"
                      title="Close"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar p-4 font-mono text-xs text-[#8b949e] space-y-1">
                  {logs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                      <span className={cn("font-bold shrink-0", LOG_COLOR[log.level])}>[{log.level}]</span>
                      <span>{log.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : sub === "live" ? (
          <div className="flex-1 overflow-y-auto custom-scrollbar px-8 py-5">
            <LiveTradingTab currentStrategyId={selectedId} />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto custom-scrollbar px-8 py-5">
            {sub === "generate" && <StrategyGeneratorPanel />}
            {sub === "optimize" && <OptimizationPanel />}
            {sub === "ml"       && <MLStrategyPanel />}
          </div>
        )}
      </div>
      <FeatureGuideButton guideKey={guideKey} className="bottom-5 right-5" />
    </div>
  );
}
