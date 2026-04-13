import type { WorkbenchTab } from "./navigation.ts";

export const WORKBENCH_SECTIONS: Record<WorkbenchTab, string[]> = {
  research: ["market", "screener", "crypto"],
  strategy: ["strategy_workshop"],
  validation: ["validation_lab"],
  run: ["trading"],
  risk_review: ["portfolio", "backtest"],
};

export const CRYPTO_WORKBENCH_SECTIONS: Record<
  "research" | "validation" | "run" | "risk_review",
  string[]
> = {
  research: ["market", "chart"],
  validation: ["backtest"],
  run: ["trade", "futures", "options"],
  risk_review: ["portfolio", "orders"],
};
