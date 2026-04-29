import {
  Briefcase,
  ListTree,
  Scale,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import type { ComponentType } from "react";

import { OpportunityPool } from "./components/OpportunityPool";
import { PortfolioOverview } from "./components/PortfolioOverview";
import { RebalanceSuggestions } from "./components/RebalanceSuggestions";
import { ReviewAsk } from "./components/ReviewAsk";
import { RiskRadar } from "./components/RiskRadar";
import type { AssistantTab } from "./navigation";
import { ASSISTANT_TABS } from "./navigation";
import { cn } from "./lib/utils";
import { useAdvisorStore } from "./store/advisorStore";

const TAB_ICONS: Record<AssistantTab, ComponentType<{ size?: number }>> = {
  overview: Briefcase,
  opportunities: ListTree,
  rebalance: Scale,
  risk: ShieldAlert,
  review: Sparkles,
};

function renderView(tab: AssistantTab) {
  switch (tab) {
    case "overview":
      return <PortfolioOverview />;
    case "opportunities":
      return <OpportunityPool />;
    case "rebalance":
      return <RebalanceSuggestions />;
    case "risk":
      return <RiskRadar />;
    case "review":
      return <ReviewAsk />;
    default: {
      const exhaustiveCheck: never = tab;
      return exhaustiveCheck;
    }
  }
}

/**
 * Investment assistant shell — dark theme aligned with workbench.
 */
export default function App() {
  const activeTab = useAdvisorStore((state) => state.activeTab);
  const setActiveTab = useAdvisorStore((state) => state.setActiveTab);

  return (
    <main className="min-h-screen bg-[#0E1014] text-white">
      <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
        <header className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#00C087]/10 border border-[#00C087]/30 rounded-lg">
              <Sparkles size={20} className="text-[#00C087]" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Investment Assistant</h1>
              <p className="text-[#8E9299] text-sm mt-0.5">
                面向投资决策流的轻量助手外壳
              </p>
            </div>
          </div>
        </header>

        <nav aria-label="Investment assistant views">
          <ul className="flex flex-wrap gap-2 list-none p-0 m-0">
            {ASSISTANT_TABS.map((tab) => {
              const Icon = TAB_ICONS[tab.key];
              const isActive = tab.key === activeTab;
              return (
                <li key={tab.key}>
                  <button
                    type="button"
                    aria-current={isActive ? "page" : undefined}
                    onClick={() => setActiveTab(tab.key)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 text-sm rounded-lg border transition-colors",
                      isActive
                        ? "bg-[#00C087] border-[#00C087] text-black font-bold"
                        : "bg-[#151619] border-[#2A2D35] text-[#8E9299] hover:text-white hover:border-[#00C087]/50",
                    )}
                  >
                    <Icon size={14} />
                    {tab.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="bg-[#0E1014] border border-[#2A2D35] rounded-xl p-6 min-h-[280px]">
          {renderView(activeTab)}
        </div>
      </div>
    </main>
  );
}
