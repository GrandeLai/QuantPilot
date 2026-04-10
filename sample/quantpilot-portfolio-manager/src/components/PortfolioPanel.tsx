import React, { useState, useMemo } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  PieChart, 
  Layers, 
  ArrowUpRight, 
  ArrowDownRight,
  Info,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { cn } from '@/src/lib/utils';
import { motion, AnimatePresence } from 'motion/react';

// --- Types ---

interface Strategy {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'paused' | 'error';
  allocation: number;
  pnl: number;
  pnlPercent: number;
  drawdown: number;
  sharpe: number;
}

interface PortfolioSummary {
  totalCapital: number;
  allocatedCapital: number;
  totalPnl: number;
  totalPnlPercent: number;
  dailyPnl: number;
  dailyPnlPercent: number;
  activeStrategies: number;
}

// --- Mock Data ---

const MOCK_STRATEGIES: Strategy[] = [
  { id: '1', name: 'Trend Follower BTC', type: 'Trend', status: 'active', allocation: 2500000, pnl: 125000, pnlPercent: 5.0, drawdown: 2.1, sharpe: 1.8 },
  { id: '2', name: 'Mean Reversion ETH', type: 'Mean Rev', status: 'active', allocation: 1500000, pnl: -45000, pnlPercent: -3.0, drawdown: 4.5, sharpe: 1.2 },
  { id: '3', name: 'Grid Bot SOL', type: 'Grid', status: 'active', allocation: 2000000, pnl: 88000, pnlPercent: 4.4, drawdown: 1.8, sharpe: 2.1 },
  { id: '4', name: 'Arbitrage DEX', type: 'Arb', status: 'paused', allocation: 1000000, pnl: 12000, pnlPercent: 1.2, drawdown: 0.5, sharpe: 3.5 },
  { id: '5', name: 'Market Maker', type: 'MM', status: 'active', allocation: 3000000, pnl: 210000, pnlPercent: 7.0, drawdown: 1.2, sharpe: 2.8 },
];

const MOCK_SUMMARY: PortfolioSummary = {
  totalCapital: 10000000,
  allocatedCapital: 10000000,
  totalPnl: 390000,
  totalPnlPercent: 3.9,
  dailyPnl: 15000,
  dailyPnlPercent: 0.15,
  activeStrategies: 4,
};

const MOCK_CHART_DATA = Array.from({ length: 30 }, (_, i) => ({
  date: `2024-03-${String(i + 1).padStart(2, '0')}`,
  value: 10000000 + Math.random() * 500000 + i * 20000,
}));

const MOCK_CORRELATION = [
  [1.00, 0.12, -0.05, 0.02, 0.15],
  [0.12, 1.00, 0.08, -0.12, 0.05],
  [-0.05, 0.08, 1.00, 0.15, -0.10],
  [0.02, -0.12, 0.15, 1.00, 0.08],
  [0.15, 0.05, -0.10, 0.08, 1.00],
];

// --- Components ---

