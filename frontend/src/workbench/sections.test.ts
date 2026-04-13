import assert from "node:assert/strict";
import test from "node:test";

import { WORKBENCH_SECTIONS } from "./sections.ts";

test("topic-only tabs are removed from first-class workbench sections", () => {
  assert.deepEqual(Object.keys(WORKBENCH_SECTIONS), [
    "research",
    "strategy",
    "validation",
    "run",
    "risk_review",
  ]);

  assert.equal(WORKBENCH_SECTIONS.research.includes("options"), false);
  assert.equal(WORKBENCH_SECTIONS.research.includes("plugins"), false);
});
