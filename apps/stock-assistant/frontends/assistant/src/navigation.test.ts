import test from "node:test";
import assert from "node:assert/strict";

import { ASSISTANT_TABS } from "./navigation.ts";

test("assistant labels stay aligned with the decision flow", () => {
  assert.deepEqual(
    ASSISTANT_TABS.map((tab) => tab.label),
    ["资产总览", "机会池", "调仓建议", "风险雷达", "复盘与问答"],
  );
});
