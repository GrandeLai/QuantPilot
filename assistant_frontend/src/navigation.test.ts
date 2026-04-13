import test from "node:test";
import assert from "node:assert/strict";

import { ASSISTANT_TABS } from "./navigation.ts";

test("assistant tabs match the decision flow IA", () => {
  assert.deepEqual(
    ASSISTANT_TABS.map((tab) => tab.key),
    ["overview", "opportunities", "rebalance", "risk", "review"],
  );
});
