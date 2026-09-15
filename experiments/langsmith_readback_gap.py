from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from langsmith import Client


READ_DELAYS_SECONDS = [0, 1, 2, 5, 10, 30]
REPETITIONS = int(os.environ.get("SABLE_READBACK_REPETITIONS", "3"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_one(client: Client, project: str, project_id: str, workflow_run_id: str, repetition: int) -> dict:
    run_id = uuid4()
    name = f"SABLE-LANGSMITH-READBACK-GAP:{workflow_run_id}:{repetition}"

    write_started = now_iso()
    client.create_run(
        id=run_id,
        name=name,
        run_type="chain",
        inputs={
            "experiment": "langsmith_single_run_readback_gap",
            "workflow_run_id": workflow_run_id,
            "repetition": repetition,
        },
        project_name=project,
        extra={
            "metadata": {
                "sable_experiment": "langsmith_readback_gap_v0.2",
                "read_delays_seconds": READ_DELAYS_SECONDS,
                "repetition": repetition,
            }
        },
    )
    write_accepted_at = now_iso()

    client.update_run(
        run_id,
        outputs={"write_accepted": True, "experiment": "langsmith_single_run_readback_gap"},
        end_time=datetime.now(timezone.utc),
    )
    update_accepted_at = now_iso()

    observations: list[dict] = []
    api = client._get_langsmith_api_sync()
    for delay in READ_DELAYS_SECONDS:
        if delay:
            time.sleep(delay)
        observed_at = now_iso()
        try:
            recorded = api.runs.retrieve_v2(
                run_id=str(run_id),
                project_id=project_id,
                selects=["ID"],
            )
            observations.append(
                {
                    "delay_seconds": delay,
                    "observed_at": observed_at,
                    "result": "READBACK_OK",
                    "observed_run_id": str(recorded.id),
                }
            )
            break
        except Exception as exc:
            observations.append(
                {
                    "delay_seconds": delay,
                    "observed_at": observed_at,
                    "result": "READBACK_404_OR_ERROR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    success_delay = next(
        (x["delay_seconds"] for x in observations if x["result"] == "READBACK_OK"), None
    )
    return {
        "repetition": repetition,
        "langsmith_run_id": str(run_id),
        "write_started": write_started,
        "write_accepted_at": write_accepted_at,
        "update_accepted_at": update_accepted_at,
        "observations": observations,
        "readback_success": success_delay is not None,
        "first_readback_success_delay_seconds": success_delay,
        "interpretation": (
            "READBACK_EVENTUALLY_AVAILABLE"
            if success_delay is not None
            else "WRITE_ACCEPTED_WITHOUT_READBACK_WITHIN_SCHEDULE"
        ),
    }


def main() -> None:
    project = os.environ["LANGSMITH_PROJECT"]
    workflow_run_id = os.environ.get("GITHUB_RUN_ID", "local")
    client = Client()
    project_record = client.read_project(project_name=project)
    project_id = str(project_record.id)

    repetitions = [run_one(client, project, project_id, workflow_run_id, i) for i in range(1, REPETITIONS + 1)]
    success_delays = [r["first_readback_success_delay_seconds"] for r in repetitions if r["readback_success"]]
    final = {
        "schema": "sable.experiment.langsmith_readback_gap.v0.2",
        "experiment": "langsmith_readback_gap_v0.2",
        "langsmith_project": project,
        "langsmith_project_id": project_id,
        "workflow_run_id": workflow_run_id,
        "repetitions_requested": REPETITIONS,
        "repetitions_completed": len(repetitions),
        "read_schedule_seconds": READ_DELAYS_SECONDS,
        "results": repetitions,
        "summary": {
            "readback_success_count": len(success_delays),
            "readback_success_rate": len(success_delays) / len(repetitions) if repetitions else 0,
            "first_success_delays_seconds": success_delays,
            "min_success_delay_seconds": min(success_delays) if success_delays else None,
            "max_success_delay_seconds": max(success_delays) if success_delays else None,
        },
    }

    out = Path("artifacts")
    out.mkdir(parents=True, exist_ok=True)
    (out / "langsmith-readback-gap-experiment.json").write_text(
        json.dumps(final, indent=2), encoding="utf-8"
    )
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
