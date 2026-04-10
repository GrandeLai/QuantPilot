import React, { useState, useEffect, useMemo } from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Percent, 
  Zap, 
  Activity, 
  Info, 
  ChevronDown,
  RefreshCw,
  Calculator,
  BarChart3,
  Search,
  Bell,
  User
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine
} from "recharts";
import { cn } from "./lib/utils";

// --- Types ---

interface Greeks {
  price: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}

interface PayoffData {
  underlying: number;
  payoff: number;
  profit: number;
}

// --- Components ---

const InputField = ({ 
  label, 
  value, 
  onChange, 
  type = "number", 
  step = "0.01",
  icon: Icon,
  suffix
}: { 
  label: string; 
  value: string | number; 
  onChange: (val: string) => void; 
  type?: string;
  step?: string;
  icon?: any;
  suffix?: string;
}) => (
  <div className="flex flex-col gap-1.5 mb-4">
    <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
      {Icon && <Icon size={12} className="text-gray-500" />}
      {label}
    </label>
    <div className="relative group">
      <input
        type={type}
        step={step}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#2a2e39] border border-[#363a45] rounded-md px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-[#2962ff] transition-colors group-hover:border-[#434651]"
      />
      {suffix && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-gray-500">
          {suffix}
        </span>
      )}
    </div>
  </div>
);

