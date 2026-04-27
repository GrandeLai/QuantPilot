/**
 * 测试验证工坊 — 历史回测 / 模拟交易 / 交易信号
 * 将回测结果透传到模拟交易上下文，形成完整的策略验证闭环。
 */
import { useState } from "react";
import { X } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import FeatureGuideButton from "@/components/guides/FeatureGuideButton";
import BacktestPanel, { type BacktestResult } from "./BacktestPanel";
import PaperTradingPanel from "./PaperTradingPanel";
import SignalsPanel from "./SignalsPanel";

type Sub = "backtest" | "paper" | "signals";

// ── 回测参考横幅 ──────────────────────────────────────────────────────────────

function BacktestRefCard({
  result,
  onDismiss,
}: {
  result: BacktestResult;
  onDismiss: () => void;
}) {
  const m = result.metrics;
  const pct = (v: number) => `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;

  return (
    <div className="flex items-center gap-2 px-4 py-2 mb-3 bg-blue-950/30 border border-blue-700/25 rounded-xl text-xs">
      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
      <span className="text-[#8b949e] font-medium shrink-0">上次回测参考</span>
      <span className="font-mono text-white">{result.symbol}</span>
      <span className="text-[#434651]">·</span>
      <span className="text-[#c9d1d9]">{result.timeframe}</span>
      <span className="text-[#434651]">·</span>
      <span className={`font-mono font-bold ${m.total_return >= 0 ? "text-green-400" : "text-red-400"}`}>
        总收益 {pct(m.total_return)}
      </span>
      <span className="text-[#434651]">·</span>
      <span className="text-[#c9d1d9]">
        胜率 <span className="font-mono text-white">{(m.win_rate * 100).toFixed(0)}%</span>
      </span>
      <span className="text-[#434651]">·</span>
      <span className="text-[#c9d1d9]">
        Sharpe <span className="font-mono text-white">{m.sharpe_ratio.toFixed(2)}</span>
      </span>
      <span className="text-[#434651]">·</span>
      <span className="text-[#c9d1d9]">
        最大回撤 <span className="font-mono text-red-400">{pct(m.max_drawdown)}</span>
      </span>
      <button
        onClick={onDismiss}
        className="ml-auto p-0.5 text-[#8b949e] hover:text-white transition-colors shrink-0"
        aria-label="关闭参考"
      >
        <X size={12} />
      </button>
    </div>
  );
}

// ── 主组件 ────────────────────────────────────────────────────────────────────

export default function ValidationLab() {
  const [sub, setSub] = useState<Sub>("backtest");
  const [lastResult, setLastResult] = useState<BacktestResult | null>(null);
  const [showRef, setShowRef] = useState(false);

  const handleGoToPaper = () => {
    setSub("paper");
    setShowRef(true);
  };

  return (
    <div className="relative space-y-4">
      {/* Sub-tab navigation */}
      <div className="flex justify-center">
        <Tabs value={sub} onValueChange={(v) => setSub(v as Sub)} className="w-fit">
          <TabsList className="bg-card border border-border h-10 p-1">
            <TabsTrigger value="backtest" className="px-8">历史回测</TabsTrigger>
            <TabsTrigger value="paper" className="px-8">模拟交易</TabsTrigger>
            <TabsTrigger value="signals" className="px-8">交易信号</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content panels */}
      {sub === "backtest" && (
        <BacktestPanel
          onResult={(r) => setLastResult(r)}
          onGoToPaper={handleGoToPaper}
        />
      )}
      {sub === "paper" && (
        <div>
          {lastResult && showRef && (
            <BacktestRefCard result={lastResult} onDismiss={() => setShowRef(false)} />
          )}
          <PaperTradingPanel />
        </div>
      )}
      {sub === "signals" && <SignalsPanel />}

      {sub === "signals" && <FeatureGuideButton guideKey="trading.signals" />}
    </div>
  );
}
