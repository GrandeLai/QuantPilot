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
import AnalystConsensusPanel from "../AnalystConsensusPanel";
import EarningsQualityPanel from "../EarningsQualityPanel";
import InsiderTradingPanel from "../InsiderTradingPanel";
import SmartMoneyPanel from "../SmartMoneyPanel";
import IndexRebalancePanel from "../IndexRebalancePanel";
import IVRankPanel from "../IVRankPanel";
import EarningsCalendarPanel from "../EarningsCalendarPanel";
import PutCallRatioPanel from "../PutCallRatioPanel";
import MacroDashboardPanel from "../MacroDashboardPanel";
import DividendAnalysisPanel from "../DividendAnalysisPanel";
import MaxPainPanel from "../MaxPainPanel";
import TechnicalScorePanel from "../TechnicalScorePanel";
import BetaCorrelationPanel from "../BetaCorrelationPanel";
import SeasonalityPanel from "../SeasonalityPanel";
import RelativeStrengthPanel from "../RelativeStrengthPanel";
import ReversalSignalPanel from "../ReversalSignalPanel";
import ADXTrendPanel from "../ADXTrendPanel";
import MAAlignmentPanel from "../MAAlignmentPanel";
import MACDPanel from "../MACDPanel";
import BollingerPanel from "../BollingerPanel";
import RSISignalPanel from "../RSISignalPanel";
import StochasticPanel from "../StochasticPanel";
import { OBVPanel } from "../OBVPanel";
import { MFIPanel } from "../MFIPanel";
import { CMFPanel } from "../CMFPanel";

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
      <AnalystConsensusPanel />
      <EarningsQualityPanel />
      <InsiderTradingPanel />
      <SmartMoneyPanel />
      <IndexRebalancePanel />
      <IVRankPanel />
      <EarningsCalendarPanel />
      <PutCallRatioPanel />
      <MacroDashboardPanel />
      <DividendAnalysisPanel />
      <MaxPainPanel />
      <TechnicalScorePanel />
      <BetaCorrelationPanel />
      <SeasonalityPanel />
      <RelativeStrengthPanel />
      <ReversalSignalPanel />
      <ADXTrendPanel />
      <MAAlignmentPanel />
      <MACDPanel />
      <BollingerPanel />
      <RSISignalPanel />
      <StochasticPanel />
      <OBVPanel />
      <MFIPanel />
      <CMFPanel />
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
