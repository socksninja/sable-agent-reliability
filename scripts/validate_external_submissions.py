#!/usr/bin/env python3
"""Validate every external Reliability Record submission in submissions/."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSIONS = ROOT / "submissions"
VALIDATOR = ROOT / "scripts" / "validate_reliability_submission_v01.py"


def main() -> None:
    paths = sorted(SUBMISSIONS.glob("*.json")) if SUBMISSIONS.exists() else []
    if not paths:
        print("NO_EXTERNAL_SUBMISSIONS=true")
        return

    seen: set[str] = set()
    for path in paths:
        obj = json.loads(path.read_text(encoding="utf-8"))
        record_id = obj.get("record_id")
        if record_id in seen:
            raise SystemExit(f"DUPLICATE_RECORD_ID: {record_id}")
        seen.add(record_id)
        subprocess.run([sys.executable, str(VALIDATOR), str(path)], check=True)

    print(f"VALID_EXTERNAL_SUBMISSIONS={len(paths)}")
    print("RECORD_IDS=" + json.dumps(sorted(seen)))


if __name__ == "__main__":
    main()
