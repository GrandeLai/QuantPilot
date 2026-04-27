/**
 * 底部面板 — 新闻资讯 + 持仓历史.
 */
import { useEffect, useState } from "react";
import { MoreHorizontal } from "lucide-react";
import FeatureGuideButton from "@/components/guides/FeatureGuideButton";
import { cn } from "../../lib/utils";
import { useChartStore } from "../../store/chartStore";

interface NewsItem {
  id: string | number;
  title: string;
  timestamp: string;
  sentiment?: "positive" | "negative" | "neutral";
}

interface Position {
  execution_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  executed_at: string;
  name: string;
}

const MOCK_NEWS: NewsItem[] = [
  { id: 1, title: "美联储维持利率不变，市场反应平稳", timestamp: "10:32 AM", sentiment: "neutral" },
  { id: 2, title: "科技股领涨，纳斯达克指数创历史新高", timestamp: "09:15 AM", sentiment: "positive" },
  { id: 3, title: "原油价格回调，能源板块承压", timestamp: "08:50 AM", sentiment: "negative" },
  { id: 4, title: "苹果公司发布新产品，股价盘前上涨 3%", timestamp: "08:20 AM", sentiment: "positive" },
  { id: 5, title: "中国经济数据好于预期，亚太市场全线上涨", timestamp: "07:05 AM", sentiment: "positive" },
];

export default function ChartBottomPanels() {
  const { symbol } = useChartStore();
  const [news, setNews] = useState<NewsItem[]>(MOCK_NEWS);
  const [positions, setPositions] = useState<Position[]>([]);
  const [usingMockNews, setUsingMockNews] = useState(true);

  useEffect(() => {
    // Try to fetch real news sentiment
    const fetchNews = async () => {
      try {
        const res = await fetch(`/api/sentiment/news?symbol=${encodeURIComponent(symbol)}&max_items=10`);
        if (res.ok) {
          const data = (await res.json()) as {
            items?: Array<{
              id: string;
              title: string;
              published: string;
              sentiment?: { label?: string };
            }>;
          };
          if (data.items && data.items.length > 0) {
            setNews(
              data.items.map((item) => ({
                id: item.id,
                title: item.title,
                timestamp: new Date(item.published).toLocaleString("zh-CN", {
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                }),
                sentiment:
                  item.sentiment?.label === "positive"
                    ? "positive"
                    : item.sentiment?.label === "negative"
                      ? "negative"
                      : "neutral",
              })),
            );
            setUsingMockNews(false);
          } else {
            setUsingMockNews(true);
          }
        }
      } catch {
        setUsingMockNews(true);
      }
    };

    // Try to fetch recent executions from the unified trading API
    const fetchPositions = async () => {
      try {
        const posRes = await fetch("/api/trading/executions/today?page=1&page_size=20");
        if (posRes.ok) {
          const posData = (await posRes.json()) as { items?: Position[] };
          setPositions(posData.items ?? []);
        }
      } catch {
        // ignore
      }
    };

    void fetchNews();
    void fetchPositions();
  }, [symbol]);

  return (
    <div className="h-64 border-t border-gray-800 bg-[#131722] flex min-h-0 shrink-0">
      {/* 新闻资讯 */}
      <div className="relative w-1/4 border-r border-gray-800 flex flex-col min-h-0">
        <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              新闻资讯
            </span>
            <span className="rounded-full border border-gray-800 bg-[#161b22] px-1.5 py-0.5 text-[9px] text-gray-500">
              {symbol}
            </span>
            {usingMockNews && (
              <span className="rounded-full border border-amber-700/30 bg-amber-500/10 px-1.5 py-0.5 text-[9px] text-amber-400">
                Mock
              </span>
            )}
          </div>
          <MoreHorizontal size={14} className="text-gray-500" />
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {news.map((item) => (
            <div
              key={item.id}
              className="px-3 py-2.5 border-b border-gray-800/50 hover:bg-[#2a2e39] cursor-pointer group"
            >
              <p className="text-xs text-gray-300 group-hover:text-white line-clamp-2 mb-1 leading-tight">
                {item.title}
              </p>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-gray-500">{item.timestamp}</span>
                {item.sentiment && (
                  <span
                    className={cn(
                      "text-[9px] font-bold uppercase px-1 rounded",
                      item.sentiment === "positive" && "text-green-500 bg-green-900/20",
                      item.sentiment === "negative" && "text-red-500 bg-red-900/20",
                      item.sentiment === "neutral" && "text-gray-400 bg-gray-800",
                    )}
                  >
                    {item.sentiment === "positive" ? "利好" : item.sentiment === "negative" ? "利空" : "中性"}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
        <FeatureGuideButton guideKey="market.chart.news" className="bottom-3 right-3" />
      </div>

      {/* 持仓历史 */}
      <div className="relative flex-1 flex flex-col min-h-0">
        <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between shrink-0">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            持仓记录
          </span>
          <MoreHorizontal size={14} className="text-gray-500" />
        </div>
        <div className="flex-1 overflow-x-auto overflow-y-auto custom-scrollbar">
          {positions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-[11px] text-gray-600">
              暂无成交记录 — 在模拟交易中发起订单后显示
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#131722]">
                <tr>
                  <th className="px-3 py-2 font-medium">标的</th>
                  <th className="px-3 py-2 font-medium">方向</th>
                  <th className="px-3 py-2 font-medium">数量</th>
                  <th className="px-3 py-2 font-medium">成交价</th>
                  <th className="px-3 py-2 font-medium">时间</th>
                </tr>
              </thead>
              <tbody className="text-gray-300">
                {positions.map((pos) => (
                  <tr
                    key={pos.execution_id}
                    className="border-b border-gray-800/30 hover:bg-[#2a2e39] transition-colors"
                  >
                    <td className="px-3 py-2 font-bold">
                      <div>{pos.symbol}</div>
                      <div className="text-[10px] text-gray-500">{pos.name}</div>
                    </td>
                    <td
                      className={cn(
                        "px-3 py-2 font-bold",
                        pos.side === "buy" ? "text-green-500" : "text-red-500",
                      )}
                    >
                      {pos.side === "buy" ? "买" : "卖"}
                    </td>
                    <td className="px-3 py-2 font-mono">{pos.quantity}</td>
                    <td className="px-3 py-2 font-mono">{pos.price.toFixed(2)}</td>
                    <td className="px-3 py-2 text-gray-500 text-[10px]">
                      {new Date(pos.executed_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <FeatureGuideButton guideKey="market.chart.positions" className="bottom-3 right-3" />
      </div>
    </div>
  );
}
