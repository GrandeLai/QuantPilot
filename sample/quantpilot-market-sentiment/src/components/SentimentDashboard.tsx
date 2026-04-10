
import { useState } from 'react';
import { Header } from './Header';
import { SentimentSidebar } from './SentimentSidebar';
import { SentimentGauge } from './SentimentGauge';
import { SentimentChart } from './SentimentChart';
import { NewsFeed } from './NewsFeed';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { mockSentimentHistory, mockNews } from '@/lib/mock-data';

export function SentimentDashboard() {
  const [symbol, setSymbol] = useState('AAPL');
  const [maxItems, setMaxItems] = useState(10);

  return (
    <div className="flex flex-col h-screen bg-background text-foreground overflow-hidden">
      <Header />
      
      {/* Sub-header Tabs */}
      <div className="h-12 border-b border-border flex items-center px-4 gap-4 bg-background/50 backdrop-blur-sm">
        <Tabs defaultValue="sentiment" className="w-auto">
          <TabsList className="bg-transparent h-9 p-0 gap-2">
            <TabsTrigger 
              value="chart" 
              className="data-[state=active]:bg-muted data-[state=active]:text-foreground rounded-md px-4 h-8 text-muted-foreground"
            >
              走势图
            </TabsTrigger>
            <TabsTrigger 
              value="sentiment" 
              className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary rounded-md px-4 h-8 text-muted-foreground"
            >
              新闻情绪
            </TabsTrigger>
            <TabsTrigger 
              value="realtime" 
              className="data-[state=active]:bg-muted data-[state=active]:text-foreground rounded-md px-4 h-8 text-muted-foreground"
            >
              实时推送
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <SentimentSidebar 
          symbol={symbol} 
          setSymbol={setSymbol} 
          maxItems={maxItems} 
          setMaxItems={setMaxItems} 
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-hidden flex flex-col p-4 gap-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-auto">
            {/* Sentiment Gauge */}
            <div className="lg:col-span-1">
              <SentimentGauge score={mockSentimentHistory[mockSentimentHistory.length - 1].score} />
            </div>
            
            {/* Sentiment Distribution Chart */}
            <div className="lg:col-span-2">
              <SentimentChart data={mockSentimentHistory} />
            </div>
          </div>

          {/* News Feed */}
          <div className="flex-1 min-h-0">
            <NewsFeed news={mockNews} />
          </div>
        </main>
      </div>
    </div>
  );
}
