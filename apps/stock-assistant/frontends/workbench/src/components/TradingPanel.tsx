/**
 * 交易面板 — 合并：交易执行 / 信号
 */
import { useState } from "react";
import FeatureGuideButton from "@/components/guides/FeatureGuideButton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import BrokerTradingPanel from "./BrokerTradingPanel";
import SignalsPanel from "./SignalsPanel";

type Sub = "execution" | "signals";

export default function TradingPanel() {
  const [sub, setSub] = useState<Sub>("execution");

  return (
    <div className="relative space-y-6">
      <div className="flex justify-center">
        <Tabs value={sub} onValueChange={(v) => setSub(v as Sub)} className="w-fit">
          <TabsList className="bg-card border border-border h-10 p-1">
            <TabsTrigger value="execution" className="px-8">交易执行</TabsTrigger>
            <TabsTrigger value="signals" className="px-8">交易信号</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      {sub === "execution" && <BrokerTradingPanel />}
      {sub === "signals" && <SignalsPanel />}
      {sub === "signals" ? <FeatureGuideButton guideKey="trading.signals" /> : null}
    </div>
  );
}
