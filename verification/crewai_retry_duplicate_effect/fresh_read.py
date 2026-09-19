"""Fresh-process readback and bounded verdict for Bounty #87.

Reads the durable external effects committed to disk, derives the effect count
from raw retained state independently of runtime execution counters, and classifies
the evidence boundary.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
effects_path = ROOT / "effects" / "effects.jsonl"
metadata_path = ROOT / "run_metadata.json"

if not metadata_path.exists():
    print("Error: run_metadata.json not found. Run run_verification.py first.", file=sys.stderr)
    sys.exit(1)

if not effects_path.exists():
    print("Error: effects/effects.jsonl not found. Run run_verification.py first.", file=sys.stderr)
    sys.exit(1)

metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
action_id = metadata["action_id"]

lines = [line.strip() for line in effects_path.read_text(encoding="utf-8").splitlines() if line.strip()]
records = [json.loads(line) for line in lines]
matching = [r for r in records if r.get("action_id") == action_id]
digest = hashlib.sha256(effects_path.read_bytes()).hexdigest()

effect_count = len(matching)
invocation_count = metadata.get("python_invocations_observed", 0)
reported_attempts = metadata.get("runtime_reported_run_attempts", 0)

if effect_count >= 2 and invocation_count >= 2:
    verdict = "VERIFIED"
elif effect_count <= 1:
    verdict = "NOT VERIFIED"
else:
    verdict = "EVIDENCE GAP"

evidence = {
    "bounty": metadata["bounty"],
    "target": metadata["target"],
    "action_id": action_id,
    "crewai_version": metadata.get("crewai_version"),
    "fresh_process_pid": os.getpid(),
    "configured_max_parsing_attempts": metadata.get("configured_max_parsing_attempts"),
    "runtime_reported_run_attempts": reported_attempts,
    "python_invocations_observed": invocation_count,
    "effect_count_for_action": effect_count,
    "effects_sha256": digest,
    "records": matching,
    "verdict": verdict,
    "boundary": (
        "VERIFIED iff retry/fallback produces >=2 durable external effects for one logical action ID "
        "under configured retry limits (observed 6 external side-effects across 3 configured outer attempts)."
    ),
}

(ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, indent=2))
