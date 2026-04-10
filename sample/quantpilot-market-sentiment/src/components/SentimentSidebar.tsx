
import { Settings2, Search, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface SentimentSidebarProps {
  symbol: string;
  setSymbol: (s: string) => void;
  maxItems: number;
  setMaxItems: (n: number) => void;
}

export function SentimentSidebar({ symbol, setSymbol, maxItems, setMaxItems }: SentimentSidebarProps) {
  return (
    <aside className="w-72 border-r border-border bg-muted/20 p-4 flex flex-col gap-6 shrink-0">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Settings2 size={16} className="text-primary" />
          情绪分析配置
        </h2>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6">
                <Info size={14} className="text-muted-foreground" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-xs">配置情绪分析的参数，包括标的代码和分析样本数量。</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="symbol" className="text-xs text-muted-foreground uppercase tracking-wider font-bold">标的代码</Label>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              id="symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="pl-9 bg-background/50 border-border"
              placeholder="例如: AAPL"
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-muted-foreground uppercase tracking-wider font-bold">分析条数</Label>
            <span className="text-xs font-mono bg-primary/10 text-primary px-1.5 py-0.5 rounded">{maxItems}</span>
          </div>
          <Slider
            value={[maxItems]}
            onValueChange={(val) => setMaxItems(val[0])}
            max={100}
            min={5}
            step={5}
            className="py-2"
          />
          <div className="flex justify-between text-[10px] text-muted-foreground px-1">
            <span>5</span>
            <span>50</span>
            <span>100</span>
          </div>
        </div>
      </div>

      <div className="mt-auto space-y-3">
        <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold shadow-lg shadow-primary/20">
          获取情绪分析
        </Button>
        <p className="text-[10px] text-center text-muted-foreground italic">
          数据由 QuantPilot AI 实时处理
        </p>
      </div>
    </aside>
  );
}
