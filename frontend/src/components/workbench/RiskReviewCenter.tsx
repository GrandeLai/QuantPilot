import BacktestPanel from "../BacktestPanel";
import PortfolioPanel from "../PortfolioPanel";

export default function RiskReviewCenter() {
  return (
    <div className="space-y-6">
      <PortfolioPanel />
      <BacktestPanel />
    </div>
  );
}
