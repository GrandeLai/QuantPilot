/**
 * 策略工坊 — 直接渲染 StrategyPanel（子标签已内置在编辑器头部）
 */
import StrategyPanel from "./StrategyPanel";

interface Props {
  onNavigate: (tab: "market" | "strategy" | "trading" | "backtest" | "options" | "portfolio" | "ai" | "system") => void;
}

export default function StrategyWorkshop({ onNavigate }: Props) {
  return <StrategyPanel onNavigate={onNavigate} />;
}
