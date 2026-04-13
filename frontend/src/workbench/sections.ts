import type { WorkbenchTab } from "./navigation.ts";

export const WORKBENCH_SECTIONS: Record<WorkbenchTab, string[]> = {
  research: ["market", "screener", "crypto"],
  strategy: ["strategy_workshop"],
  validation: ["validation_lab"],
  run: ["paper_trading", "trading"],
  risk_review: ["portfolio", "backtest"],
};
