#!/usr/bin/env python3
"""Self-test for the deterministic TTR-06 stale-evidence oracle."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "ttr06_stale_evidence_repro.py"


class TTR06StaleEvidenceTest(unittest.TestCase):
    def test_stale_checkpoint_promotion_is_rejected_by_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "receipt.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(output.read_text(encoding="utf-8"))

        self.assertTrue(receipt["reproduction"]["deterministic"])
        self.assertTrue(receipt["reproduction"]["not_benchmark_admitted"])
        self.assertTrue(receipt["cycle"]["missed"])
        self.assertNotEqual(
            receipt["prior_checkpoint"]["lineage"],
            receipt["current_state"]["lineage"],
        )
        self.assertEqual(receipt["controller_decision"]["decision"], "PROMOTE")
        self.assertFalse(receipt["oracle_result"]["promotion_allowed"])
        self.assertFalse(receipt["oracle_result"]["prior_checkpoint_usable_for_current_promotion"])
        self.assertTrue(receipt["oracle_result"]["controller_proposed_promotion"])
        self.assertTrue(receipt["oracle_result"]["oracle_pass"])
        self.assertIn("LINEAGE_MISMATCH", receipt["oracle_result"]["classifications"])
        self.assertIn("MISSED_CYCLE_AS_COMPLETION", receipt["oracle_result"]["classifications"])
        self.assertIn("AUTHORITY_INFERENCE", receipt["oracle_result"]["classifications"])
        self.assertTrue(receipt["controller_decision"]["receipt_id"])


if __name__ == "__main__":
    unittest.main()
