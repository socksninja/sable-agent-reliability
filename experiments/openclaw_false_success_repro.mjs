import assert from "node:assert/strict";

const { resolveCronCompletionStatus } = await import(
  "../../openclaw/openclaw/src/cron/completion-status.ts"
);

const result = resolveCronCompletionStatus({
  status: "ok",
  deliveryStatus: "not-requested",
  requiredDelivery: false,
});

console.log(JSON.stringify({
  case: "deferred-or-dispatch-only run represented as successful completion",
  input: {
    status: "ok",
    deliveryStatus: "not-requested",
    requiredDelivery: false,
  },
  observed_completion_status: result,
  expected_for_unobserved_agent_completion: "unknown",
}));

assert.equal(result, "succeeded");
console.log("REPRO_PASS: OpenClaw completion mapper returns succeeded for status=ok with no required delivery.");
