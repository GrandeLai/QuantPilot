import ValidationLab from "../ValidationLab";
import CryptoResearchPanel from "../CryptoResearchPanel";
import BacktestPanel from "../BacktestPanel";

export default function ValidationCenter() {
  return (
    <div className="space-y-6">
      <ValidationLab />
      <CryptoResearchPanel />
      <BacktestPanel />
    </div>
  );
}
