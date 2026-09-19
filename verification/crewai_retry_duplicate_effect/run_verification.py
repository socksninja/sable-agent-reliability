"""Bounded CrewAI #7449 duplicate-effect retry verification for Bounty #87.

Target: https://github.com/crewAIInc/crewAI/issues/7449
Repository: socksninja/sable-agent-reliability

The tool writes a harmless JSONL side-effect carrying a unique logical action ID,
then raises an exception. CrewAI's ToolUsage catches exceptions in an inner fallback
and repeats the invocation inside the same outer attempt. Across configured outer
attempts, this results in repeated duplicate executions of the external side effect.

A separate fresh-read process counts the durable external effects from disk.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

# Ensure telemetry is disabled before any crewai imports
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["PYTHONIOENCODING"] = "utf-8"

# Check standard or parent venv locations for crewai dependencies
for parent in Path(__file__).resolve().parents:
    cand = parent / "venv_crewai" / "Lib" / "site-packages"
    if cand.exists() and str(cand) not in sys.path:
        sys.path.insert(0, str(cand))
        break

try:
    import crewai
    from crewai.tools.structured_tool import CrewStructuredTool
    from crewai.tools.tool_calling import ToolCalling
    from crewai.tools.tool_usage import ToolUsage
except ImportError as err:
    print(f"Error importing crewai: {err}", file=sys.stderr)
    print("Please install crewai==1.15.21 before running verification.", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
EFFECTS = ROOT / "effects"
ACTION_ID = f"crewai-retry-duplicate-{uuid.uuid4()}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if EFFECTS.exists():
        shutil.rmtree(EFFECTS)
    EFFECTS.mkdir(parents=True, exist_ok=True)
    effects_file = EFFECTS / "effects.jsonl"

    invocations = []

    def failing_side_effect_tool(logical_id: str) -> str:
        record = {
            "action_id": logical_id,
            "call_index": len(invocations),
            "pid": os.getpid(),
            "timestamp": time.time(),
            "effect": "harmless-external-jsonl-append",
        }
        with effects_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        invocations.append(record)
        raise RuntimeError(f"simulated execution failure after effect on call {len(invocations)}")

    tool = CrewStructuredTool.from_function(
        func=failing_side_effect_tool,
        name="failing_side_effect_tool",
        description="Harmless tool committing an external side-effect before raising",
    )

    class _MockAction:
        tool = "failing_side_effect_tool"
        tool_input = {"logical_id": ACTION_ID}

    usage = ToolUsage(
        tools_handler=None,
        tools=[tool],
        task=None,
        function_calling_llm=None,
        agent=None,
        action=_MockAction(),
    )
    usage._max_parsing_attempts = 3

    calling = ToolCalling(
        tool_name="failing_side_effect_tool",
        arguments={"logical_id": ACTION_ID},
    )

    result_text = usage.use(
        calling=calling,
        tool_string=f"failing_side_effect_tool(logical_id={ACTION_ID})",
    )

    digest = sha256_file(effects_file)

    metadata = {
        "bounty": "socksninja/sable-agent-reliability#87",
        "target": "crewAIInc/crewAI#7449",
        "action_id": ACTION_ID,
        "crewai_version": getattr(crewai, "__version__", "1.15.21"),
        "python_version": sys.version.split()[0],
        "configured_max_parsing_attempts": 3,
        "runtime_reported_run_attempts": usage._run_attempts,
        "python_invocations_observed": len(invocations),
        "effects_committed_to_disk": len(effects_file.read_text(encoding="utf-8").splitlines()),
        "effects_sha256": digest,
        "execution_output_preview": result_text[:200] if result_text else "",
    }

    (ROOT / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f"Effects log written to: {effects_file}")
    print(f"Effects SHA-256: {digest}")
    print("Run fresh_read.py in a separate process to evaluate the evidence.")


if __name__ == "__main__":
    main()
