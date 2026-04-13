import PaperTradingPanel from "../PaperTradingPanel";
import TradingPanel from "../TradingPanel";

export default function RunCenter() {
  return (
    <div className="space-y-6">
      <PaperTradingPanel />
      <TradingPanel />
    </div>
  );
}
