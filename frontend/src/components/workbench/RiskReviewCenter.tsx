import BacktestPanel from "../BacktestPanel";
import CryptoPanel from "../CryptoPanel";
import PortfolioPanel from "../PortfolioPanel";

export default function RiskReviewCenter() {
  return (
    <div className="space-y-6">
      <PortfolioPanel />
      <BacktestPanel />
      <CryptoPanel allowedTabs={["portfolio", "orders"]} defaultTab="portfolio" />
    </div>
  );
}
