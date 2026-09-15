#!/usr/bin/env python3
"""Verify a SABLE execution manifest against live GitHub Actions metadata."""
import json
import os
import sys
import urllib.request


def fetch_json(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "sable-execution-manifest-verifier/1.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_execution_manifest.py <manifest.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        m = json.load(f)

    repo = os.environ.get("GITHUB_REPOSITORY", "socksninja/sable-agent-reliability")
    run_id = m["verification"]["run_id"]
    job_id = m["verification"]["job_id"]
    artifact_id = m["verification"]["artifact"]["id"]

    run = fetch_json(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}")
    assert run["id"] == run_id
    assert run["conclusion"] == m["verification"]["run_conclusion"] == "success"
    assert run["head_sha"] == m["verification"]["head_sha"]
    assert run["path"] == m["verification"]["workflow_path"]

    jobs = fetch_json(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")
    matching = [j for j in jobs["jobs"] if j["id"] == job_id]
    assert len(matching) == 1
    assert matching[0]["name"] == m["verification"]["job_name"]
    assert matching[0]["conclusion"] == "success"

    artifacts = fetch_json(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100")
    matching_artifacts = [a for a in artifacts["artifacts"] if a["id"] == artifact_id]
    assert len(matching_artifacts) == 1
    artifact = matching_artifacts[0]
    assert artifact["name"] == m["verification"]["artifact"]["name"]
    assert artifact["digest"] == m["verification"]["artifact"]["digest"]
    assert artifact["expired"] is False

    print(json.dumps({
        "status": "PASS",
        "run_id": run_id,
        "job_id": job_id,
        "artifact_id": artifact_id,
        "artifact_digest": artifact["digest"],
        "head_sha": run["head_sha"],
        "verifier_status": m["result"]["verifier_status"],
    }, indent=2))


if __name__ == "__main__":
    main()
