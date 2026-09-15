import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from langfuse import get_client, propagate_attributes

REPO = os.environ.get("GITHUB_REPOSITORY", "socksninja/sable-agent-reliability")
ISSUE_NUMBER = int(os.environ.get("SABLE_EXTERNAL_ISSUE", "63"))
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")
COMMIT = os.environ.get("GITHUB_SHA", "unknown")
MARKER = f"SABLE-LANGFUSE-REAL-EXECUTION-V1:{RUN_ID}"


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
    trace_seed = f"sable-langfuse-real-execution:{REPO}:{RUN_ID}:{COMMIT}"
    trace_id = lf.create_trace_id(seed=trace_seed)
    tool_input = {
        "repository": REPO,
        "issue_number": ISSUE_NUMBER,
        "marker": MARKER,
        "operation": "create_issue_comment",
    }

    with lf.start_as_current_observation(
        as_type="span",
        name="sable-real-agent-execution",
        input={"task": "Perform one harmless externally readable tool action"},
        trace_context={"trace_id": trace_id},
    ) as root:
        with propagate_attributes(
            trace_name="sable-real-agent-execution",
            session_id=f"github-actions:{RUN_ID}",
            metadata={"runtime": "github-actions", "proof_layer": "sable", "commit": COMMIT},
            tags=["sable", "langfuse", "external-effect", "otel"],
        ):
            effect_text = (
                f"{MARKER}\n\n"
                "This is a harmless SABLE reality-test execution. "
                "The authoritative world-state is this GitHub comment; "
                "the Langfuse trace records the same execution."
            )
            with lf.start_as_current_observation(
                as_type="span",
                name="github-tool:create-issue-comment",
                input=tool_input,
            ) as tool_span:
                created = gh_api(
                    f"/repos/{REPO}/issues/{ISSUE_NUMBER}/comments",
                    method="POST",
                    body={"body": effect_text},
                )
                comment_id = created["id"]
                comment_url = created["html_url"]
                tool_span.update(output={"comment_id": comment_id, "comment_url": comment_url})

            observed = gh_api(f"/repos/{REPO}/issues/comments/{comment_id}")
            final_state = {
                "comment_id": observed["id"],
                "body": observed["body"],
                "html_url": observed["html_url"],
                "issue_url": observed["issue_url"],
                "user": observed["user"]["login"],
            }
            final_state_hash = sha256_json(final_state)
            root.update(output={
                "task_success": True,
                "effect_verified": observed["body"] == effect_text,
                "external_effect_id": str(comment_id),
                "external_effect_url": comment_url,
                "final_state_sha256": final_state_hash,
            })
            root.set_trace_as_public()

    lf.flush()
    finished = datetime.now(timezone.utc)
    receipt = {
        "schema": "sable.reliability_record.v0.9",
        "status": "EVIDENCE_REACHABLE",
        "runtime": "langfuse-python-sdk-v4",
        "telemetry": "OpenTelemetry-backed Langfuse SDK",
        "repository": REPO,
        "commit_sha": COMMIT,
        "github_actions_run_id": RUN_ID,
        "trace_id": trace_id,
        "trace_url": lf.get_trace_url(trace_id=trace_id),
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "task_success": True,
        "external_effect": {
            "system": "GitHub Issues",
            "operation": "create_issue_comment",
            "issue_number": ISSUE_NUMBER,
            "effect_id": str(observed["id"]),
            "effect_url": observed["html_url"],
            "final_state_sha256": final_state_hash,
        },
        "input_sha256": sha256_json(tool_input),
        "proof_claim": "Langfuse trace and independently readable GitHub world-state refer to the same execution effect.",
    }
    out = Path("artifacts")
    out.mkdir(parents=True, exist_ok=True)
    (out / "sable-langfuse-reliability-record.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
