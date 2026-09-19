"""Fresh-process independent readback and bounded verdict for SABLE Issue #84 & #63.

This script executes in a separate process outside the agent\'s runtime context.
It reads local effect journals, performs an independent out-of-band readback of the
authoritative external state (GitHub API), computes SHA-256 integrity digests,
and outputs a machine-readable evidence packet.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EFFECTS_FILE = ROOT / "effects" / "effects.jsonl"
METADATA_FILE = ROOT / "run_metadata.json"
EVIDENCE_FILE = ROOT / "evidence.json"


def fetch_external_state(pr_url: str, commit_url: str) -> dict:
    """Fetch authoritative external state from GitHub REST API."""
    proxies = {}
    for env_var in ["HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"]:
        val = os.environ.get(env_var)
        if val:
            proxies["https"] = val
            proxies["http"] = val
            break

    # If requests is installed, use it for socks5 proxy support
    try:
        import requests
        headers = {"User-Agent": "SableVerifier/1.0", "Accept": "application/vnd.github+json"}
        # Check if local socks5 proxy is active
        local_proxy = proxies or {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}
        try:
            r_pr = requests.get(pr_url, headers=headers, proxies=local_proxy, timeout=10)
            r_commit = requests.get(commit_url, headers=headers, proxies=local_proxy, timeout=10)
            if r_pr.status_code == 200 and r_commit.status_code == 200:
                return {
                    "source": "live_github_api",
                    "pr": r_pr.json(),
                    "commit": r_commit.json(),
                }
        except Exception:
            # Try without proxy
            r_pr = requests.get(pr_url, headers=headers, timeout=10)
            r_commit = requests.get(commit_url, headers=headers, timeout=10)
            if r_pr.status_code == 200 and r_commit.status_code == 200:
                return {
                    "source": "live_github_api",
                    "pr": r_pr.json(),
                    "commit": r_commit.json(),
                }
    except ImportError:
        pass

    # Fallback to standard urllib
    req_pr = urllib.request.Request(pr_url, headers={"User-Agent": "SableVerifier/1.0", "Accept": "application/vnd.github+json"})
    req_commit = urllib.request.Request(commit_url, headers={"User-Agent": "SableVerifier/1.0", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req_pr, timeout=10) as resp_pr, urllib.request.urlopen(req_commit, timeout=10) as resp_commit:
        return {
            "source": "live_github_api",
            "pr": json.loads(resp_pr.read().decode("utf-8")),
            "commit": json.loads(resp_commit.read().decode("utf-8")),
        }


def main() -> None:
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    raw_effects = EFFECTS_FILE.read_bytes()
    effects_digest = hashlib.sha256(raw_effects).hexdigest()

    records = [json.loads(line) for line in EFFECTS_FILE.read_text(encoding="utf-8").splitlines() if line]
    matching = [r for r in records if r.get("action_id") == metadata["action_id"]]

    api_pr_url = f"https://api.github.com/repos/{metadata['target_repository']}/pulls/14698"
    api_commit_url = f"https://api.github.com/repos/{metadata['target_repository']}/commits/{metadata['target_commit_sha']}"

    external_data = fetch_external_state(api_pr_url, api_commit_url)
    pr = external_data["pr"]
    commit = external_data["commit"]

    # Construct deterministic canonical state
    canonical_state = {
        "target_repo": metadata["target_repository"],
        "pull_request_number": pr.get("number"),
        "pull_request_url": pr.get("html_url"),
        "pull_request_state": pr.get("state"),
        "author_login": pr.get("user", {}).get("login"),
        "head_ref": pr.get("head", {}).get("ref"),
        "head_sha": pr.get("head", {}).get("sha"),
        "commit_sha": commit.get("sha"),
        "commit_tree_sha": commit.get("commit", {}).get("tree", {}).get("sha"),
        "commit_message": commit.get("commit", {}).get("message", "").strip(),
        "changed_files": sorted([f["filename"] for f in commit.get("files", [])]),
    }
    canonical_bytes = json.dumps(canonical_state, sort_keys=True).encode("utf-8")
    external_state_sha256 = hashlib.sha256(canonical_bytes).hexdigest()

    # Verification predicates
    pr_matches = (
        pr.get("state") in ["open", "closed"]
        and pr.get("head", {}).get("sha") == metadata["target_commit_sha"]
        and pr.get("user", {}).get("login") == "Tsai-etc"
    )
    commit_matches = (
        commit.get("sha") == metadata["target_commit_sha"]
        and commit.get("commit", {}).get("tree", {}).get("sha") == metadata["target_tree_sha"]
    )
    effects_consistent = len(matching) == metadata["effects_count"]

    if pr_matches and commit_matches and effects_consistent:
        verdict = "VERIFIED"
    elif len(matching) == 0:
        verdict = "NOT VERIFIED"
    else:
        verdict = "EVIDENCE GAP"

    evidence = {
        "bounty_pilot": metadata["bounty_pilot"],
        "related_open_call": metadata["related_open_call"],
        "session_id": metadata["session_id"],
        "action_id": metadata["action_id"],
        "agent_runtime": metadata["agent_runtime"],
        "agent_identity": metadata["agent_identity"],
        "target_repository": metadata["target_repository"],
        "target_pull_request": metadata["target_pull_request"],
        "target_commit_sha": metadata["target_commit_sha"],
        "target_tree_sha": metadata["target_tree_sha"],
        "workflow_status": metadata["workflow_status"],
        "fresh_process_pid": os.getpid(),
        "effects_count": len(matching),
        "effects_sha256": effects_digest,
        "external_state_sha256": external_state_sha256,
        "external_verification_details": {
            "source": external_data["source"],
            "remote_pr_state": pr.get("state"),
            "remote_pr_head_sha": pr.get("head", {}).get("sha"),
            "remote_commit_author": pr.get("user", {}).get("login"),
            "remote_commit_sha": commit.get("sha"),
            "remote_tree_sha": commit.get("commit", {}).get("tree", {}).get("sha"),
            "remote_changed_files": canonical_state["changed_files"],
        },
        "verdict": verdict,
        "boundary": (
            "VERIFIED iff independent out-of-band readback from external authoritative source (GitHub API) "
            "confirms target PR, commit SHA, tree SHA, and author match agent declared mutations."
        ),
    }

    EVIDENCE_FILE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
