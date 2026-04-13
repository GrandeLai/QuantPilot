import ValidationLab from "../ValidationLab";
import CryptoPanel from "../CryptoPanel";
import CryptoResearchPanel from "../CryptoResearchPanel";

export default function ValidationCenter() {
  return (
    <div className="space-y-6">
      <ValidationLab />
      <CryptoResearchPanel />
      <CryptoPanel allowedTabs={["backtest"]} defaultTab="backtest" />
    </div>
  );
}
