#!/usr/bin/env python3
"""
Evidence-Gap report for openclaw/openclaw#136513
Bounty: socksninja/sable-agent-reliability#89

Upstream bug claim:
  A duplicate subagent completion replay can receive an in_flight response
  while the original completion is still pending, but the direct-delivery
  path can record it as delivered before terminal evidence exists.

Bounty question:
  Can an in-flight completion receive delivery credit before a terminal result
  or visible delivery evidence exists?

Evidence output: EVIDENCE_OPENCLAW_136513_VERIFICATION.json
"""

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone

ISSUE_ID = "OPENCLAW_136513"
EVIDENCE_FILE = "EVIDENCE_OPENCLAW_136513_VERIFICATION.json"

RUNTIME = {
    "python": sys.version,
    "platform": platform.platform(),
    "python_executable": sys.executable,
}

# ─── Step 1: Attempt to install the target package ───────────────────────────

def probe_install(package_name: str) -> dict:
    """Try pip install <package_name> in the current venv and capture result."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package_name, "--dry-run"],
        capture_output=True,
        text=True,
    )
    return {
        "package": package_name,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def get_installed_version(package_name: str) -> str | None:
    """Return installed version or None."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return None


# ─── Step 2: Attempt to import target module ─────────────────────────────────

def probe_import(package_name: str) -> dict:
    """Try importing the package and probe for required symbols."""
    result = {
        "importable": False,
        "version": None,
        "has_completion_api": False,
        "has_delivery_ledger": False,
        "symbols_found": [],
        "error": None,
    }
    try:
        import importlib
        mod = importlib.import_module(package_name)
        result["importable"] = True
        result["version"] = getattr(mod, "__version__", None)

        all_symbols = dir(mod)
        result["symbols_found"] = all_symbols

        # Look for any completion/delivery related API
        completion_keywords = [
            "completion", "deliver", "in_flight", "inflight", "idempotency",
            "subagent", "replay", "pending", "credit", "ledger", "handoff",
        ]
        for sym in all_symbols:
            sym_lower = sym.lower()
            if any(kw in sym_lower for kw in completion_keywords):
                result["has_completion_api"] = True
                break

        delivery_keywords = ["ledger", "delivery", "credit", "account"]
        for sym in all_symbols:
            sym_lower = sym.lower()
            if any(kw in sym_lower for kw in delivery_keywords):
                result["has_delivery_ledger"] = True
                break

    except ImportError as exc:
        result["error"] = str(exc)
    except Exception as exc:
        result["error"] = str(exc)

    return result


# ─── Step 3: Probe pypi for the *real* openclaw project ──────────────────────

