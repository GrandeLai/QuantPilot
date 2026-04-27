import { OpportunityPool } from "./components/OpportunityPool";
import { PortfolioOverview } from "./components/PortfolioOverview";
import { RebalanceSuggestions } from "./components/RebalanceSuggestions";
import { ReviewAsk } from "./components/ReviewAsk";
import { RiskRadar } from "./components/RiskRadar";
import type { AssistantTab } from "./navigation";
import { ASSISTANT_TABS } from "./navigation";
import { useAdvisorStore } from "./store/advisorStore";

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
 * Minimal investment assistant shell with five decision views.
 */
export default function App() {
  const activeTab = useAdvisorStore((state) => state.activeTab);
  const setActiveTab = useAdvisorStore((state) => state.setActiveTab);

  return (
    <main style={{ margin: "0 auto", maxWidth: "960px", padding: "32px 24px" }}>
      <header>
        <h1>Investment Assistant</h1>
        <p>面向投资决策流的轻量助手外壳。</p>
      </header>

      <nav aria-label="Investment assistant views">
        <ul
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "12px",
            listStyle: "none",
            margin: "24px 0",
            padding: 0,
          }}
        >
        {ASSISTANT_TABS.map((tab) => (
            <li key={tab.key}>
              <button
                type="button"
                aria-current={tab.key === activeTab ? "page" : undefined}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  backgroundColor: tab.key === activeTab ? "#111827" : "#ffffff",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  color: tab.key === activeTab ? "#ffffff" : "#111827",
                  cursor: "pointer",
                  padding: "10px 14px",
                }}
              >
                {tab.label}
              </button>
            </li>
        ))}
        </ul>
      </nav>

      <div
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          minHeight: "220px",
          padding: "24px",
        }}
      >
        {renderView(activeTab)}
      </div>
    </main>
  );
}
