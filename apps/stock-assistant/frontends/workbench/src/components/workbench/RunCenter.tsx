import TradingPanel from "../TradingPanel";
import CryptoPanel from "../CryptoPanel";

export default function RunCenter() {
  return (
    <div className="space-y-6">
      <TradingPanel />
      <CryptoPanel allowedTabs={["trade", "futures", "options"]} defaultTab="trade" />
    </div>
  );
}
