import CryptoPanel from "../CryptoPanel";
import MarketPanel from "../MarketPanel";
import QuantResearchPanel from "../QuantResearchPanel";
import ScreenerPanel from "../ScreenerPanel";

export default function ResearchCenter() {
  return (
    <div className="space-y-6">
      <QuantResearchPanel />
      <MarketPanel />
      <ScreenerPanel />
      <CryptoPanel allowedTabs={["market", "chart"]} defaultTab="market" />
    </div>
  );
}
