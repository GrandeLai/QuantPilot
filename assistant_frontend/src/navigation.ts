/**
 * Investment assistant navigation registry.
 */
export type AssistantTab =
  | "overview"
  | "opportunities"
  | "rebalance"
  | "risk"
  | "review";

export const ASSISTANT_TABS = [
  { key: "overview", label: "资产总览" },
  { key: "opportunities", label: "机会池" },
  { key: "rebalance", label: "调仓建议" },
  { key: "risk", label: "风险雷达" },
  { key: "review", label: "复盘与问答" },
] as const;
