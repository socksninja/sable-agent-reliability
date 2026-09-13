import assert from "node:assert/strict";

// Run from the SABLE repository root after checking out OpenClaw at:
// ./openclaw
// Expected revision: 0d0e2852b2542c4d128c34d8fc9a1edb2100e1d2
const { resolveCronCompletionStatus } = await import(
  "./openclaw/src/cron/completion-status.ts"
);

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
