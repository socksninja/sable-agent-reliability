#!/usr/bin/env python3
"""Self-test for the TTR-01 local-provider receipt and oracle."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "ttr01_local_provider_repro.py"


class TTR01LocalProviderTest(unittest.TestCase):
    def test_reproduces_lost_child_error_and_oracle_detects_it(self) -> None:
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

        self.assertTrue(receipt["reproduction"]["not_benchmark_admitted"])
        self.assertEqual(receipt["provider"]["status_code"], 500)
        self.assertEqual(receipt["child_terminal_state"], "FAILED")
        self.assertEqual(receipt["parent_received_state"], "RESULT")
        self.assertEqual(receipt["parent_received_payload"], "")
        self.assertEqual(receipt["oracle_result"]["classification"], "ERROR_LOST")
        self.assertTrue(receipt["oracle_result"]["oracle_pass"])
        self.assertTrue(receipt["parent_call_id"])
        self.assertTrue(receipt["child_session_id"])
        self.assertTrue(receipt["provider_request_id"])


if __name__ == "__main__":
    unittest.main()
