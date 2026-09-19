"""Fresh-process external readback of the downstream effect.

This process never executes the graph. It opens the effects database that the
sink node writes to, and (for SQLite checkpoint cases) re-opens the persisted
checkpoint from disk to read the recorded thread state independently of the
runtime process that produced it.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sqlite3
import sys
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    value: int


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def read_effects(effects_db: str, case_id: str) -> dict:
    if not os.path.exists(effects_db):
        return {"effects_db_exists": False, "rows": [], "sink_effect_rows": 0}
    conn = sqlite3.connect(f"file:{effects_db}?mode=ro", uri=True)
    try:
        cur = conn.execute(
            "SELECT id, run_id, case_id, node, value, ts FROM effects WHERE case_id = ? ORDER BY id",
            (case_id,),
        )
        rows = [
            {"id": r[0], "run_id": r[1], "case_id": r[2], "node": r[3], "value": r[4], "ts": r[5]}
            for r in cur.fetchall()
        ]
        total = conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    finally:
        conn.close()
    return {
        "effects_db_exists": True,
        "rows": rows,
        "sink_effect_rows": len(rows),
        "total_rows_all_cases": total,
        "observed_value": rows[-1]["value"] if rows else None,
    }


def read_checkpoint(checkpoint_db: str, thread_id: str) -> dict:
    """Re-open the persisted checkpoint from a process that never ran the graph."""
    if not checkpoint_db or not os.path.exists(checkpoint_db):
        return {"checkpoint_db_exists": False}

    def noop(state: State):
        raise AssertionError("readback process must never execute graph nodes")

    def route(state: State):
        raise AssertionError("readback process must never execute graph nodes")

    graph = StateGraph(State)
    graph.add_node("node", noop)
    graph.add_node("sink", noop)
    graph.add_edge(START, "node")
    graph.add_conditional_edges("node", route, {"sink": "sink"})
    graph.add_edge("sink", END)

    conn = sqlite3.connect(checkpoint_db, check_same_thread=False)
    try:
        app = graph.compile(checkpointer=SqliteSaver(conn))
        config = {"configurable": {"thread_id": thread_id}}
        snap = app.get_state(config)
        history = [
            {
                "checkpoint_id": h.config.get("configurable", {}).get("checkpoint_id"),
                "values": h.values,
                "next": list(h.next),
                "source": (h.metadata or {}).get("source"),
                "step": (h.metadata or {}).get("step"),
            }
            for h in app.get_state_history(config)
        ]
        return {
            "checkpoint_db_exists": True,
            "values": snap.values,
            "next": list(snap.next),
            "checkpoint_id": snap.config.get("configurable", {}).get("checkpoint_id"),
            "history_len": len(history),
            "history": history,
        }
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--thread-id", required=True)
    ap.add_argument("--effects-db", required=True)
    ap.add_argument("--checkpoint-db", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = {
        "case_id": args.case_id,
        "thread_id": args.thread_id,
        "read_at": _now(),
        "reader_pid": os.getpid(),
        "reader_python": sys.version,
        "effects": read_effects(args.effects_db, args.case_id),
        "checkpoint": read_checkpoint(args.checkpoint_db, args.thread_id),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=str)
    print(json.dumps({"case_id": args.case_id,
                      "sink_effect_rows": payload["effects"]["sink_effect_rows"],
                      "checkpoint_values": payload["checkpoint"].get("values")},
                     sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
