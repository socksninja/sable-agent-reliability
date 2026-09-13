import assert from "node:assert/strict";
import path from "node:path";

// The workflow checks out the exact OpenClaw revision into OPENCLAW_ROOT.
const openclawRoot = process.env.OPENCLAW_ROOT;
if (!openclawRoot) {
  throw new Error("OPENCLAW_ROOT must point at the checked-out OpenClaw tree");
}

const completionStatusPath = path.join(
  openclawRoot,
  "src/cron/completion-status.ts",
);

const { resolveCronCompletionStatus } = await import(completionStatusPath);

const input = {
  status: "ok",
  deliveryStatus: "not-requested",
  requiredDelivery: false,
};

const observed = resolveCronCompletionStatus(input);

console.log(JSON.stringify({
  reproduction: "SABLE-FS-0002 / OpenClaw deferred systemEvent completion mapping",
  openclaw_revision: "0d0e2852b2542c4d128c34d8fc9a1edb2100e1d2",
  input,
  observed_completion_status: observed,
  expected_unobserved_agent_completion: "unknown",
}, null, 2));

assert.equal(observed, "succeeded");
console.log("REPRO_PASS: exact OpenClaw completion mapper produces succeeded for an execution with no required delivery fact.");
