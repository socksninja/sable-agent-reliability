from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def gh_api(path: str, method: str = "GET", body: dict | None = None):
    token = os.environ["GITHUB_TOKEN"]
    cmd = [
        "curl", "-fsS", "-X", method,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
    ]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd.append(f"https://api.github.com{path}")
    return json.loads(subprocess.check_output(cmd, text=True))


def sha256_json(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def main() -> None:
    required = ["LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "GITHUB_TOKEN"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"LangSmith credentials/config missing; refusing blind execution: {', '.join(missing)}")
    if os.environ.get("LANGSMITH_TRACING", "true").lower() != "true":
        raise RuntimeError("LANGSMITH_TRACING must be true for the second-backend reality test")

    issue = int(os.environ.get("SABLE_EXTERNAL_ISSUE", "63"))
    repo = os.environ.get("GITHUB_REPOSITORY", "socksninja/sable-agent-reliability")
    marker = f"SABLE-LANGSMITH-SECOND-BACKEND:{os.environ.get('GITHUB_RUN_ID', 'local')}"
    project = os.environ["LANGSMITH_PROJECT"]

    try:
        from langgraph.graph import END, START, StateGraph
        from langsmith import Client
        from typing_extensions import TypedDict
    except ImportError as exc:
        raise RuntimeError("langgraph and langsmith are required for the LangSmith second-backend probe") from exc

    # Explicit LangSmith run: independently addressable observability evidence.
    langsmith_client = Client()
    langsmith_run_id = uuid4()
    langsmith_client.create_run(
        id=langsmith_run_id,
        name=marker,
        run_type="chain",
        inputs={"marker": marker, "runtime": "langgraph"},
        project_name=project,
        extra={"metadata": {"sable_workflow_run_id": os.environ.get("GITHUB_RUN_ID", "local")}},
    )

    class State(TypedDict):
        marker: str
        comment_id: str
        task_success: bool

    def action(state: State):
        body = {
            "body": marker + "\n\nLangSmith second-backend SABLE reality test."
        }
        created = gh_api(f"/repos/{repo}/issues/{issue}/comments", method="POST", body=body)
        return {"comment_id": str(created["id"]), "task_success": True}

    graph = StateGraph(State)
    graph.add_node("external_effect", action)
    graph.add_edge(START, "external_effect")
    graph.add_edge("external_effect", END)
    app = graph.compile()

    try:
        result = app.invoke({"marker": marker, "comment_id": "", "task_success": False})
    except Exception as exc:
        langsmith_client.update_run(langsmith_run_id, error=str(exc), end_time=now_utc())
        raise

    comment_id = result["comment_id"]
    observed = gh_api(f"/repos/{repo}/issues/comments/{comment_id}")
    final_state = {
        "comment_id": observed["id"],
        "body": observed["body"],
        "html_url": observed["html_url"],
        "issue_url": observed["issue_url"],
        "user": observed["user"]["login"],
    }
    verified = observed["body"].startswith(marker)
    if not verified:
        langsmith_client.update_run(
            langsmith_run_id,
            error="external effect verification failed",
            end_time=now_utc(),
        )
        raise RuntimeError("external effect verification failed")

    langsmith_client.update_run(
        langsmith_run_id,
        outputs={"task_success": True, "external_effect_id": comment_id},
        end_time=now_utc(),
    )
    recorded = langsmith_client.read_run(langsmith_run_id)
    if recorded.id != langsmith_run_id:
        raise RuntimeError("LangSmith run could not be independently read back")

    try:
        langsmith_run_url = langsmith_client.get_run_url(run_id=langsmith_run_id)
    except Exception:
        langsmith_run_url = None

    receipt = {
        "schema": "sable.reliability_record.v0.9",
        "status": "EVIDENCE_REACHABLE",
        "runtime": "langgraph",
        "observability_backend": "langsmith",
        "langsmith_project": project,
        "langsmith_run_id": str(langsmith_run_id),
        "langsmith_run_url": langsmith_run_url,
        "langsmith_readback": True,
        "github_actions_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "task_success": bool(result["task_success"]),
        "external_effect": {
            "system": "GitHub Issues",
            "operation": "create_issue_comment",
            "effect_id": comment_id,
            "effect_url": observed["html_url"],
            "final_state_sha256": sha256_json(final_state),
        },
        "proof_claim": "LangGraph execution was traced with LangSmith and the LangSmith run itself was independently read back, alongside an independently readable GitHub effect.",
    }
    out = Path("artifacts")
    out.mkdir(exist_ok=True)
    (out / "sable-langsmith-second-backend-record.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