const MetricCard = ({ title, value, subValue, trend, icon: Icon }: any) => (
  <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-5 flex flex-col gap-2 relative overflow-hidden group">
    <div className="flex justify-between items-start">
      <span className="text-[#8E9299] text-xs font-mono uppercase tracking-wider">{title}</span>
      <div className="p-2 bg-[#1C1E22] rounded-lg text-[#8E9299] group-hover:text-white transition-colors">
        <Icon size={16} />
      </div>
    </div>
    <div className="flex flex-col">
      <span className="text-2xl font-bold text-white tracking-tight">{value}</span>
      <div className="flex items-center gap-1.5 mt-1">
        {trend !== undefined && (
          <span className={cn(
            "text-xs font-medium flex items-center gap-0.5",
            trend >= 0 ? "text-[#00C087]" : "text-[#FF4D4D]"
          )}>
            {trend >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
            {Math.abs(trend)}%
          </span>
        )}
        <span className="text-[#8E9299] text-xs">{subValue}</span>
      </div>
    </div>
    <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-[#2A2D35] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
  </div>
);

const CorrelationHeatmap = ({ strategies, matrix }: { strategies: Strategy[], matrix: number[][] }) => {
  const getColor = (val: number) => {
    if (val === 1) return 'bg-[#2A2D35] text-white/40';
    const abs = Math.abs(val);
    if (val > 0) {
      if (abs > 0.7) return 'bg-[#FF4D4D]/20 text-[#FF4D4D]';
      if (abs > 0.3) return 'bg-[#FF4D4D]/10 text-[#FF4D4D]/80';
      return 'bg-[#1C1E22] text-[#8E9299]';
    } else {
      if (abs > 0.7) return 'bg-[#00C087]/20 text-[#00C087]';
      if (abs > 0.3) return 'bg-[#00C087]/10 text-[#00C087]/80';
      return 'bg-[#1C1E22] text-[#8E9299]';
    }
  };

  return (
    <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Layers size={18} className="text-[#8E9299]" />
          <h3 className="text-white font-semibold">相关性矩阵</h3>
          <div className="group relative">
            <Info size={14} className="text-[#8E9299] cursor-help" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-[#1C1E22] border border-[#2A2D35] rounded text-[10px] text-[#8E9299] opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
              衡量策略间盈亏的相关程度。1为完全同步，0为不相关，-1为完全对冲。
            </div>
          </div>
        </div>
        <button className="text-[#8E9299] hover:text-white transition-colors">
          <RefreshCw size={14} />
        </button>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[400px]">
          {/* Header Row */}
          <div className="grid grid-cols-[100px_repeat(5,1fr)] gap-1 mb-1">
            <div />
            {strategies.map(s => (
              <div key={s.id} className="text-[10px] text-[#8E9299] font-mono uppercase text-center truncate px-1" title={s.name}>
                {s.name.split(' ')[0]}
              </div>
            ))}
          </div>

          {/* Rows */}
          {matrix.map((row, i) => (
            <div key={i} className="grid grid-cols-[100px_repeat(5,1fr)] gap-1 mb-1">
              <div className="text-[10px] text-[#8E9299] font-mono uppercase flex items-center truncate pr-2" title={strategies[i].name}>
                {strategies[i].name.split(' ')[0]}
              </div>
              {row.map((val, j) => (
                <div 
                  key={j} 
                  className={cn(
                    "aspect-square flex items-center justify-center rounded text-[11px] font-mono transition-all hover:scale-105 cursor-default",
                    getColor(val)
                  )}
                >
                  {val.toFixed(2)}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-6 flex justify-between items-center">
        <div className="flex gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#FF4D4D]" />
            <span className="text-[10px] text-[#8E9299] uppercase tracking-wider">高相关</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#00C087]" />
            <span className="text-[10px] text-[#8E9299] uppercase tracking-wider">低相关/对冲</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function PortfolioPanel() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredStrategies = useMemo(() => {
    return MOCK_STRATEGIES.filter(s => 
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.type.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm]);

  return (
    <div className="min-h-screen bg-[#0B0C0E] text-[#E1E4E8] p-6 font-sans selection:bg-white/10">
      <div className="max-w-[1600px] mx-auto space-y-6">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[#8E9299] mb-1">
              <PieChart size={16} />
              <span className="text-xs font-mono uppercase tracking-[0.2em]">Portfolio Management</span>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">组合概览</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8E9299]" size={14} />
              <input 
                type="text" 
                placeholder="搜索策略..." 
                className="bg-[#151619] border border-[#2A2D35] rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-[#4A4D55] transition-colors w-64"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="bg-[#151619] border border-[#2A2D35] rounded-lg p-2 text-[#8E9299] hover:text-white transition-colors">
              <Filter size={18} />
            </button>
            <button className="bg-white text-black font-semibold text-sm px-4 py-2 rounded-lg hover:bg-[#E1E4E8] transition-colors">
              添加策略
            </button>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard 
            title="总资产 (USD)" 
            value={`$${MOCK_SUMMARY.totalCapital.toLocaleString()}`} 
            subValue="账户净值"
            icon={Activity}
          />
          <MetricCard 
            title="累计盈亏" 
            value={`$${MOCK_SUMMARY.totalPnl.toLocaleString()}`} 
            trend={MOCK_SUMMARY.totalPnlPercent}
            subValue="总回报率"
            icon={TrendingUp}
          />
          <MetricCard 
            title="当日盈亏" 
            value={`$${MOCK_SUMMARY.dailyPnl.toLocaleString()}`} 
            trend={MOCK_SUMMARY.dailyPnlPercent}
            subValue="今日变动"
            icon={TrendingUp}
          />
          <MetricCard 
            title="分散化评分" 
            value="84/100" 
            subValue="风险分散程度良好"
            icon={PieChart}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left: Strategy List & Chart */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Equity Chart */}
            <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <TrendingUp size={18} className="text-[#00C087]" />
                  净值曲线
                </h3>
                <div className="flex bg-[#1C1E22] rounded-lg p-1">
                  {['1D', '1W', '1M', 'ALL'].map(t => (
                    <button key={t} className={cn(
                      "px-3 py-1 text-[10px] font-bold rounded-md transition-all",
                      t === '1M' ? "bg-[#2A2D35] text-white" : "text-[#8E9299] hover:text-white"
                    )}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={MOCK_CHART_DATA}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00C087" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00C087" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1C1E22" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#4A4D55" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false}
                      tickFormatter={(val) => val.split('-')[2]}
                    />
                    <YAxis 
                      stroke="#4A4D55" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false}
                      tickFormatter={(val) => `$${(val / 1000000).toFixed(1)}M`}
                      domain={['dataMin - 100000', 'dataMax + 100000']}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1C1E22', border: '1px solid #2A2D35', borderRadius: '8px', fontSize: '12px' }}
                      itemStyle={{ color: '#00C087' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#00C087" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorValue)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Strategy Table */}
            <div className="bg-[#151619] border border-[#2A2D35] rounded-xl overflow-hidden">
              <div className="p-6 border-bottom border-[#2A2D35]">
                <h3 className="text-white font-semibold">策略列表</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#1C1E22]/50 border-y border-[#2A2D35]">
                      <th className="px-6 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">策略名称</th>
                      <th className="px-6 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">状态</th>
                      <th className="px-6 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">分配资金</th>
                      <th className="px-6 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">盈亏</th>
                      <th className="px-6 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">回撤</th>
                      <th className="px-6 py-3 text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">夏普比率</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#2A2D35]">
                    {filteredStrategies.map((s) => (
                      <tr key={s.id} className="hover:bg-[#1C1E22]/30 transition-colors group cursor-pointer">
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-white group-hover:text-[#00C087] transition-colors">{s.name}</span>
                            <span className="text-[10px] text-[#8E9299] font-mono">{s.type}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className={cn(
                              "w-1.5 h-1.5 rounded-full",
                              s.status === 'active' ? "bg-[#00C087]" : s.status === 'paused' ? "bg-[#FFB800]" : "bg-[#FF4D4D]"
                            )} />
                            <span className="text-xs capitalize">{s.status}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm font-mono">${(s.allocation / 1000).toLocaleString()}K</td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className={cn("text-sm font-mono", s.pnl >= 0 ? "text-[#00C087]" : "text-[#FF4D4D]")}>
                              {s.pnl >= 0 ? '+' : ''}{s.pnl.toLocaleString()}
                            </span>
                            <span className={cn("text-[10px] font-mono", s.pnl >= 0 ? "text-[#00C087]/70" : "text-[#FF4D4D]/70")}>
                              {s.pnlPercent}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm font-mono text-[#FF4D4D]">{s.drawdown}%</td>
                        <td className="px-6 py-4 text-sm font-mono text-[#8E9299]">{s.sharpe}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right: Correlation Matrix */}
          <div className="space-y-6">
            <CorrelationHeatmap strategies={MOCK_STRATEGIES} matrix={MOCK_CORRELATION} />
            
            {/* Risk Insights Card */}
            <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <Info size={18} className="text-[#FFB800]" />
                风险洞察
              </h3>
              <div className="space-y-4">
                <div className="p-3 bg-[#1C1E22] rounded-lg border-l-2 border-[#FF4D4D]">
                  <p className="text-xs text-[#E1E4E8] leading-relaxed">
                    <span className="font-bold text-[#FF4D4D]">警报</span>: "Trend Follower BTC" 与 "Market Maker" 的相关性近期上升至 0.15，建议关注波动。
                  </p>
                </div>
                <div className="p-3 bg-[#1C1E22] rounded-lg border-l-2 border-[#00C087]">
                  <p className="text-xs text-[#E1E4E8] leading-relaxed">
                    <span className="font-bold text-[#00C087]">建议</span>: "Mean Reversion ETH" 提供了良好的负相关性，可考虑增加分配。
                  </p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
