/**
 * 下单面板 — 连接真实 paper trading API.
 *
 * 流程：
 *   1. 挂载时检查是否有 paper session，没有则自动创建默认 session
 *   2. 买/卖按钮调用 POST /paper/sessions/{id}/orders（直接撮合，无需 Redis）
 *   3. 显示成交价、手续费、成交后现金余额
 */
import { useEffect, useRef, useState } from "react";
import { MoreHorizontal, ChevronDown, RefreshCw } from "lucide-react";
import { useChartStore } from "../../store/chartStore";
import { cn } from "../../lib/utils";

const DEFAULT_SESSION = "chart-panel-default";

interface OrderResult {
  side: string;
  symbol: string;
  quantity: number;
  fill_price: number;
  commission: number;
  cash_after: number;
  portfolio_value: number;
}

export default function ChartOrderEntry() {
  const { symbol, bars } = useChartStore();
  const [qty, setQty] = useState(1);
  const [limitPrice, setLimitPrice] = useState("");
  const [priceType, setPriceType] = useState<"market" | "limit">("market");
  const [sessionReady, setSessionReady] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<OrderResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sessionCreating = useRef(false);

  // ── 确保 paper session 存在 ──────────────────────────────────────────────
  useEffect(() => {
    if (sessionCreating.current) return;
    sessionCreating.current = true;

    void (async () => {
      try {
        // 检查是否已有 session
        const listRes = await fetch("/api/paper/sessions");
        if (listRes.ok) {
          const data = (await listRes.json()) as { sessions: { session_id: string }[] };
          const exists = data.sessions.some((s) => s.session_id === DEFAULT_SESSION);
          if (exists) {
            setSessionReady(true);
            return;
          }
        }
        // 创建默认 session
        const createRes = await fetch("/api/paper/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: DEFAULT_SESSION,
            symbol,
            timeframe: "1d",
            initial_cash: 1_000_000,
          }),
        });
        if (createRes.ok || createRes.status === 409) setSessionReady(true);
      } catch {
        // 后端未启动时静默降级
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 获取当前价格 ─────────────────────────────────────────────────────────
  const getCurrentPrice = (): number => {
    if (priceType === "limit" && limitPrice) {
      const p = parseFloat(limitPrice);
      if (!isNaN(p) && p > 0) return p;
    }
    // 使用最新 bar 收盘价
    if (bars.length > 0) return bars[bars.length - 1].close;
    return 0;
  };

  // ── 提交订单 ─────────────────────────────────────────────────────────────
  const handleOrder = async (side: "buy" | "sell") => {
    setError(null);
    setResult(null);
    const price = getCurrentPrice();
    if (price <= 0) {
      setError("无法获取当前价格，请先加载行情数据");
      return;
    }
    if (!sessionReady) {
      setError("模拟盘未就绪，请稍候");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`/api/paper/sessions/${DEFAULT_SESSION}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, side, quantity: qty, price }),
      });
      const data = await res.json() as OrderResult & { detail?: string };
      if (!res.ok) {
        setError((data as { detail?: string }).detail ?? "下单失败");
      } else {
        setResult(data as OrderResult);
        setTimeout(() => setResult(null), 6000);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "网络错误");
    } finally {
      setSubmitting(false);
    }
  };

  const currentPrice = getCurrentPrice();

  return (
    <div className="flex flex-col h-1/2 bg-[#131722] p-4 text-xs">
      <div className="flex items-center justify-between mb-4 shrink-0">
        <span className="text-gray-400 font-bold uppercase tracking-wider text-[10px]">
          下单面板
        </span>
        <div className="flex items-center gap-2">
          {sessionReady ? (
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" title="模拟盘已就绪" />
          ) : (
            <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" title="初始化中…" />
          )}
          <MoreHorizontal size={14} className="text-gray-500 cursor-pointer" />
        </div>
      </div>

      <div className="space-y-3 flex-1">
        <div className="flex items-center justify-between">
          <span className="text-gray-500">标的</span>
          <span className="text-white font-mono font-bold">{symbol}</span>
        </div>

        {currentPrice > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500">当前价</span>
            <span className="text-blue-400 font-mono font-bold">${currentPrice.toFixed(2)}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <span className="text-gray-500">数量</span>
          <div className="bg-[#2a2e39] border border-gray-700 rounded px-2 py-1 w-24 text-right">
            <input
              type="number"
              min={1}
              value={qty}
              onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))}
              className="bg-transparent border-none outline-none text-white w-full text-right font-mono text-xs"
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-500">价格类型</span>
          <button
            className="flex items-center gap-1 text-white cursor-pointer hover:text-blue-400 bg-[#2a2e39] border border-gray-700 rounded px-2 py-1 w-28 justify-between"
            onClick={() => setPriceType(priceType === "market" ? "limit" : "market")}
          >
            <span>{priceType === "market" ? "市价" : "限价"}</span>
            <ChevronDown size={12} />
          </button>
        </div>

        {priceType === "limit" && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500">限价</span>
            <div className="bg-[#2a2e39] border border-gray-700 rounded px-2 py-1 w-24 text-right">
              <input
                type="text"
                placeholder="价格"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                className="bg-transparent border-none outline-none text-white w-full text-right font-mono text-xs"
              />
            </div>
          </div>
        )}

        {currentPrice > 0 && (
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-gray-500">预估金额</span>
            <span className="text-gray-400 font-mono">
              ${(currentPrice * qty).toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </span>
          </div>
        )}
      </div>

      {/* 成交结果 */}
      {result && (
        <div className="mt-2 text-[10px] bg-green-900/20 border border-green-700/30 rounded px-2 py-2 shrink-0 space-y-1">
          <div className={cn("font-bold", result.side === "buy" ? "text-green-400" : "text-red-400")}>
            {result.side === "buy" ? "✓ 买入成功" : "✓ 卖出成功"} {result.quantity}股 @${result.fill_price.toFixed(2)}
          </div>
          <div className="text-gray-400 flex justify-between">
            <span>手续费 ${result.commission.toFixed(2)}</span>
            <span>余额 ${result.cash_after.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-2 text-[10px] text-red-400 bg-red-900/20 border border-red-700/30 rounded px-2 py-1.5 shrink-0">
          {error}
        </div>
      )}

      <div className="mt-auto flex gap-2 pt-3 border-t border-gray-800 shrink-0">
        <button
          className={cn(
            "flex-1 font-bold py-2 rounded transition-colors uppercase text-[11px] flex items-center justify-center gap-1",
            submitting
              ? "bg-green-600/20 text-green-500/50 cursor-default"
              : "bg-green-600/20 text-green-500 border border-green-600/30 hover:bg-green-600/30",
          )}
          onClick={() => void handleOrder("buy")}
          disabled={submitting}
        >
          {submitting ? <RefreshCw size={11} className="animate-spin" /> : null}
          买入
        </button>
        <button
          className={cn(
            "flex-1 font-bold py-2 rounded transition-colors uppercase text-[11px] flex items-center justify-center gap-1",
            submitting
              ? "bg-red-600/20 text-red-500/50 cursor-default"
              : "bg-red-600/20 text-red-500 border border-red-600/30 hover:bg-red-600/30",
          )}
          onClick={() => void handleOrder("sell")}
          disabled={submitting}
        >
          {submitting ? <RefreshCw size={11} className="animate-spin" /> : null}
          卖出
        </button>
      </div>
    </div>
  );
}
