const VERSION = "sable.verifier_service.v2.8";

function canonicalize(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonicalize(value[k])}`).join(",")}}`;
}

function sha256Hex(bytes) {
  return crypto.subtle.digest("SHA-256", bytes).then((digest) =>
    [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("")
  );
}

function base64ToBytes(value) {
  return Uint8Array.from(Buffer.from(value, "base64"));
}

async function verifyReceipt(receipt) {
  const reasons = [];
  if (receipt?.schema_version !== "sable.verification_receipt.v2.6") reasons.push("schema_version_mismatch");
  const signing = receipt?.signing || {};
  if (signing.alg !== "Ed25519") reasons.push("signing_algorithm_mismatch");

  const body = Object.fromEntries(Object.entries(receipt || {}).filter(([k]) =>
    !["receipt_hash", "signature", "signing", "public_key"].includes(k)
  ));
  const encoder = new TextEncoder();
  const bodyBytes = encoder.encode(canonicalize(body));
  const computedHash = await sha256Hex(bodyBytes);
  if (receipt?.receipt_hash !== computedHash) reasons.push("receipt_integrity_mismatch");

  try {
    const publicKey = await crypto.subtle.importKey(
      "raw",
      base64ToBytes(receipt.public_key),
      { name: "Ed25519" },
      false,
      ["verify"]
    );
    const payload = Object.fromEntries(Object.entries(receipt).filter(([k]) => k !== "signature"));
    const valid = await crypto.subtle.verify(
      { name: "Ed25519" },
      publicKey,
      base64ToBytes(receipt.signature),
      encoder.encode(canonicalize(payload))
    );
    if (!valid) reasons.push("signature_invalid");
  } catch {
    reasons.push("signature_invalid");
  }

  const auth = receipt?.authorization || {};
  const evidence = receipt?.evidence || {};
  if (auth.permission !== "ALLOW" || auth.verified !== true) reasons.push("authorization_not_verified_allow");
  if (evidence.task_success !== true || evidence.replay_match !== true) reasons.push("execution_not_verified");
  for (const field of ["evidence_hash", "before_state_hash", "after_state_hash"]) {
    if (!evidence[field]) reasons.push(`${field}_missing`);
  }
  return { ok: reasons.length === 0, reasons };
}

async function verifyPayload(payload) {
  const schema = payload?.schema_version || payload?.protocol_version;
  if (schema === "sable.verification_receipt.v2.6") {
    const { ok, reasons } = await verifyReceipt(payload);
    return {
      schema_version: VERSION,
      verified: ok,
      decision: ok ? "VERIFIED" : "REJECTED",
      reasons,
      verification_level: ok ? "CRYPTOGRAPHICALLY_VERIFIED" : "REJECTED",
      execution_proof: ok,
      receipt_hash: payload.receipt_hash,
    };
  }
  if (schema === "sable.submission.v0.9") {
    return {
      schema_version: VERSION,
      verified: false,
      decision: "REJECTED",
      reasons: ["raw_submission_requires_v26_signed_receipt"],
      verification_level: "STRUCTURALLY_VALID",
      execution_proof: false,
    };
  }
  return {
    schema_version: VERSION,
    verified: false,
    decision: "REJECTED",
    reasons: ["unsupported_schema"],
    verification_level: "REJECTED",
    execution_proof: false,
  };
}

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "method_not_allowed" });
  try {
    const payload = typeof req.body === "string" ? JSON.parse(req.body) : req.body;
    const result = await verifyPayload(payload);
    res.status(result.verified ? 200 : 422).json(result);
  } catch (error) {
    res.status(400).json({ error: "invalid_json", detail: error?.name || "Error" });
  }
}
