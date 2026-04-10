
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { NewsItem } from '@/lib/mock-data';
import { MessageSquare, Zap, ExternalLink } from 'lucide-react';

interface NewsFeedProps {
  news: NewsItem[];
}

export function NewsFeed({ news }: NewsFeedProps) {
  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish':
        return <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 hover:bg-emerald-500/20">看涨</Badge>;
      case 'bearish':
        return <Badge className="bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500/20">看跌</Badge>;
      default:
        return <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20 hover:bg-yellow-500/20">中性</Badge>;
    }
  };

  const getImpactBadge = (impact: string) => {
    switch (impact) {
      case 'high':
        return <div className="flex items-center gap-1 text-orange-500 font-bold text-[10px] uppercase"><Zap size={10} /> 高影响</div>;
      case 'medium':
        return <div className="flex items-center gap-1 text-blue-500 font-bold text-[10px] uppercase">中影响</div>;
      default:
        return <div className="flex items-center gap-1 text-muted-foreground font-bold text-[10px] uppercase">低影响</div>;
    }
  };

  return (
    <Card className="bg-muted/10 border-border h-full flex flex-col">
      <CardHeader className="pb-2 flex flex-row items-center justify-between shrink-0">
        <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <MessageSquare size={14} className="text-primary" />
          最新新闻情绪分析
        </CardTitle>
        <div className="text-[10px] text-muted-foreground">共 {news.length} 条分析结果</div>
      </CardHeader>
      <CardContent className="p-0 flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <Table>
            <TableHeader className="bg-muted/30 sticky top-0 z-10">
              <TableRow className="hover:bg-transparent border-border">
                <TableHead className="w-[100px] text-[10px] font-bold uppercase">情绪</TableHead>
                <TableHead className="text-[10px] font-bold uppercase">新闻标题 / 摘要</TableHead>
                <TableHead className="w-[120px] text-[10px] font-bold uppercase">来源 / 时间</TableHead>
                <TableHead className="w-[100px] text-[10px] font-bold uppercase">影响程度</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {news.map((item) => (
                <TableRow key={item.id} className="border-border hover:bg-muted/20 group transition-colors">
                  <TableCell className="py-4">
                    {getSentimentBadge(item.sentiment)}
                  </TableCell>
                  <TableCell className="py-4">
                    <div className="space-y-1">
                      <div className="font-semibold text-sm group-hover:text-primary transition-colors cursor-pointer">{item.title}</div>
                      <div className="text-xs text-muted-foreground line-clamp-1">{item.summary}</div>
                    </div>
                  </TableCell>
                  <TableCell className="py-4">
                    <div className="text-[11px] font-medium">{item.source}</div>
                    <div className="text-[10px] text-muted-foreground">{item.time}</div>
                  </TableCell>
                  <TableCell className="py-4">
                    {getImpactBadge(item.impact)}
                  </TableCell>
                  <TableCell className="py-4">
                    <button className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                      <ExternalLink size={14} />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
