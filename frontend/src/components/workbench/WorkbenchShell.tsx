import type { ReactNode } from "react";

import ResearchCenter from "./ResearchCenter";
import RiskReviewCenter from "./RiskReviewCenter";
import RunCenter from "./RunCenter";
import StrategyLibrary from "./StrategyLibrary";
import ValidationCenter from "./ValidationCenter";
import type { WorkbenchTab } from "@/workbench/navigation";

interface WorkbenchShellProps {
  activeTab: WorkbenchTab;
}

const SECTION_COMPONENTS: Record<WorkbenchTab, ReactNode> = {
  research: <ResearchCenter />,
  strategy: <StrategyLibrary />,
  validation: <ValidationCenter />,
  run: <RunCenter />,
  risk_review: <RiskReviewCenter />,
};

export default function WorkbenchShell({ activeTab }: WorkbenchShellProps) {
  return SECTION_COMPONENTS[activeTab];
}
