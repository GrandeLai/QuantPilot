import { lazy } from "react";
import type { WorkbenchTab } from "@/workbench/navigation";

interface WorkbenchShellProps {
  activeTab: WorkbenchTab;
  onNavigate?: (tab: WorkbenchTab) => void;
}

const ResearchCenter = lazy(() => import("./ResearchCenter"));
const StrategyLibrary = lazy(() => import("./StrategyLibrary"));
const ValidationCenter = lazy(() => import("./ValidationCenter"));
const RunCenter = lazy(() => import("./RunCenter"));
const RiskReviewCenter = lazy(() => import("./RiskReviewCenter"));

const SECTION_COMPONENTS = {
  research: ResearchCenter,
  strategy: StrategyLibrary,
  validation: ValidationCenter,
  run: RunCenter,
  risk_review: RiskReviewCenter,
} as const satisfies Record<WorkbenchTab, React.ComponentType<{ onNavigate?: (tab: WorkbenchTab) => void }>>;

export default function WorkbenchShell({ activeTab, onNavigate }: WorkbenchShellProps) {
  const ActiveSection = SECTION_COMPONENTS[activeTab];

  return (
    <ActiveSection onNavigate={activeTab === "strategy" ? onNavigate : undefined} />
  );
}
