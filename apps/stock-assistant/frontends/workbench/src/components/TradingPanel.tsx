/**
 * 交易面板 — 合并：模拟盘 / 信号
 */
import { useState } from "react";
import FeatureGuideButton from "@/components/guides/FeatureGuideButton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PaperTradingPanel from "./PaperTradingPanel";
import SignalsPanel from "./SignalsPanel";

type Sub = "paper" | "signals";

export default function TradingPanel() {
  const [sub, setSub] = useState<Sub>("paper");

  return (
    <div className="relative space-y-6">
      <div className="flex justify-center">
        <Tabs value={sub} onValueChange={(v) => setSub(v as Sub)} className="w-fit">
          <TabsList className="bg-card border border-border h-10 p-1">
            <TabsTrigger value="paper" className="px-8">模拟交易</TabsTrigger>
            <TabsTrigger value="signals" className="px-8">交易信号</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      {sub === "paper" && <PaperTradingPanel />}
      {sub === "signals" && <SignalsPanel />}
      {sub === "signals" ? <FeatureGuideButton guideKey="trading.signals" /> : null}
    </div>
  );
}
