import test from "node:test";
import assert from "node:assert/strict";

import { WORKBENCH_TABS } from "./navigation.ts";

test("workbench tabs follow the profit workflow order", () => {
  assert.deepEqual(
    WORKBENCH_TABS.map((tab) => tab.key),
    ["research", "strategy", "validation", "run", "risk_review"],
  );
});
