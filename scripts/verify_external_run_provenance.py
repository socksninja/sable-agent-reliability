#!/usr/bin/env python3
"""Verify that a public GitHub Actions run has real, successful execution provenance."""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

RUN_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/actions/runs/(\d+)/?(?:\?.*)?$")
API_ROOT = "https://api.github.com"
UA = "sable-external-run-provenance/0.1"


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API {exc.code}: {url}") from exc


def parse_run_url(url: str):
    match = RUN_RE.match(url.strip())
    if not match:
        raise ValueError("run_url must be a public github.com Actions run URL")
    owner, repo, run_id = match.groups()
    return owner, repo, int(run_id)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_url")
    parser.add_argument("--runtime")
    parser.add_argument("--model")
    parser.add_argument("--execution-context")
    args = parser.parse_args()

    owner, repo, run_id = parse_run_url(args.run_url)
    repo_full_name = f"{owner}/{repo}"
    run = get_json(f"{API_ROOT}/repos/{owner}/{repo}/actions/runs/{run_id}")
    jobs_payload = get_json(run["jobs_url"] + "?per_page=100")
    artifacts_payload = get_json(run["artifacts_url"] + "?per_page=100")

    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise AssertionError(f"workflow run is not successful: status={run.get('status')} conclusion={run.get('conclusion')}")
    if run.get("head_sha") is None:
        raise AssertionError("workflow run has no head_sha")

    jobs = jobs_payload.get("jobs", [])
    successful_jobs = [j for j in jobs if j.get("status") == "completed" and j.get("conclusion") == "success"]
    if not successful_jobs:
        raise AssertionError("no successful workflow job found")

    artifacts = artifacts_payload.get("artifacts", [])
    live_artifacts = [a for a in artifacts if not a.get("expired")]
    if not live_artifacts:
        raise AssertionError("no non-expired workflow artifact found")
    if any(not a.get("digest", "").startswith("sha256:") for a in live_artifacts):
        raise AssertionError("at least one live artifact has no GitHub SHA-256 digest")

    manifest = {
        "protocol": "SABLE-EXTERNAL-RUN-PROVENANCE-v0.1",
        "verification": "PASS",
        "provenance_scope": "public GitHub Actions execution existence and artifact reachability; not reliability semantics",
        "submitted_run_url": args.run_url,
        "runtime": args.runtime,
        "model": args.model,
        "execution_context": args.execution_context,
        "repository": repo_full_name,
        "workflow": {
            "id": run.get("workflow_id"),
            "name": run.get("name"),
            "path": run.get("path"),
            "run_id": run.get("id"),
            "run_number": run.get("run_number"),
            "event": run.get("event"),
            "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
            "html_url": run.get("html_url"),
        },
        "jobs": [
            {
                "id": j.get("id"),
                "name": j.get("name"),
                "status": j.get("status"),
                "conclusion": j.get("conclusion"),
                "html_url": j.get("html_url"),
            }
            for j in successful_jobs
        ],
        "artifacts": [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "size_in_bytes": a.get("size_in_bytes"),
                "expired": a.get("expired"),
                "created_at": a.get("created_at"),
                "expires_at": a.get("expires_at"),
                "digest": a.get("digest"),
                "archive_download_url": a.get("archive_download_url"),
            }
            for a in live_artifacts
        ],
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
