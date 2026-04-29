import BacktestPanel from "../BacktestPanel";
import CryptoDerivsPanel from "../CryptoDerivsPanel";
import CryptoPanel from "../CryptoPanel";
import GEXPanel from "../GEXPanel";
import PortfolioPanel from "../PortfolioPanel";
import RiskMetricsPanel from "../RiskMetricsPanel";
import SECEventsPanel from "../SECEventsPanel";
import FundamentalPanel from "../FundamentalPanel";
import TLHPanel from "../TLHPanel";
import QuantSignalsPanel from "../QuantSignalsPanel";
import EPSRevisionPanel from "../EPSRevisionPanel";
import TokenUnlockPanel from "../TokenUnlockPanel";
import DCFPanel from "../DCFPanel";
import ShortInterestPanel from "../ShortInterestPanel";
import WhaleMonitorPanel from "../WhaleMonitorPanel";
import PEADPanel from "../PEADPanel";
import MomentumPanel from "../MomentumPanel";
import SocialSentimentPanel from "../SocialSentimentPanel";
import UnusualOptionsPanel from "../UnusualOptionsPanel";
import EarningsMovePanel from "../EarningsMovePanel";
import SectorMomentumPanel from "../SectorMomentumPanel";

export default function RiskReviewCenter() {
  return (
    <div className="space-y-6">
      <GEXPanel />
      <SECEventsPanel />
      <TLHPanel />
      <FundamentalPanel />
      <QuantSignalsPanel />
      <EPSRevisionPanel />
      <PEADPanel />
      <MomentumPanel />
      <SocialSentimentPanel />
      <UnusualOptionsPanel />
      <EarningsMovePanel />
      <SectorMomentumPanel />
      <TokenUnlockPanel />
      <DCFPanel />
      <ShortInterestPanel />
      <WhaleMonitorPanel />
      <RiskMetricsPanel />
      <CryptoDerivsPanel />
      <PortfolioPanel />
      <BacktestPanel />
      <CryptoPanel allowedTabs={["portfolio", "orders"]} defaultTab="portfolio" />
    </div>
  );
}
