
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { SentimentData } from '@/lib/mock-data';

interface SentimentChartProps {
  data: SentimentData[];
}

export function SentimentChart({ data }: SentimentChartProps) {
  return (
    <Card className="bg-muted/10 border-border h-full">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">情绪趋势分析 (24H)</CardTitle>
        <div className="flex gap-4 text-[10px] font-bold uppercase">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#26a69a]" />
            <span className="text-[#26a69a]">看涨</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#ef5350]" />
            <span className="text-[#ef5350]">看跌</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="h-[220px] pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorBullish" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#26a69a" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#26a69a" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorBearish" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef5350" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef5350" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="timestamp" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} 
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }} 
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e222d', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
              itemStyle={{ fontSize: '12px' }}
            />
            <Area 
              type="monotone" 
              dataKey="bullish" 
              stroke="#26a69a" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorBullish)" 
            />
            <Area 
              type="monotone" 
              dataKey="bearish" 
              stroke="#ef5350" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorBearish)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
