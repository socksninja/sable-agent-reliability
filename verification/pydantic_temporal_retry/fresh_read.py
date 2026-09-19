"""Fresh-process readback and bounded verdict for bounty #90."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
effects_path = ROOT / "effects" / "effects.jsonl"
metadata = json.loads((ROOT / "run_metadata.json").read_text(encoding="utf-8"))
records = [json.loads(line) for line in effects_path.read_text(encoding="utf-8").splitlines() if line]
matching = [r for r in records if r.get("action_id") == metadata["action_id"]]
digest = hashlib.sha256(effects_path.read_bytes()).hexdigest()

if metadata.get("workflow_status") == "failed_after_retry" and len(matching) >= 2:
    verdict = "VERIFIED"
elif len(matching) <= 1:
    verdict = "NOT VERIFIED"
else:
    verdict = "EVIDENCE GAP"

evidence = {
    "bounty": metadata["bounty"],
    "target": metadata["target"],
    "action_id": metadata["action_id"],
    "workflow_status": metadata.get("workflow_status"),
    "fresh_process_pid": __import__("os").getpid(),
    "effect_count_for_action": len(matching),
    "records": matching,
    "effects_sha256": digest,
    "verdict": verdict,
    "boundary": "VERIFIED iff the workflow exhausts retry after the first committed effect and fresh readback finds >=2 effects for one logical action ID.",
}
(ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, indent=2))
