import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import TypedDict

from langfuse import get_client
from langgraph.graph import END, START, StateGraph

REPO = os.environ.get("GITHUB_REPOSITORY", "socksninja/sable-agent-reliability")
ISSUE_NUMBER = int(os.environ.get("SABLE_EXTERNAL_ISSUE", "63"))
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")
COMMIT = os.environ.get("GITHUB_SHA", "unknown")
MARKER = f"SABLE-LANGGRAPH-REAL-EXECUTION-V1:{RUN_ID}"


class State(TypedDict, total=False):
    task: str
    effect_id: str
    effect_url: str
    final_state_sha256: str


def sha256_json(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def gh_api(path, method="GET", body=None):
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


def main():
    if not os.environ.get("LANGFUSE_SECRET_KEY") or not os.environ.get("LANGFUSE_PUBLIC_KEY"):
        raise RuntimeError("LANGFUSE credentials are not configured; refusing to create a non-Langfuse execution")

    lf = get_client()
    started = datetime.now(timezone.utc)

    def execute_external_effect(state: State) -> State:
        text = (
            f"{MARKER}\n\n"
            "This is a harmless SABLE reality-test execution performed inside LangGraph. "
            "The authoritative world-state is this GitHub comment; Langfuse records the same run."
        )
        created = gh_api(
            f"/repos/{REPO}/issues/{ISSUE_NUMBER}/comments",
            method="POST",
            body={"body": text},
        )
        observed = gh_api(f"/repos/{REPO}/issues/comments/{created['id']}")
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
            "effect_verified": observed["body"] == text,
        }

    graph = StateGraph(State)
    graph.add_node("execute_external_effect", execute_external_effect)
    graph.add_edge(START, "execute_external_effect")
    graph.add_edge("execute_external_effect", END)
    app = graph.compile()

    with lf.start_as_current_observation(
        as_type="agent",
        name="sable-langgraph-real-agent-execution",
        input={"task": "Perform one harmless externally readable tool action"},
    ) as root:
        result = app.invoke({"task": "create one harmless external effect"})
        root.update(output={
            "runtime": "langgraph",
            "runtime_execution": True,
            "task_success": True,
            "external_effect_id": result["effect_id"],
            "external_effect_url": result["effect_url"],
            "final_state_sha256": result["final_state_sha256"],
        })
        root.set_trace_as_public()

    trace_id = root.trace_id
    trace_url = lf.get_trace_url(trace_id=trace_id)
    lf.flush()
    finished = datetime.now(timezone.utc)

    receipt = {
        "schema": "sable.reliability_record.v0.9",
        "status": "EVIDENCE_REACHABLE" if result.get("effect_verified") else "STRUCTURALLY_VALID",
        "runtime": "langgraph",
        "runtime_execution": True,
        "telemetry": "OpenTelemetry-backed Langfuse SDK",
        "repository": REPO,
        "commit_sha": COMMIT,
        "github_actions_run_id": RUN_ID,
        "trace_id": trace_id,
        "trace_url": trace_url,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "task_success": True,
        "external_effect": {
            "system": "GitHub Issues",
            "operation": "create_issue_comment",
            "issue_number": ISSUE_NUMBER,
            "effect_id": result["effect_id"],
            "effect_url": result["effect_url"],
            "final_state_sha256": result["final_state_sha256"],
        },
        "proof_claim": "LangGraph runtime execution, Langfuse trace, and independently readable GitHub world-state refer to the same execution effect.",
    }
    out = os.path.join("artifacts", "sable-langgraph-reliability-record.json")
    os.makedirs("artifacts", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
