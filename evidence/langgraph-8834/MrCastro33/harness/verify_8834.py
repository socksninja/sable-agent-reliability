"""Orchestrator for the bounded independent verification of LangGraph #8834.

Runs every case in its own subprocess, then performs the downstream-effect
readback in a separate process that never executes the graph, and writes a
machine-readable evidence bundle plus a SHA-256 manifest.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_CASE = os.path.join(HERE, "run_case.py")
READBACK = os.path.join(HERE, "readback.py")

CASES = [
    ("route_memory", "memory", "route"),
    ("route_sqlite", "sqlite", "route"),
    ("node_memory", "memory", "node"),
    ("node_sqlite", "sqlite", "node"),
    ("none_memory", "memory", "none"),
    ("none_sqlite", "sqlite", "none"),
]


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def capture_env(outdir: str) -> dict:
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                            capture_output=True, text=True)
    import importlib.metadata as md
    import langgraph

    if getattr(langgraph, "__file__", None):
        lg_dir = os.path.dirname(os.path.abspath(langgraph.__file__))
    else:  # namespace package
        lg_dir = os.path.abspath(list(langgraph.__path__)[0])
    watched = [
        "graph/state.py",
        "pregel/_runner.py",
        "pregel/_loop.py",
        "pregel/main.py",
    ]
    source_hashes = {}
    for rel in watched:
        p = os.path.join(lg_dir, rel)
        if os.path.exists(p):
            source_hashes[rel] = sha256_file(p)

    versions = {}
    for dist in ("langgraph", "langgraph-checkpoint", "langgraph-checkpoint-sqlite",
                 "langchain-core", "pydantic"):
        try:
            versions[dist] = md.version(dist)
        except Exception:  # noqa: BLE001
            versions[dist] = None

    env = {
        "captured_at": _now(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "sqlite3_library_version": __import__("sqlite3").sqlite_version,
        "package_versions": versions,
        "langgraph_package_dir": lg_dir,
        "langgraph_source_sha256": source_hashes,
        "pip_freeze": freeze.stdout.splitlines(),
    }
    with open(os.path.join(outdir, "environment.json"), "w", encoding="utf-8") as fh:
        json.dump(env, fh, indent=2, sort_keys=True)
    return env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    outdir = os.path.abspath(args.outdir)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    for sub in ("cases", "readback", "databases", "logs"):
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)

    run_id = str(uuid.uuid4())
    env = capture_env(outdir)
    effects_db = os.path.join(outdir, "databases", f"effects_{run_id}.db")

    results = []
    for case_id, saver, failure in CASES:
        checkpoint_db = os.path.join(outdir, "databases", f"checkpoints_{case_id}_{run_id}.db")
        case_json = os.path.join(outdir, "cases", f"{case_id}.json")
        cmd = [sys.executable, RUN_CASE,
               "--case-id", case_id, "--run-id", run_id,
               "--saver", saver, "--failure", failure,
               "--effects-db", effects_db,
               "--checkpoint-db", checkpoint_db,
               "--out", case_json]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        with open(os.path.join(outdir, "logs", f"{case_id}.run.stdout.txt"), "w", encoding="utf-8") as fh:
            fh.write(proc.stdout)
        with open(os.path.join(outdir, "logs", f"{case_id}.run.stderr.txt"), "w", encoding="utf-8") as fh:
            fh.write(proc.stderr)

        rb_json = os.path.join(outdir, "readback", f"{case_id}.json")
        rb_cmd = [sys.executable, READBACK,
                  "--case-id", case_id, "--thread-id", case_id,
                  "--effects-db", effects_db,
                  "--checkpoint-db", checkpoint_db if saver == "sqlite" else "",
                  "--out", rb_json]
        rb_proc = subprocess.run(rb_cmd, capture_output=True, text=True)
        with open(os.path.join(outdir, "logs", f"{case_id}.readback.stdout.txt"), "w", encoding="utf-8") as fh:
            fh.write(rb_proc.stdout)
        with open(os.path.join(outdir, "logs", f"{case_id}.readback.stderr.txt"), "w", encoding="utf-8") as fh:
            fh.write(rb_proc.stderr)

        case = json.load(open(case_json, encoding="utf-8")) if os.path.exists(case_json) else None
        rb = json.load(open(rb_json, encoding="utf-8")) if os.path.exists(rb_json) else None

        runtime_value = None
        runtime_pending = None
        sink_calls = None
        if case:
            runtime_value = (case.get("resume", {}).get("result") or {}).get("value")
            runtime_pending = case.get("state_after_resume", {}).get("next")
            sink_calls = case.get("calls_after_resume", {}).get("sink")
        external_rows = rb["effects"]["sink_effect_rows"] if rb else None
        external_value = rb["effects"].get("observed_value") if rb else None
        checkpoint_values = rb["checkpoint"].get("values") if rb else None

        runtime_claims_done = bool(case) and not case.get("resume", {}).get("raised") and runtime_pending == []
        runtime_reports_sink_effect = runtime_value == 2
        external_shows_sink_effect = bool(external_rows)

        results.append({
            "case_id": case_id,
            "saver": saver,
            "failure_location": failure,
            "run_exit_code": proc.returncode,
            "readback_exit_code": rb_proc.returncode,
            "first_invocation_raised": case.get("first_invocation", {}).get("raised") if case else None,
            "first_error": case.get("first_invocation", {}).get("error") if case else None,
            "pending_before_resume": case.get("state_before_resume", {}).get("next") if case else None,
            "resume_returned_value": runtime_value,
            "resume_raised": case.get("resume", {}).get("raised") if case else None,
            "pending_after_resume": runtime_pending,
            "in_process_calls": case.get("calls_after_resume") if case else None,
            "sink_calls": sink_calls,
            "external_sink_effect_rows": external_rows,
            "external_observed_value": external_value,
            "fresh_process_checkpoint_values": checkpoint_values,
            "runtime_claims_completed": runtime_claims_done,
            "runtime_reports_sink_effect": runtime_reports_sink_effect,
            "external_shows_sink_effect": external_shows_sink_effect,
            "response_matches_external_readback": runtime_reports_sink_effect == external_shows_sink_effect,
            "silent_completion": runtime_claims_done and not external_shows_sink_effect and failure != "none",
            "case_artifact": os.path.relpath(case_json, outdir),
            "readback_artifact": os.path.relpath(rb_json, outdir),
        })

    by_id = {r["case_id"]: r for r in results}
    router_cases = [r for r in results if r["failure_location"] == "route"]
    control_cases = [r for r in results if r["failure_location"] in ("node", "none")]

    observer_valid = all(c["external_shows_sink_effect"] for c in control_cases)
    bug_present = all(
        r["first_invocation_raised"] and r["resume_raised"] is False
        and r["pending_after_resume"] == []
        and r["sink_calls"] == 0
        and r["external_sink_effect_rows"] == 0
        for r in router_cases
    )
    all_agree = all(r["response_matches_external_readback"] for r in results)

    if not observer_valid:
        verdict = "EVIDENCE GAP"
    elif bug_present and all_agree:
        verdict = "VERIFIED"
    elif not bug_present:
        verdict = "NOT VERIFIED"
    else:
        verdict = "EVIDENCE GAP"

    evidence = {
        "schema": "sable-evidence/1",
        "target_issue": "https://github.com/langchain-ai/langgraph/issues/8834",
        "bounty_issue": "https://github.com/socksninja/sable-agent-reliability/issues/86",
        "verifier": "MrCastro33",
        "execution": "Codex (OpenAI GPT-6 agent), locally executed",
        "run_id": run_id,
        "generated_at": _now(),
        "environment": env,
        "evidence_question": "Does the resumed runtime response agree with a fresh external readback of the downstream effect?",
        "method": {
            "isolation": "each case runs in its own OS process with its own thread_id and its own checkpoint database",
            "durable_effect": "the sink node, and only the sink node, commits one row to a separate local SQLite effects database",
            "readback": "a separate process, which never executes graph nodes, re-opens the effects database read-only and re-opens the persisted checkpoint",
            "controls": "node-failure and no-failure controls prove the observer detects a real sink effect",
        },
        "cases": results,
        "findings": {
            "observer_validated_by_controls": observer_valid,
            "router_failure_reproduced_on_all_savers": bug_present,
            "response_and_external_readback_agree_in_all_cases": all_agree,
            "answer_to_evidence_question": (
                "Yes. In every case the resumed response and the fresh external readback agree about "
                "whether the downstream sink ran. The defect is not a response/state divergence: after a "
                "conditional-router exception the runtime returns normally with an empty pending-task list "
                "while the selected downstream node never ran, so a normal return is not evidence of completion."
            ) if (bug_present and all_agree and observer_valid) else "See per-case results.",
        },
        "verdict": verdict,
        "scope_limits": [
            "Synchronous StateGraph.invoke only; async execution was not tested.",
            "InMemorySaver and SqliteSaver only; no other persistence backend was tested.",
            "Single-node linear graph with one conditional edge; subgraphs, parallel branches, interrupts and retry policies were not tested.",
            "No production workload, no frequency or impact estimate in production.",
            "Single machine, single OS and Python build as recorded in environment.json.",
            "LangGraph source was not modified and no patch is proposed.",
        ],
    }

    ev_path = os.path.join(outdir, "EVIDENCE_8834_VERIFICATION.json")
    with open(ev_path, "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2, sort_keys=True, default=str)

    manifest_lines = []
    for root, _dirs, files in os.walk(outdir):
        for name in sorted(files):
            if name == "MANIFEST.sha256":
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, outdir)
            manifest_lines.append(f"{sha256_file(full)}  {rel}")
    manifest_lines.sort(key=lambda line: line.split("  ", 1)[1])
    manifest_path = os.path.join(outdir, "MANIFEST.sha256")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(manifest_lines) + "\n")

    print(json.dumps({"run_id": run_id, "verdict": verdict,
                      "observer_valid": observer_valid,
                      "bug_present": bug_present,
                      "all_agree": all_agree,
                      "evidence_sha256": sha256_file(ev_path),
                      "cases": {r["case_id"]: {"sink_calls": r["sink_calls"],
                                                 "resume_value": r["resume_returned_value"],
                                                 "external_rows": r["external_sink_effect_rows"],
                                                 "pending_after": r["pending_after_resume"]}
                                 for r in results}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
