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
import { WilliamsRPanel } from "../WilliamsRPanel";
import { CCIPanel } from "../CCIPanel";
import { ATRPanel } from "../ATRPanel";
import { ROCPanel } from "../ROCPanel";
import { SARPanel } from "../SARPanel";
import { VWAPPanel } from "../VWAPPanel";
import { KeltnerPanel } from "../KeltnerPanel";
import { ForceIndexPanel } from "../ForceIndexPanel";
import { TRIXPanel } from "../TRIXPanel";
import { AroonPanel } from "../AroonPanel";
import { UltimateOscPanel } from "../UltimateOscPanel";
import { SupertrendPanel } from "../SupertrendPanel";
import { DPOPanel } from "../DPOPanel";
import { TSIPanel } from "../TSIPanel";
import { DonchianPanel } from "../DonchianPanel";
import { IchimokuPanel } from "../IchimokuPanel";
import { KSTPanel } from "../KSTPanel";
import { ChaikinOscPanel } from "../ChaikinOscPanel";
import { ElderRayPanel } from "../ElderRayPanel";
import { VortexPanel } from "../VortexPanel";
import { PVTPanel } from "../PVTPanel";
import { CMOPanel } from "../CMOPanel";
import { PPOPanel } from "../PPOPanel";
import { MassIndexPanel } from "../MassIndexPanel";
import { KVOPanel } from "../KVOPanel";
import { HMAPanel } from "../HMAPanel";
import { KAMAPanel } from "../KAMAPanel";
import { STCPanel } from "../STCPanel";
import { CKSPanel } from "../CKSPanel";
import { PriceOscPanel } from "../PriceOscPanel";
import { ChaikinVolPanel } from "../ChaikinVolPanel";
import { DEMAPanel } from "../DEMAPanel";
import { TEMAPanel } from "../TEMAPanel";
import { AlligatorPanel } from "../AlligatorPanel";

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
      <WilliamsRPanel />
      <CCIPanel />
      <ATRPanel />
      <ROCPanel />
      <SARPanel />
      <VWAPPanel />
      <KeltnerPanel />
      <ForceIndexPanel />
      <TRIXPanel />
      <AroonPanel />
      <UltimateOscPanel />
      <SupertrendPanel />
      <DPOPanel />
      <TSIPanel />
      <DonchianPanel />
      <IchimokuPanel />
      <KSTPanel />
      <ChaikinOscPanel />
      <ElderRayPanel />
      <VortexPanel />
      <PVTPanel />
      <CMOPanel />
      <PPOPanel />
      <MassIndexPanel />
      <KVOPanel />
      <HMAPanel />
      <KAMAPanel />
      <STCPanel />
      <CKSPanel />
      <PriceOscPanel />
      <ChaikinVolPanel />
      <DEMAPanel />
      <TEMAPanel />
      <AlligatorPanel />
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
