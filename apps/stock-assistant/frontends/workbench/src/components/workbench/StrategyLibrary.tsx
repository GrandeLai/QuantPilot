import StrategyWorkshop from "../StrategyWorkshop";
import type { WorkbenchTab } from "@/workbench/navigation";

interface StrategyLibraryProps {
  onNavigate?: (tab: WorkbenchTab) => void;
}

export default function StrategyLibrary({ onNavigate }: StrategyLibraryProps) {
  return (
    <StrategyWorkshop
      onNavigate={(tab) => {
        if (tab === "validation") {
          onNavigate?.("validation");
        }
      }}
    />
  );
}
