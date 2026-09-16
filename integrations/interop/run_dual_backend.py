from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sha256_json(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


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


class State(TypedDict, total=False):
    execution_id: str
    task: str
    effect_id: str
    effect_url: str
    final_state_sha256: str
    task_success: bool


def main() -> None:
    required = [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "GITHUB_TOKEN",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"dual-backend probe requires both observability backends: {', '.join(missing)}")

    from langfuse import get_client
    from langgraph.graph import END, START, StateGraph
    from langsmith import Client

    repo = os.environ.get("GITHUB_REPOSITORY", "socksninja/sable-agent-reliability")
    issue = int(os.environ.get("SABLE_EXTERNAL_ISSUE", "63"))
    actions_run_id = os.environ.get("GITHUB_RUN_ID", "local")
    execution_id = f"sable-dual-backend:{actions_run_id}:{uuid4()}"

    langsmith_client = Client()
    langsmith_run_id = uuid4()
    langsmith_client.create_run(
        id=langsmith_run_id,
        name="sable-dual-backend-same-execution",
        run_type="chain",
        inputs={"execution_id": execution_id, "runtime": "langgraph"},
        project_name=os.environ["LANGSMITH_PROJECT"],
        extra={"metadata": {"sable_execution_id": execution_id}},
    )

    langfuse_client = get_client()
    started = now_utc()

    def execute_effect(state: State) -> State:
        marker = f"SABLE-DUAL-BACKEND-SAME-EXECUTION:{execution_id}"
        body = {
            "body": (
                f"{marker}\n\n"
                "One harmless LangGraph invocation is being observed by both Langfuse and LangSmith."
            )
        }
        created = gh_api(
            f"/repos/{repo}/issues/{issue}/comments",
            method="POST",
            body=body,
        )
        observed = gh_api(f"/repos/{repo}/issues/comments/{created['id']}")
        final_state = {
            "comment_id": observed["id"],
            "body": observed["body"],
            "html_url": observed["html_url"],
            "issue_url": observed["issue_url"],
            "user": observed["user"]["login"],
        }
        return {
            **state,
            "effect_id": str(observed["id"]),
            "effect_url": observed["html_url"],
            "final_state_sha256": sha256_json(final_state),
            "task_success": observed["body"] == body["body"],
        }

    graph = StateGraph(State)
    graph.add_node("external_effect", execute_effect)
    graph.add_edge(START, "external_effect")
    graph.add_edge("external_effect", END)
    app = graph.compile()

    try:
        with langfuse_client.start_as_current_observation(
            as_type="agent",
            name="sable-dual-backend-same-execution",
            input={"execution_id": execution_id, "task": "perform one harmless externally readable action"},
        ) as langfuse_root:
            result = app.invoke({
                "execution_id": execution_id,
                "task": "create one harmless external effect",
            })
            langfuse_root.update(
                output={
                    "execution_id": execution_id,
                    "runtime": "langgraph",
                    "task_success": result["task_success"],
                    "external_effect_id": result["effect_id"],
                    "final_state_sha256": result["final_state_sha256"],
                }
            )
            langfuse_root.set_trace_as_public()

        langsmith_client.update_run(
            langsmith_run_id,
            outputs={
                "execution_id": execution_id,
                "task_success": result["task_success"],
                "external_effect_id": result["effect_id"],
                "final_state_sha256": result["final_state_sha256"],
            },
            end_time=now_utc(),
        )
    except Exception as exc:
        langsmith_client.update_run(langsmith_run_id, error=str(exc), end_time=now_utc())
        raise

    langfuse_client.flush()
    finished = now_utc()
    trace_id = langfuse_root.trace_id
    try:
        langfuse_trace_url = langfuse_client.get_trace_url(trace_id=trace_id)
    except Exception:
        langfuse_trace_url = None
    try:
        langsmith_run_url = langsmith_client.get_run_url(run_id=langsmith_run_id)
    except Exception:
        langsmith_run_url = None

    # The authoritative external state was read back by the same execution immediately after creation.
    # Re-read once more after both observability writes to test cross-backend stability.
    reread = gh_api(f"/repos/{repo}/issues/comments/{result['effect_id']}")
    reread_state = {
        "comment_id": reread["id"],
        "body": reread["body"],
        "html_url": reread["html_url"],
        "issue_url": reread["issue_url"],
        "user": reread["user"]["login"],
    }
    reread_hash = sha256_json(reread_state)
    same_effect = str(reread["id"]) == result["effect_id"]
    same_hash = reread_hash == result["final_state_sha256"]

    receipt = {
        "schema": "sable.reliability_record.v0.9",
        "status": "EVIDENCE_REACHABLE" if (result["task_success"] and same_effect and same_hash) else "STRUCTURALLY_VALID",
        "execution_id": execution_id,
        "runtime": "langgraph",
        "github_actions_run_id": actions_run_id,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "task_success": result["task_success"],
        "observability": {
            "langfuse": {
                "trace_id": trace_id,
                "trace_url": langfuse_trace_url,
            },
            "langsmith": {
                "run_id": str(langsmith_run_id),
                "run_url": langsmith_run_url,
            },
        },
        "external_effect": {
            "system": "GitHub Issues",
            "operation": "create_issue_comment",
            "effect_id": result["effect_id"],
            "effect_url": result["effect_url"],
            "final_state_sha256": result["final_state_sha256"],
        },
        "independent_readback": {
            "effect_id_matches": same_effect,
            "final_state_sha256_matches": same_hash,
            "readback_sha256": reread_hash,
        },
        "proof_claim": "A single LangGraph invocation is bound to one execution_id and one independently readable GitHub effect while both Langfuse and LangSmith emit separately addressable evidence.",
    }

    out = Path("artifacts")
    out.mkdir(exist_ok=True)
    (out / "sable-dual-backend-same-execution.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
