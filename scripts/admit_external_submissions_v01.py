#!/usr/bin/env python3
"""Batch-admit external SABLE Reliability Records and emit an audit report.

Machine admission is intentionally separate from human promotion:
STRUCTURALLY_VALID -> EVIDENCE_REACHABLE -> (human review) -> PROMOTED.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSIONS = ROOT / "submissions"
STRUCTURAL = ROOT / "scripts" / "validate_reliability_submission_v01.py"
EVIDENCE = ROOT / "scripts" / "admit_external_reliability_record_v01.py"


def run_checker(script: Path, path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(script), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def main() -> int:
    paths = sorted(SUBMISSIONS.glob("*.json")) if SUBMISSIONS.exists() else []
    report: dict = {
        "schema_version": "sable.admission_report.v0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "submission_count": len(paths),
        "results": [],
    }

    if not paths:
        report["status"] = "NO_SUBMISSIONS"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    seen: set[str] = set()
    overall_ok = True
    for path in paths:
        rel = str(path.relative_to(ROOT))
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            overall_ok = False
            report["results"].append({
                "path": rel,
                "record_id": None,
                "structural_status": "INVALID",
                "evidence_status": "NOT_CHECKED",
                "promotion_status": "PENDING_HUMAN_REVIEW",
                "error": f"invalid JSON: {exc}",
            })
            continue

        record_id = obj.get("record_id")
        duplicate = record_id in seen
        if record_id is not None:
            seen.add(record_id)

        structural_ok, structural_output = run_checker(STRUCTURAL, path)
        evidence_ok = False
        evidence_output = "NOT_CHECKED"
        if structural_ok and not duplicate:
            evidence_ok, evidence_output = run_checker(EVIDENCE, path)

        if duplicate:
            structural_status = "INVALID"
            evidence_status = "NOT_CHECKED"
            error = "duplicate record_id"
        else:
            structural_status = "STRUCTURALLY_VALID" if structural_ok else "INVALID"
            evidence_status = (
                "EVIDENCE_REACHABLE" if evidence_ok
                else "NOT_REACHABLE" if structural_ok
                else "NOT_CHECKED"
            )
            error = None if structural_ok and evidence_ok else (evidence_output or structural_output)

        overall_ok = overall_ok and structural_ok and evidence_ok and not duplicate
        result = {
            "path": rel,
            "record_id": record_id,
            "structural_status": structural_status,
            "evidence_status": evidence_status,
            "promotion_status": "PENDING_HUMAN_REVIEW",
        }
        if error:
            result["error"] = error[-4000:]
        report["results"].append(result)

    report["evidence_reachable_count"] = sum(
        r["evidence_status"] == "EVIDENCE_REACHABLE" for r in report["results"]
    )
    report["status"] = "EVIDENCE_REACHABLE" if overall_ok else "ADMISSION_DENIED"

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
