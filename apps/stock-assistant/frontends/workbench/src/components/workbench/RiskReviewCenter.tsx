import BacktestPanel from "../BacktestPanel";
import CryptoDerivsPanel from "../CryptoDerivsPanel";
import CryptoPanel from "../CryptoPanel";
import GEXPanel from "../GEXPanel";
import PortfolioPanel from "../PortfolioPanel";
import RiskMetricsPanel from "../RiskMetricsPanel";
import SECEventsPanel from "../SECEventsPanel";
import TLHPanel from "../TLHPanel";

export default function RiskReviewCenter() {
  return (
    <div className="space-y-6">
      <GEXPanel />
      <SECEventsPanel />
      <TLHPanel />
      <RiskMetricsPanel />
      <CryptoDerivsPanel />
      <PortfolioPanel />
      <BacktestPanel />
      <CryptoPanel allowedTabs={["portfolio", "orders"]} defaultTab="portfolio" />
    </div>
  );
}
