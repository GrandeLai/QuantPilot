/**
 * 底部面板 — 新闻资讯 + 持仓历史.
 */
import { useEffect, useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { cn } from "../../lib/utils";

interface NewsItem {
  id: number;
  title: string;
  timestamp: string;
  sentiment?: "positive" | "negative" | "neutral";
}

interface Position {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  qty: number;
  entry_price: number;
  exit_price: number | null;
  pnl: number;
  created_at: string;
}

const MOCK_NEWS: NewsItem[] = [
  { id: 1, title: "美联储维持利率不变，市场反应平稳", timestamp: "10:32 AM", sentiment: "neutral" },
  { id: 2, title: "科技股领涨，纳斯达克指数创历史新高", timestamp: "09:15 AM", sentiment: "positive" },
  { id: 3, title: "原油价格回调，能源板块承压", timestamp: "08:50 AM", sentiment: "negative" },
  { id: 4, title: "苹果公司发布新产品，股价盘前上涨 3%", timestamp: "08:20 AM", sentiment: "positive" },
  { id: 5, title: "中国经济数据好于预期，亚太市场全线上涨", timestamp: "07:05 AM", sentiment: "positive" },
];

export default function ChartBottomPanels() {
  const [news, setNews] = useState<NewsItem[]>(MOCK_NEWS);
  const [positions, setPositions] = useState<Position[]>([]);

  useEffect(() => {
    // Try to fetch real news sentiment
    const fetchNews = async () => {
      try {
        const res = await fetch("/api/news/headlines?limit=10");
        if (res.ok) {
          const data = (await res.json()) as { headlines?: NewsItem[] };
          if (data.headlines && data.headlines.length > 0) {
            setNews(data.headlines);
          }
        }
      } catch {
        // use mock data
      }
    };
    // Try to fetch paper positions
    const fetchPositions = async () => {
      try {
        const sessRes = await fetch("/api/paper/sessions");
        if (sessRes.ok) {
          const sessData = (await sessRes.json()) as { sessions?: { id: string }[] };
          const sessions = sessData.sessions ?? [];
          if (sessions.length > 0) {
            const sid = sessions[0].id;
            const posRes = await fetch(`/api/paper/sessions/${sid}/orders`);
            if (posRes.ok) {
              const posData = (await posRes.json()) as { orders?: Position[] };
              setPositions(posData.orders ?? []);
            }
          }
        }
      } catch {
        // no sessions yet
      }
    };

    void fetchNews();
    void fetchPositions();
  }, []);

  return (
    <div className="h-64 border-t border-gray-800 bg-[#131722] flex min-h-0 shrink-0">
      {/* 新闻资讯 */}
      <div className="w-1/4 border-r border-gray-800 flex flex-col min-h-0">
        <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between shrink-0">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            新闻资讯
          </span>
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
      </div>

      {/* 持仓历史 */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between shrink-0">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            持仓记录
          </span>
          <MoreHorizontal size={14} className="text-gray-500" />
        </div>
        <div className="flex-1 overflow-x-auto overflow-y-auto custom-scrollbar">
          {positions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-[11px] text-gray-600">
              暂无持仓记录 — 在模拟盘中发起交易后显示
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="text-gray-500 border-b border-gray-800 sticky top-0 bg-[#131722]">
                <tr>
                  <th className="px-3 py-2 font-medium">标的</th>
                  <th className="px-3 py-2 font-medium">方向</th>
                  <th className="px-3 py-2 font-medium">数量</th>
                  <th className="px-3 py-2 font-medium">开仓价</th>
                  <th className="px-3 py-2 font-medium">平仓价</th>
                  <th className="px-3 py-2 font-medium">盈亏</th>
                  <th className="px-3 py-2 font-medium">时间</th>
                </tr>
              </thead>
              <tbody className="text-gray-300">
                {positions.map((pos) => (
                  <tr
                    key={pos.id}
                    className="border-b border-gray-800/30 hover:bg-[#2a2e39] transition-colors"
                  >
                    <td className="px-3 py-2 font-bold">{pos.symbol}</td>
                    <td
                      className={cn(
                        "px-3 py-2 font-bold",
                        pos.side === "BUY" ? "text-green-500" : "text-red-500",
                      )}
                    >
                      {pos.side === "BUY" ? "买" : "卖"}
                    </td>
                    <td className="px-3 py-2 font-mono">{pos.qty}</td>
                    <td className="px-3 py-2 font-mono">{pos.entry_price.toFixed(2)}</td>
                    <td className="px-3 py-2 font-mono">
                      {pos.exit_price != null ? pos.exit_price.toFixed(2) : "—"}
                    </td>
                    <td
                      className={cn(
                        "px-3 py-2 font-mono font-bold",
                        pos.pnl >= 0 ? "text-green-500" : "text-red-500",
                      )}
                    >
                      {pos.pnl >= 0 ? "+" : ""}
                      {pos.pnl.toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-gray-500 text-[10px]">
                      {new Date(pos.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
