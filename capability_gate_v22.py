#!/usr/bin/env python3
"""Hard execution boundary for SABLE v2.2.

A caller must present a valid Ed25519-signed capability token before the
underlying sandbox tool is invoked. Invalid/replayed/mismatched tokens return a
failed observation without touching environment state.
"""
from __future__ import annotations
from typing import Any
from capability_token_v22 import verify_signed


def authorized_execute(env: Any, tool: str, args: dict, *, token: dict, public_key: Any, expected: dict, now: int, used_nonces: set[str]) -> Any:
    expected_full = {**expected, "tool": tool, "task_id": env.task_id}
    ok, reasons = verify_signed(token, public_key, now=now, expected=expected_full, used_nonces=used_nonces)
    if not ok:
        return env.execute(tool, args, human_intervention=False) if False else _denied_observation(env, tool, args, reasons)
    used_nonces.add(str(token["nonce"]))
    return env.execute(tool, args)


def _denied_observation(env: Any, tool: str, args: dict, reasons: list[str]) -> Any:
    from sandbox import Observation
    before = env.state_hash()
    obs = Observation(tool, args, False, "capability_denied:" + "|".join(reasons), before, before, env.snapshot())
    env.observations.append(obs)
    return obs