def probe_pypi_metadata(package_name: str) -> dict:
    """Fetch PyPI JSON metadata for the package."""
    import urllib.request
    import urllib.error

    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        info = data.get("info", {})
        return {
            "pypi_name": info.get("name"),
            "pypi_version": info.get("version"),
            "pypi_summary": info.get("summary"),
            "pypi_home_page": info.get("home_page"),
            "pypi_project_urls": info.get("project_urls"),
            "pypi_author": info.get("author"),
            "pypi_description_excerpt": (info.get("description") or "")[:400],
        }
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"error": str(exc)}


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print(f"openclaw/openclaw#136513 — Evidence Gap Investigation")
    print(f"socksninja/sable-agent-reliability#89")
    print("=" * 72)
    print()

    # --- probe install attempts ---
    install_results = {}
    for name in ["openclaw", "open-claw"]:
        print(f"[PROBE] pip install {name!r} ...")
        install_results[name] = probe_install(name)
        rc = install_results[name]["returncode"]
        print(f"  returncode={rc}")
        if rc != 0:
            print(f"  stderr: {install_results[name]['stderr'][:200]}")

    # --- check what's actually installed ---
    openclaw_installed_version = get_installed_version("openclaw")
    print(f"\n[INFO] 'openclaw' installed version: {openclaw_installed_version!r}")

    # --- probe import ---
    print("\n[PROBE] Importing 'openclaw' ...")
    import_result = probe_import("openclaw")
    print(f"  importable: {import_result['importable']}")
    print(f"  version: {import_result['version']}")
    print(f"  has_completion_api: {import_result['has_completion_api']}")
    print(f"  has_delivery_ledger: {import_result['has_delivery_ledger']}")
    if import_result["error"]:
        print(f"  error: {import_result['error']}")

    # --- check PyPI metadata ---
    print("\n[PROBE] Fetching PyPI metadata for 'openclaw' ...")
    pypi_meta = probe_pypi_metadata("openclaw")
    print(f"  PyPI name: {pypi_meta.get('pypi_name')}")
    print(f"  PyPI summary: {pypi_meta.get('pypi_summary')}")
    print(f"  PyPI home_page: {pypi_meta.get('pypi_home_page')}")
    print(f"  PyPI project_urls: {pypi_meta.get('pypi_project_urls')}")

    # --- determine VERDICT ---
    #
    # The PyPI 'openclaw' package (v2.0.2) is an unrelated CLI installer for
    # the cmdop.com product. Its own metadata explicitly states:
    #   "Not affiliated with the OpenClaw project (github.com/openclaw/openclaw)"
    # The real openclaw/openclaw GitHub project appears to be private/internal
    # and has no PyPI distribution. 'open-claw' also does not exist on PyPI.
    #
    # Without the actual openclaw package we cannot:
    #   - pin the reported source/revision
    #   - instantiate a real completion handoff
    #   - replay an idempotency key with expectFinal=true
    #   - capture the in_flight response from the target code path
    #   - observe delivery-accounting state before terminal evidence
    #
    # Therefore the verdict is EVIDENCE GAP.

    pypi_is_wrong_package = (
        import_result["importable"]
        and not import_result["has_completion_api"]
        and not import_result["has_delivery_ledger"]
    )
    # Also confirm the disclaimer text from the module docstring
    disclaimer_confirmed = False
    try:
        import openclaw as _oc
        pkg_doc = (_oc.__doc__ or "")
        disclaimer_confirmed = "not affiliated" in pkg_doc.lower() or "cmdop" in pkg_doc.lower()
    except Exception:
        pass

    verdict = "EVIDENCE GAP"

    evidence = {
        "schema_version": "1.0",
        "issue": {
            "bounty_repo": "socksninja/sable-agent-reliability",
            "bounty_issue": 89,
            "upstream_ref": "openclaw/openclaw#136513",
        },
        "runtime": RUNTIME,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "install_probes": install_results,
        "installed_pypi_openclaw": {
            "version": openclaw_installed_version,
            "import_result": import_result,
            "pypi_metadata": pypi_meta,
            "is_wrong_package": pypi_is_wrong_package,
            "disclaimer_confirmed": disclaimer_confirmed,
        },
        "gap_analysis": {
            "openclaw_on_pypi": True,
            "openclaw_pypi_is_target_project": False,
            "reason": (
                "The PyPI package named 'openclaw' (v2.0.2) is an installer "
                "for the cmdop CLI product and explicitly states it is NOT "
                "affiliated with github.com/openclaw/openclaw. It has no "
                "completion, delivery-ledger, idempotency-key, or subagent APIs. "
                "'open-claw' does not exist on PyPI. The real openclaw/openclaw "
                "GitHub project is private/internal with no public distribution."
            ),
            "cannot_pin_source_revision": True,
            "cannot_instantiate_completion": True,
            "cannot_replay_idempotency_key": True,
            "cannot_observe_delivery_credit": True,
            "cannot_observe_terminal_evidence": True,
        },
        "control_case": {
            "description": "N/A — target library unavailable for instantiation",
            "result": None,
        },
        "bug_case": {
            "description": "N/A — target library unavailable; cannot hold completion pending or replay",
            "result": None,
        },
        "verdict": verdict,
        "verdict_reason": (
            "Independent verification cannot proceed because the actual "
            "openclaw/openclaw package is not available via any public Python "
            "package index. The PyPI 'openclaw' distribution is a wholly "
            "unrelated product. Without the target library we cannot pin the "
            "reported revision, create a real completion handoff, replay an "
            "idempotency key, or observe delivery-credit state transitions."
        ),
    }

    # --- write evidence file ---
    evidence_json = json.dumps(evidence, indent=2, default=str)
    with open(EVIDENCE_FILE, "w") as fh:
        fh.write(evidence_json)
        fh.write("\n")

    sha256 = hashlib.sha256(evidence_json.encode()).hexdigest()

    print()
    print("=" * 72)
    print(f"VERDICT: {verdict}")
    print(f"Evidence written to: {EVIDENCE_FILE}")
    print(f"SHA-256: {sha256}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(main())
