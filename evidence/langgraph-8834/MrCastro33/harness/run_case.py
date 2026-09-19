"""Run one bounded LangGraph #8834 verification case in an isolated process.

Each case: build the reported graph, trigger the configured failure, resume from
the same thread/checkpoint, and let the sink write one harmless durable record
into a separate local SQLite effects database. Nothing here reads that effects
database back; the readback is performed by a different process.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import platform
import sqlite3
import sys
import traceback
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    value: int


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _ensure_effects(path: str) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS effects ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, case_id TEXT, "
            "node TEXT, value INTEGER, ts TEXT)"
        )
        conn.commit()
    finally:
        conn.close()


def _record_effect(path: str, run_id: str, case_id: str, value: int) -> None:
    """Durable, harmless, committed write performed only by the sink node."""
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO effects (run_id, case_id, node, value, ts) VALUES (?,?,?,?,?)",
            (run_id, case_id, "sink", value, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def _snapshot(app, config) -> dict:
    snap = app.get_state(config)
    return {
        "values": snap.values,
        "next": list(snap.next),
        "checkpoint_id": snap.config.get("configurable", {}).get("checkpoint_id"),
        "tasks": [
            {
                "name": t.name,
                "error": None if t.error is None else repr(t.error),
                "interrupts": [repr(i) for i in getattr(t, "interrupts", ())],
            }
            for t in snap.tasks
        ],
        "metadata": dict(snap.metadata or {}),
    }


def build(failure_location: str, calls: dict, effects_db: str, run_id: str, case_id: str):
    def node(state: State):
        calls["node"] += 1
        if failure_location == "node" and calls["node"] == 1:
            raise ValueError("temporary node failure")
        return {"value": 1}

    def route(state: State):
        calls["route"] += 1
        if failure_location == "route" and calls["route"] == 1:
            raise ValueError("temporary route failure")
        return "sink"

    def sink(state: State):
        calls["sink"] += 1
        _record_effect(effects_db, run_id, case_id, 2)
        return {"value": 2}

    graph = StateGraph(State)
    graph.add_node("node", node)
    graph.add_node("sink", sink)
    graph.add_edge(START, "node")
    graph.add_conditional_edges("node", route, {"sink": "sink"})
    graph.add_edge("sink", END)
    return graph


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--saver", choices=["memory", "sqlite"], required=True)
    ap.add_argument("--failure", choices=["route", "node", "none"], required=True)
    ap.add_argument("--effects-db", required=True)
    ap.add_argument("--checkpoint-db", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    _ensure_effects(args.effects_db)
    calls = {"node": 0, "route": 0, "sink": 0}
    thread_id = args.case_id
    config = {"configurable": {"thread_id": thread_id}}

    record = {
        "case_id": args.case_id,
        "run_id": args.run_id,
        "saver": args.saver,
        "failure_location": args.failure,
        "thread_id": thread_id,
        "effects_db": args.effects_db,
        "checkpoint_db": args.checkpoint_db if args.saver == "sqlite" else None,
        "started_at": _now(),
        "python": sys.version,
        "platform": platform.platform(),
    }

    graph = build(args.failure, calls, args.effects_db, args.run_id, args.case_id)
    conn = None
    try:
        if args.saver == "sqlite":
            conn = sqlite3.connect(args.checkpoint_db, check_same_thread=False)
            saver = SqliteSaver(conn)
        else:
            saver = InMemorySaver()
        app = graph.compile(checkpointer=saver)

        record["first_invocation"] = {}
        try:
            first_result = app.invoke({"value": 0}, config)
            record["first_invocation"] = {"raised": False, "result": first_result}
        except Exception as exc:  # noqa: BLE001 - we deliberately record any failure
            record["first_invocation"] = {
                "raised": True,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        record["calls_after_first"] = dict(calls)
        record["state_before_resume"] = _snapshot(app, config)

        record["resume"] = {}
        try:
            resumed = app.invoke(None, config)
            record["resume"] = {"raised": False, "result": resumed}
        except Exception as exc:  # noqa: BLE001
            record["resume"] = {
                "raised": True,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        record["calls_after_resume"] = dict(calls)
        record["state_after_resume"] = _snapshot(app, config)
        record["status"] = "ok"
    except Exception:  # noqa: BLE001
        record["status"] = "harness_error"
        record["traceback"] = traceback.format_exc()
    finally:
        if conn is not None:
            conn.commit()
            conn.close()
        record["finished_at"] = _now()
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, sort_keys=True, default=str)

    print(json.dumps({"case_id": args.case_id, "status": record["status"],
                      "calls": record.get("calls_after_resume"),
                      "resume": record.get("resume")}, sort_keys=True, default=str))
    return 0 if record["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
