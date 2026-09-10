#!/usr/bin/env python3
"""Verify that an external Reliability Record points to real GitHub evidence."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REPO = re.compile(r"^[^/\s]+/[^/\s]+$")
API = "https://api.github.com"


def fail(msg: str) -> None:
    raise SystemExit(f"ADMISSION_DENIED: {msg}")


def get_json(url: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "sable-admission/0.2"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        fail(f"GitHub API {exc.code}: {url}")
    except urllib.error.URLError as exc:
        fail(f"GitHub API unavailable: {exc.reason}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: admit_external_reliability_record_v02.py PATH")
    path = Path(sys.argv[1])
    record = json.loads(path.read_text(encoding="utf-8"))
    provenance = record.get("provenance", {})
    repo = provenance.get("repository")
    run_id = provenance.get("run_id")
    job_id = provenance.get("job_id")
    commit = provenance.get("commit")
    artifact = record.get("artifact", {})
    artifact_id = artifact.get("artifact_id")
    artifact_name = artifact.get("name")
    artifact_sha = artifact.get("sha256")

    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        fail("invalid provenance.repository")
    if not isinstance(run_id, int) or run_id < 1:
        fail("invalid provenance.run_id")
    if not isinstance(job_id, int) or job_id < 1:
        fail("invalid provenance.job_id")
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        fail("invalid provenance.commit")
    if not isinstance(artifact_id, int) or artifact_id < 1:
        fail("invalid artifact.artifact_id")
    if not isinstance(artifact_name, str) or not artifact_name:
        fail("invalid artifact.name")
    if not isinstance(artifact_sha, str) or not HEX64.fullmatch(artifact_sha):
        fail("invalid artifact.sha256")

    run = get_json(f"{API}/repos/{repo}/actions/runs/{run_id}")
    if run.get("id") != run_id:
        fail("run_id does not resolve to the cited workflow run")
    if run.get("head_sha") != commit:
        fail("workflow run head_sha does not match provenance.commit")
    if run.get("repository", {}).get("full_name") != repo:
        fail("workflow run repository does not match provenance.repository")

    job = get_json(f"{API}/repos/{repo}/actions/jobs/{job_id}")
    if job.get("id") != job_id:
        fail("job_id does not resolve")
    if job.get("run_id") != run_id:
        fail("job does not belong to cited run")
    if job.get("conclusion") != "success":
        fail(f"cited job conclusion is {job.get('conclusion')!r}, not 'success'")
    if job.get("head_sha") and job.get("head_sha") != commit:
        fail("job head_sha does not match provenance.commit")

    art = get_json(f"{API}/repos/{repo}/actions/artifacts/{artifact_id}")
    if art.get("id") != artifact_id:
        fail("artifact_id does not resolve")
    if art.get("name") != artifact_name:
        fail("artifact name does not match")
    if art.get("workflow_run", {}).get("id") != run_id:
        fail("artifact does not belong to cited workflow run")
    digest = art.get("digest")
    if digest and digest.startswith("sha256:"):
        digest = digest[len("sha256:"):]
    if digest != artifact_sha:
        fail("artifact SHA-256 digest does not match GitHub")
    if art.get("expired") is True:
        fail("cited artifact is expired")

    out = {
        "admission": "EVIDENCE_REACHABLE",
        "record_id": record.get("record_id"),
        "repository": repo,
        "run_id": run_id,
        "job_id": job_id,
        "commit": commit,
        "artifact_id": artifact_id,
        "artifact_sha256": artifact_sha,
        "verifier": "v0.2",
    }
    print(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