const GreekCard = ({ label, value, description, symbol }: { label: string; value: number; description: string; symbol: string }) => (
  <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4 flex flex-col gap-1 hover:border-[#363a45] transition-all group">
    <div className="flex justify-between items-start">
      <span className="text-[11px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-1">
        {label} <span className="text-gray-600 font-normal">({symbol})</span>
      </span>
      <div className="opacity-0 group-hover:opacity-100 transition-opacity">
        <Info size={12} className="text-gray-600 cursor-help" />
      </div>
    </div>
    <div className="text-2xl font-mono font-medium text-gray-100">
      {value.toFixed(4)}
    </div>
    <div className="text-[10px] text-gray-500 leading-tight mt-1">
      {description}
    </div>
  </div>
);

export default function App() {
  const [S, setS] = useState<string>("100");
  const [K, setK] = useState<string>("100");
  const [T, setT] = useState<string>("1");
  const [r, setr] = useState<string>("0.05");
  const [sigma, setSigma] = useState<string>("0.20");
  const [type, setType] = useState<"call" | "put">("call");
  const [marketPrice, setMarketPrice] = useState<string>("");
  
  const [greeks, setGreeks] = useState<Greeks | null>(null);
  const [iv, setIv] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [ivLoading, setIvLoading] = useState(false);

  const calculateGreeks = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/options/greeks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ S, K, T, r, sigma, type }),
      });
      const data = await response.json();
      setGreeks(data);
    } catch (error) {
      console.error("Failed to calculate greeks", error);
    } finally {
      setLoading(false);
    }
  };

  const calculateIV = async () => {
    if (!marketPrice) return;
    setIvLoading(true);
    try {
      const response = await fetch("/api/options/implied-vol", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ marketPrice, S, K, T, r, type }),
      });
      const data = await response.json();
      setIv(data.iv);
    } catch (error) {
      console.error("Failed to calculate IV", error);
    } finally {
      setIvLoading(false);
    }
  };

  useEffect(() => {
    calculateGreeks();
  }, []);

  const payoffData = useMemo(() => {
    if (!greeks) return [];
    const data: PayoffData[] = [];
    const sNum = Number(S);
    const kNum = Number(K);
    const range = sNum * 0.5;
    const start = Math.max(0, sNum - range);
    const end = sNum + range;
    const step = (end - start) / 50;

    for (let x = start; x <= end; x += step) {
      let payoff = 0;
      if (type === "call") {
        payoff = Math.max(0, x - kNum);
      } else {
        payoff = Math.max(0, kNum - x);
      }
      data.push({
        underlying: x,
        payoff: payoff,
        profit: payoff - greeks.price
      });
    }
    return data;
  }, [S, K, type, greeks]);

  return (
    <div className="min-h-screen bg-[#131722] text-gray-300 font-sans selection:bg-[#2962ff]/30">
      {/* Header */}
      <header className="h-12 border-b border-[#2a2e39] bg-[#131722] flex items-center justify-between px-4 sticky top-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-[#2962ff] rounded flex items-center justify-center">
              <Zap size={14} className="text-white fill-white" />
            </div>
            <span className="font-bold text-white tracking-tight">QuantPilot</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-1">
            {["看板", "策略", "交易", "回测", "期权", "组合", "AI", "系统"].map((item) => (
              <button 
                key={item} 
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded transition-colors",
                  item === "期权" ? "bg-[#2a2e39] text-white" : "text-gray-400 hover:text-gray-200 hover:bg-[#1e222d]"
                )}
              >
                {item}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative hidden sm:block">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input 
              placeholder="搜索... ⌘K" 
              className="bg-[#1e222d] border border-[#2a2e39] rounded-md pl-9 pr-3 py-1.5 text-xs w-48 focus:outline-none focus:border-[#2962ff]"
            />
          </div>
          <button className="p-1.5 hover:bg-[#1e222d] rounded-md text-gray-400">
            <Bell size={18} />
          </button>
          <div className="w-8 h-8 rounded-full bg-[#2a2e39] flex items-center justify-center text-xs font-bold text-white border border-[#363a45]">
            QP
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-48px)]">
        {/* Sidebar */}
        <aside className="w-72 border-r border-[#2a2e39] bg-[#131722] overflow-y-auto p-5 shrink-0 custom-scrollbar">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">期权参数</h2>
            <button 
              onClick={calculateGreeks}
              className="p-1.5 hover:bg-[#1e222d] rounded-md text-[#2962ff] transition-transform active:rotate-180 duration-500"
            >
              <RefreshCw size={14} />
            </button>
          </div>

          <div className="space-y-1">
            <InputField label="标的现价" value={S} onChange={setS} icon={Activity} />
            <InputField label="行权价" value={K} onChange={setK} icon={TrendingUp} />
            <InputField label="到期时间 (年)" value={T} onChange={setT} icon={Clock} />
            <InputField label="无风险利率" value={r} onChange={setr} icon={Percent} />
            <InputField label="波动率" value={sigma} onChange={setSigma} icon={Zap} suffix="σ" />
            
            <div className="flex flex-col gap-1.5 mb-6">
              <label className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">期权类型</label>
              <div className="grid grid-cols-2 gap-2">
                <button 
                  onClick={() => setType("call")}
                  className={cn(
                    "py-2 text-xs font-bold rounded-md border transition-all",
                    type === "call" 
                      ? "bg-[#2962ff] border-[#2962ff] text-white shadow-[0_0_15px_rgba(41,98,255,0.3)]" 
                      : "bg-[#1e222d] border-[#2a2e39] text-gray-400 hover:border-[#363a45]"
                  )}
                >
                  看涨 (Call)
                </button>
                <button 
                  onClick={() => setType("put")}
                  className={cn(
                    "py-2 text-xs font-bold rounded-md border transition-all",
                    type === "put" 
                      ? "bg-[#f23645] border-[#f23645] text-white shadow-[0_0_15px_rgba(242,54,69,0.3)]" 
                      : "bg-[#1e222d] border-[#2a2e39] text-gray-400 hover:border-[#363a45]"
                  )}
                >
                  看跌 (Put)
                </button>
              </div>
            </div>

            <button 
              onClick={calculateGreeks}
              disabled={loading}
              className="w-full bg-[#2962ff] hover:bg-[#1e53e5] text-white font-bold py-2.5 rounded-md text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <RefreshCw size={16} className="animate-spin" /> : <Calculator size={16} />}
              计算 Greeks
            </button>
          </div>

          <div className="mt-8 pt-8 border-t border-[#2a2e39]">
            <h3 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-4">隐含波动率反推</h3>
            <InputField label="市场价格" value={marketPrice} onChange={setMarketPrice} icon={BarChart3} />
            <button 
              onClick={calculateIV}
              disabled={ivLoading || !marketPrice}
              className="w-full bg-[#ff9800] hover:bg-[#e68a00] text-white font-bold py-2 rounded-md text-xs transition-all disabled:opacity-50"
            >
              {ivLoading ? "计算中..." : "求 IV"}
            </button>
            
            {iv !== null && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-3 bg-[#1e222d] border border-[#ff9800]/30 rounded-md"
              >
                <div className="text-[10px] text-gray-500 uppercase font-bold">隐含波动率 (IV)</div>
                <div className="text-xl font-mono font-bold text-[#ff9800]">{(iv * 100).toFixed(2)}%</div>
              </motion.div>
            )}
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 bg-[#131722] overflow-y-auto custom-scrollbar p-6">
          <AnimatePresence mode="wait">
            {greeks ? (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-6xl mx-auto space-y-6"
              >
                {/* Price Header */}
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 bg-[#1e222d] border border-[#2a2e39] rounded-xl p-6 shadow-xl">
                  <div>
                    <div className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-1">理论价格 (Theoretical Price)</div>
                    <div className="flex items-baseline gap-3">
                      <span className="text-5xl font-mono font-bold text-white tracking-tighter">
                        {greeks.price.toFixed(4)}
                      </span>
                      <span className={cn(
                        "text-sm font-bold px-2 py-0.5 rounded",
                        type === "call" ? "bg-[#2962ff]/10 text-[#2962ff]" : "bg-[#f23645]/10 text-[#f23645]"
                      )}>
                        {type.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-8">
                    <div className="text-right">
                      <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">内在价值</div>
                      <div className="text-lg font-mono text-gray-200">
                        {type === "call" ? Math.max(0, Number(S) - Number(K)).toFixed(4) : Math.max(0, Number(K) - Number(S)).toFixed(4)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">时间价值</div>
                      <div className="text-lg font-mono text-gray-200">
                        {Math.max(0, greeks.price - (type === "call" ? Math.max(0, Number(S) - Number(K)) : Math.max(0, Number(K) - Number(S)))).toFixed(4)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Greeks Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                  <GreekCard label="Delta" symbol="δ" value={greeks.delta} description="股价变动 1 元时，期权价格的变动量" />
                  <GreekCard label="Gamma" symbol="γ" value={greeks.gamma} description="Delta 本身的变动速度" />
                  <GreekCard label="Theta" symbol="θ" value={greeks.theta} description="时间流逝对期权价格的每日影响" />
                  <GreekCard label="Vega" symbol="ν" value={greeks.vega} description="波动率变化 1% 对期权价格的影响" />
                  <GreekCard label="Rho" symbol="ρ" value={greeks.rho} description="利率变化 1% 对期权价格的影响" />
                </div>

                {/* Chart Section */}
                <div className="bg-[#1e222d] border border-[#2a2e39] rounded-xl p-6 shadow-xl">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <BarChart3 size={16} className="text-[#2962ff]" />
                      盈亏分析图 (Payoff Chart)
                    </h3>
                    <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest">
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-0.5 bg-[#2962ff]"></div>
                        <span className="text-gray-400">到期盈亏</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="w-3 h-0.5 bg-[#f23645]"></div>
                        <span className="text-gray-400">盈亏平衡点</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={payoffData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#2962ff" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#2962ff" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2e39" vertical={false} />
                        <XAxis 
                          dataKey="underlying" 
                          stroke="#434651" 
                          fontSize={10} 
                          tickFormatter={(val) => val.toFixed(0)}
                          label={{ value: '标的价格', position: 'insideBottomRight', offset: -5, fontSize: 10, fill: '#434651' }}
                        />
                        <YAxis 
                          stroke="#434651" 
                          fontSize={10} 
                          label={{ value: '盈亏', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#434651' }}
                        />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1e222d', border: '1px solid #363a45', borderRadius: '4px', fontSize: '11px' }}
                          itemStyle={{ color: '#fff' }}
                          labelStyle={{ color: '#8e9299', marginBottom: '4px' }}
                          formatter={(value: number) => [value.toFixed(2), '盈亏']}
                          labelFormatter={(label: number) => `标的价格: ${label.toFixed(2)}`}
                        />
                        <ReferenceLine y={0} stroke="#434651" strokeWidth={1} />
                        <ReferenceLine x={Number(K)} stroke="#8e9299" strokeDasharray="3 3" label={{ value: '行权价', position: 'top', fill: '#8e9299', fontSize: 10 }} />
                        <Area 
                          type="monotone" 
                          dataKey="profit" 
                          stroke="#2962ff" 
                          strokeWidth={2}
                          fillOpacity={1} 
                          fill="url(#colorProfit)" 
                          animationDuration={1000}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Footer Info */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-[11px] text-gray-500 leading-relaxed">
                  <div className="space-y-2">
                    <div className="font-bold text-gray-400 uppercase tracking-widest">模型说明</div>
                    <p>本工具采用标准的 Black-Scholes-Merton 模型进行定价。该模型假设标的资产价格服从几何布朗运动，且波动率和无风险利率在期权有效期内保持不变。</p>
                  </div>
                  <div className="space-y-2">
                    <div className="font-bold text-gray-400 uppercase tracking-widest">风险提示</div>
                    <p>理论价格仅供参考，实际市场价格受供需关系、流动性溢价及偏斜（Skew）等多种因素影响。交易衍生品具有高风险，请谨慎操作。</p>
                  </div>
                  <div className="space-y-2">
                    <div className="font-bold text-gray-400 uppercase tracking-widest"> Greeks 含义</div>
                    <p>Delta 衡量方向风险，Gamma 衡量 Delta 的稳定性，Theta 衡量时间损耗，Vega 衡量波动率敏感度，Rho 衡量利率敏感度。</p>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-4">
                <div className="w-16 h-16 bg-[#1e222d] rounded-full flex items-center justify-center border border-[#2a2e39]">
                  <Calculator size={32} className="text-gray-600" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-400">输入参数后点击「计算 Greeks」</p>
                  <p className="text-xs mt-1">理论价格与风险指标将在此处实时显示</p>
                </div>
              </div>
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* Status Bar */}
      <footer className="h-6 border-t border-[#2a2e39] bg-[#131722] flex items-center justify-between px-3 text-[10px] font-medium text-gray-500">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span>本地优先</span>
          </div>
          <span>QUANT PILOT V0.1</span>
        </div>
        <div className="flex items-center gap-4">
          <span>量化交易平台</span>
        </div>
      </footer>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
          height: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #2a2e39;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #363a45;
        }
      `}</style>
    </div>
  );
}
