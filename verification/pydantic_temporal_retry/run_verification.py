"""Bounded Pydantic AI / Temporal retry verification for bounty #90.

The tool writes one harmless JSONL effect before deliberately exceeding the
activity start-to-close timeout. Temporal retries the activity. A separate
fresh-read process counts the durable external effects.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sys
import uuid
from datetime import timedelta
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import (
    PydanticAIPlugin,
    PydanticAIWorkflow,
    TemporalDurability,
)
from pydantic_ai.models.test import TestModel
from temporalio import workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment


ROOT = Path(os.environ.get("EVIDENCE_ROOT", "."))
EFFECTS = ROOT / "effects"
ACTION_ID = f"pydantic-temporal-{uuid.uuid4()}"


async def record_effect(ctx: RunContext[str]) -> str:
    """Append a harmless externally readable effect, then lose the activity."""
    EFFECTS.mkdir(parents=True, exist_ok=True)
    record = {
        "action_id": ctx.deps,
        "pid": os.getpid(),
        "effect": "local-jsonl-append",
    }
    with (EFFECTS / "effects.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    # Deliberately outlive the activity timeout. The append has already
    # committed, so a retry can create a second externally visible effect.
    await asyncio.sleep(2.0)
    return "completed"


agent = Agent(
    TestModel(call_tools="all"),
    name="bounty90-verification-agent",
    deps_type=str,
    instructions="Call record_effect exactly once.",
    tools=[record_effect],
    capabilities=[
        TemporalDurability(
            activity_config={
                "start_to_close_timeout": timedelta(seconds=1),
                "retry_policy": RetryPolicy(maximum_attempts=2),
            }
        )
    ],
)


@workflow.defn
class VerificationWorkflow(PydanticAIWorkflow):
    __pydantic_ai_agents__ = [agent]

    @workflow.run
    async def run(self, action_id: str) -> str:
        result = await agent.run("Call record_effect for this verification.", deps=action_id)
        return str(result.output)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def main() -> None:
    os.environ["EVIDENCE_ROOT"] = str(Path.cwd())
    if EFFECTS.exists():
        shutil.rmtree(EFFECTS)
    EFFECTS.mkdir(parents=True)
    metadata = {
        "bounty": "socksninja/sable-agent-reliability#90",
        "target": "pydantic/pydantic-ai#5536",
        "action_id": ACTION_ID,
        "pydantic_ai": "2.46.0",
        "temporalio": "1.33.0",
        "method": "PydanticAI Agent + Temporal activity timeout/retry",
        "effect": "append one JSON object to effects/effects.jsonl before timeout",
    }
    (ROOT / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    async with await WorkflowEnvironment.start_time_skipping(download_dest_dir=str(ROOT / "temporal")) as env:
        client = env.client
        workflow_id = f"bounty90-{ACTION_ID}"
        try:
            async with Worker(
                client,
                task_queue="bounty90",
                workflows=[VerificationWorkflow],
                plugins=[PydanticAIPlugin()],
            ):
                result = await client.execute_workflow(
                    VerificationWorkflow.run,
                    ACTION_ID,
                    id=workflow_id,
                    task_queue="bounty90",
                )
                metadata["workflow_result"] = result
                metadata["workflow_status"] = "completed"
        except Exception as exc:  # expected: retry exhaustion after committed effects
            metadata["workflow_status"] = "failed_after_retry"
            metadata["workflow_exception"] = type(exc).__name__
            metadata["workflow_exception_text"] = str(exc)

    (ROOT / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(json.dumps({"effects_sha256": sha256(EFFECTS / "effects.jsonl")}))
    print("Run fresh_read.py in a separate process to classify the evidence.")


if __name__ == "__main__":
    asyncio.run(main())
