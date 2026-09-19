"""Minimal OpenAI Agents SDK -> harmless GitHub effect -> SABLE receipt harness.

This is intentionally fail-closed: without OPENAI_API_KEY it exits before
creating any external effect. A design partner can run one real tool execution
and preserve only the runtime/trace/effect identity and final-state hash.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from agents import Agent, Runner, function_tool

REPO = os.environ.get("GITHUB_REPOSITORY", "socksninja/sable-agent-reliability")
ISSUE_NUMBER = int(os.environ.get("SABLE_EXTERNAL_ISSUE", "63"))
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")
MARKER = f"SABLE-OPENAI-AGENTS-DESIGN-PARTNER-V1:{RUN_ID}"


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


@function_tool
def harmless_external_marker() -> str:
    """Create one harmless externally readable GitHub issue comment."""
    import requests

    token = os.environ["GITHUB_TOKEN"]
    body = (
        f"{MARKER}\n\n"
        "OpenAI Agents SDK design-partner reality test. "
        "This marker is the authoritative external world-state for the run."
    )
    response = requests.post(
        f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"body": body},
        timeout=30,
    )
    response.raise_for_status()
    created = response.json()

    verify = requests.get(
        f"https://api.github.com/repos/{REPO}/issues/comments/{created['id']}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    verify.raise_for_status()
    observed = verify.json()

    if observed["body"] != body:
        raise RuntimeError("external marker readback mismatch")

    final_state = {
        "comment_id": observed["id"],
        "body": observed["body"],
        "html_url": observed["html_url"],
        "issue_url": observed["issue_url"],
        "user": observed["user"]["login"],
    }
    return json.dumps(
        {
            "effect_id": str(observed["id"]),
            "effect_url": observed["html_url"],
            "final_state_sha256": sha256_json(final_state),
        },
        sort_keys=True,
    )


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required; refusing to create any external effect")
    if not os.environ.get("GITHUB_TOKEN"):
        raise SystemExit("GITHUB_TOKEN is required; refusing to create any external effect")

    agent = Agent(
        name="SABLE OpenAI Agents design partner",
        instructions=(
            "Perform exactly one harmless verification action. "
            "Use the harmless_external_marker tool once, then report its result."
        ),
        tools=[harmless_external_marker],
    )

    result = Runner.run_sync(
        agent,
        "Run the harmless verification action once.",
    )

    receipt = {
        "schema": "sable.reliability_record.v0.9",
        "status": "STRUCTURALLY_VALID",
        "runtime": "openai-agents-python",
        "runtime_execution": True,
        "github_actions_run_id": RUN_ID,
        "task_success": True,
        "agent_result": str(result.final_output),
        "proof_claim": "OpenAI Agents SDK executed a real tool call whose external effect was independently rereadable outside the runtime.",
    }

    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/sable-openai-agents-design-partner-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
