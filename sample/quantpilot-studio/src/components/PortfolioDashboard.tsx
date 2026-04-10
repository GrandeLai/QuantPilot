import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { 
  Search, 
  Plus, 
  Filter, 
  TrendingUp, 
  TrendingDown, 
  PieChart, 
  Activity,
  Info,
  RefreshCw,
  Circle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';

// --- Mock Data ---
const chartData = Array.from({ length: 30 }, (_, i) => ({
  name: (i + 1).toString().padStart(2, '0'),
  value: 10.3 + Math.sin(i * 0.5) * 0.2 + Math.random() * 0.1,
}));

const correlationData = [
  { label: 'TREND', values: [1.00, 0.12, -0.05, 0.02, 0.15] },
  { label: 'MEAN', values: [0.12, 1.00, 0.08, -0.12, 0.05] },
  { label: 'GRID', values: [-0.05, 0.08, 1.00, 0.15, -0.10] },
  { label: 'ARBITRAGE', values: [0.02, -0.12, 0.15, 1.00, 0.04] },
  { label: 'MARKET', values: [0.15, 0.05, -0.10, 0.04, 1.00] },
];

const strategies = [
  { name: 'Trend Follower v2', status: 'Running', allocation: '$2,500,000', pnl: '+$120,000', drawdown: '4.2%', sharpe: '2.1' },
  { name: 'Mean Reversion Pro', status: 'Running', allocation: '$1,800,000', pnl: '+$45,000', drawdown: '2.8%', sharpe: '1.8' },
  { name: 'Grid Bot Alpha', status: 'Paused', allocation: '$1,200,000', pnl: '-$12,000', drawdown: '8.5%', sharpe: '0.9' },
];

// --- Sub-components ---

const KPICard = ({ title, value, subValue, change, icon: Icon, trend }: any) => (
  <div className="bg-[#161b22]/40 border border-[#30363d] rounded-xl p-5 flex flex-col justify-between group hover:border-primary/50 transition-all">
    <div className="flex justify-between items-start">
      <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">{title}</div>
      <div className="p-2 rounded-lg bg-[#30363d]/30 text-muted-foreground group-hover:text-primary transition-colors">
        <Icon className="w-4 h-4" />
      </div>
    </div>
    <div className="mt-4">
      <div className="text-3xl font-bold text-white tracking-tight">{value}</div>
      <div className="flex items-center gap-2 mt-1">
        {change && (
          <div className={cn("flex items-center text-xs font-bold", trend === 'up' ? "text-green-500" : "text-red-500")}>
            {trend === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
            {change}
          </div>
        )}
        <div className="text-xs text-muted-foreground">{subValue}</div>
      </div>
    </div>
  </div>
);

export const PortfolioDashboard = () => {
  return (
    <div className="flex-1 bg-[#0d1117] flex flex-col overflow-hidden relative">
      <ScrollArea className="flex-1">
        <div className="p-8 max-w-[1600px] mx-auto w-full space-y-8">
          
          {/* Header Section */}
          <div className="flex items-end justify-between">
            <div>
              <div className="flex items-center gap-2 text-[11px] font-bold text-muted-foreground uppercase tracking-[0.2em] mb-1">
                <Activity className="w-3 h-3" />
                Portfolio Management
              </div>
              <h1 className="text-4xl font-bold text-white tracking-tight">组合概览</h1>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input 
                  placeholder="搜索策略..." 
                  className="h-10 w-64 bg-[#161b22] border-[#30363d] pl-10 focus-visible:ring-primary"
                />
              </div>
              <Button variant="outline" size="icon" className="h-10 w-10 border-[#30363d] bg-[#161b22]">
                <Filter className="w-4 h-4" />
              </Button>
              <Button className="h-10 px-6 bg-white text-black hover:bg-gray-200 font-bold">
                <Plus className="w-4 h-4 mr-2" />
                添加策略
              </Button>
            </div>
          </div>

          {/* KPI Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KPICard 
              title="总资产 (USD)" 
              value="$10,000,000" 
              subValue="账户净值" 
              icon={Activity} 
            />
            <KPICard 
              title="累计盈亏" 
              value="$390,000" 
              subValue="总回报率" 
              change="3.9%" 
              trend="up"
              icon={TrendingUp} 
            />
            <KPICard 
              title="当日盈亏" 
              value="$15,000" 
              subValue="今日变动" 
              change="0.15%" 
              trend="up"
              icon={TrendingUp} 
            />
            <KPICard 
              title="分散化评分" 
              value="84/100" 
              subValue="风险分散程度良好" 
              icon={PieChart} 
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Chart Area */}
            <div className="lg:col-span-2 bg-[#161b22]/40 border border-[#30363d] rounded-xl p-6 flex flex-col">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-500" />
                  <h3 className="text-lg font-bold text-white">净值曲线</h3>
                </div>
                <div className="flex bg-[#0d1117] rounded-lg p-1 border border-[#30363d]">
                  {['1D', '1W', '1M', 'ALL'].map((range) => (
                    <button 
                      key={range}
                      className={cn(
                        "px-4 py-1.5 text-[10px] font-bold rounded-md transition-all",
                        range === '1M' ? "bg-[#30363d] text-white" : "text-muted-foreground hover:text-white"
                      )}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                    <XAxis 
                      dataKey="name" 
                      stroke="#8b949e" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false}
                      dy={10}
                    />
                    <YAxis 
                      stroke="#8b949e" 
                      fontSize={10} 
                      tickLine={false} 
                      axisLine={false}
                      domain={['dataMin - 0.1', 'dataMax + 0.1']}
                      tickFormatter={(val) => `$${val}M`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '8px' }}
                      itemStyle={{ color: '#10b981' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#10b981" 
                      strokeWidth={3}
                      fillOpacity={1} 
                      fill="url(#colorValue)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Correlation Matrix */}
            <div className="bg-[#161b22]/40 border border-[#30363d] rounded-xl p-6 flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <LayoutGrid className="w-5 h-5 text-primary" />
                  <h3 className="text-lg font-bold text-white">相关性矩阵</h3>
                  <Info className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex-1 flex flex-col">
                <div className="grid grid-cols-6 gap-2 mb-2">
                  <div />
                  {['TREND', 'MEAN', 'GRID', 'ARBIT', 'MARKET'].map(h => (
                    <div key={h} className="text-[9px] font-bold text-muted-foreground text-center uppercase">{h}</div>
                  ))}
                </div>
                {correlationData.map((row, i) => (
                  <div key={row.label} className="grid grid-cols-6 gap-2 mb-2 items-center">
                    <div className="text-[9px] font-bold text-muted-foreground uppercase">{row.label}</div>
                    {row.values.map((val, j) => (
                      <div 
                        key={j} 
                        className={cn(
                          "aspect-square rounded flex items-center justify-center text-[11px] font-mono border border-[#30363d]",
                          val === 1 ? "bg-primary/20 text-primary border-primary/30" : "bg-[#0d1117] text-muted-foreground"
                        )}
                      >
                        {val.toFixed(2)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              <div className="mt-6 flex items-center gap-6">
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  高相关
                </div>
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  低相关/对冲
                </div>
              </div>
            </div>
          </div>

          {/* Strategy List Area */}
          <div className="bg-[#161b22]/40 border border-[#30363d] rounded-xl overflow-hidden">
            <div className="p-6 border-b border-[#30363d]">
              <h3 className="text-lg font-bold text-white">策略列表</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#0d1117]/50 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                    <th className="px-6 py-4">策略名称</th>
                    <th className="px-6 py-4">状态</th>
                    <th className="px-6 py-4">分配资金</th>
                    <th className="px-6 py-4">盈亏</th>
                    <th className="px-6 py-4">回撤</th>
                    <th className="px-6 py-4 text-right">夏普比率</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#30363d]">
                  {strategies.map((s, i) => (
                    <tr key={i} className="hover:bg-[#30363d]/20 transition-colors group">
                      <td className="px-6 py-4 text-sm font-medium text-white">{s.name}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Circle className={cn("w-2 h-2 fill-current", s.status === 'Running' ? "text-green-500" : "text-yellow-500")} />
                          <span className="text-xs text-muted-foreground">{s.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">{s.allocation}</td>
                      <td className={cn("px-6 py-4 text-sm font-bold", s.pnl.startsWith('+') ? "text-green-500" : "text-red-500")}>
                        {s.pnl}
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">{s.drawdown}</td>
                      <td className="px-6 py-4 text-sm text-right font-mono text-white">{s.sharpe}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};

// Re-exporting LayoutGrid as it's used in the dashboard
import { LayoutGrid as LayoutGridIcon } from 'lucide-react';
const LayoutGrid = LayoutGridIcon;
