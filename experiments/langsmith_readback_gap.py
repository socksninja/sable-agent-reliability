from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from langsmith import Client


READ_DELAYS_SECONDS = [0, 1, 2, 5, 10, 30]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    project = os.environ["LANGSMITH_PROJECT"]
    workflow_run_id = os.environ.get("GITHUB_RUN_ID", "local")
    client = Client()
    project_record = client.read_project(project_name=project)
    project_id = str(project_record.id)
    run_id = uuid4()
    name = f"SABLE-LANGSMITH-READBACK-GAP:{workflow_run_id}"

    write_started = now_iso()
    client.create_run(
        id=run_id,
        name=name,
        run_type="chain",
        inputs={"experiment": "langsmith_single_run_readback_gap", "workflow_run_id": workflow_run_id},
        project_name=project,
        extra={
            "metadata": {
                "sable_experiment": "langsmith_readback_gap_v0.1",
                "read_delays_seconds": READ_DELAYS_SECONDS,
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
    for delay in READ_DELAYS_SECONDS:
        if delay:
            time.sleep(delay)
        observed_at = now_iso()
        try:
            recorded = client.runs.retrieve(run_id, project_id=project_id)
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

    final = {
        "schema": "sable.experiment.langsmith_readback_gap.v0.1",
        "status": "PASS" if observations and observations[-1]["result"] == "READBACK_OK" else "READBACK_NOT_OBSERVED",
        "experiment": "langsmith_readback_gap_v0.1",
        "langsmith_project": project,
        "langsmith_project_id": project_id,
        "langsmith_run_id": str(run_id),
        "langsmith_run_url": None,
        "workflow_run_id": workflow_run_id,
        "write_started": write_started,
        "write_accepted_at": write_accepted_at,
        "update_accepted_at": update_accepted_at,
        "read_schedule_seconds": READ_DELAYS_SECONDS,
        "observations": observations,
        "readback_success": any(x["result"] == "READBACK_OK" for x in observations),
        "first_readback_success_delay_seconds": next(
            (x["delay_seconds"] for x in observations if x["result"] == "READBACK_OK"), None
        ),
        "interpretation": (
            "WRITE_ACCEPTED_WITHOUT_READBACK_WITHIN_SCHEDULE"
            if not any(x["result"] == "READBACK_OK" for x in observations)
            else "READBACK_EVENTUALLY_AVAILABLE"
        ),
    }
    try:
        final["langsmith_run_url"] = client.get_run_url(run_id=run_id)
    except Exception:
        pass

    out = Path("artifacts")
    out.mkdir(parents=True, exist_ok=True)
    (out / "langsmith-readback-gap-experiment.json").write_text(
        json.dumps(final, indent=2), encoding="utf-8"
    )
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
