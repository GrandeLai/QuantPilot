import MarketPanel from "../MarketPanel";
import ScreenerPanel from "../ScreenerPanel";
import CryptoPanel from "../CryptoPanel";

export default function ResearchCenter() {
  return (
    <div className="space-y-6">
      <MarketPanel />
      <ScreenerPanel />
      <CryptoPanel />
    </div>
  );
}
