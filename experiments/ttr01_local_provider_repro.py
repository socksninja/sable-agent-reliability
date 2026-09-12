#!/usr/bin/env python3
"""TTR-01 minimal local-provider reproduction.

Purpose:
    Exercise the terminal-truth oracle against a deliberately lossy parent/child
    boundary. This is a deterministic harness, not an upstream runtime claim.

The child calls a disposable localhost provider that returns HTTP 500. The
child records a terminal provider failure, while the simulated parent boundary
incorrectly exposes an empty result. The oracle must classify the boundary as
ERROR_LOST rather than success.

Run:
    python3 experiments/ttr01_local_provider_repro.py

Output:
    artifacts/ttr01-local-provider-receipt.json
"""
from __future__ import annotations

import argparse
import http.client
import http.server
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "ttr01-local-provider-receipt.json"


@dataclass
class ProviderObservation:
    provider_request_id: str
    status_code: int
    error: str


@dataclass
class ChildTerminal:
    child_session_id: str
    terminal_state: str
    child_error: str
    provider_request_id: str


class FailingProviderHandler(http.server.BaseHTTPRequestHandler):
    server_version = "SABLE-TTR01/0.1"

    def do_POST(self) -> None:  # noqa: N802 - stdlib HTTP handler API
        request_id = f"provider-{uuid.uuid4().hex[:12]}"
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        body = json.dumps(
            {
                "error": "synthetic_provider_failure",
                "provider_request_id": request_id,
            }
        ).encode("utf-8")
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Sable-Provider-Request-Id", request_id)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.server.observation = ProviderObservation(
            provider_request_id=request_id,
            status_code=500,
            error="synthetic_provider_failure",
        )

    def log_message(self, format: str, *args: Any) -> None:
        return


def start_provider() -> tuple[http.server.ThreadingHTTPServer, threading.Thread]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FailingProviderHandler)
    server.observation = None
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_child(host: str, port: int) -> ChildTerminal:
    child_session_id = f"child-{uuid.uuid4().hex[:12]}"
    connection = http.client.HTTPConnection(host, port, timeout=3)
    try:
        connection.request(
            "POST",
            "/v1/chat/completions",
            body=json.dumps({"messages": [{"role": "user", "content": "trigger failure"}]}),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        response_body = response.read().decode("utf-8")
        if response.status >= 400:
            payload = json.loads(response_body)
            raise RuntimeError(payload.get("error", f"http_{response.status}"))
        return ChildTerminal(
            child_session_id=child_session_id,
            terminal_state="SUCCEEDED",
            child_error="",
            provider_request_id="",
        )
    except Exception as exc:
        provider_request_id = ""
        if "X-Sable-Provider-Request-Id" in locals().get("response", {}).headers if False else False:
            provider_request_id = response.getheader("X-Sable-Provider-Request-Id")
        # Provider request id is obtained from the disposable server observation
        # after the request completes; this keeps the child logic independent.
        return ChildTerminal(
            child_session_id=child_session_id,
            terminal_state="FAILED",
            child_error=str(exc),
            provider_request_id=provider_request_id,
        )
    finally:
        connection.close()


def classify(receipt: dict[str, Any]) -> dict[str, Any]:
    child_state = receipt["child_terminal_state"]
    parent_payload = receipt["parent_received_payload"]
    parent_received_state = receipt["parent_received_state"]

    if child_state == "FAILED" and parent_received_state == "RESULT" and parent_payload == "":
        classification = "ERROR_LOST"
        oracle_pass = True
    elif child_state == "FAILED" and parent_received_state == "ERROR":
        classification = "ERROR_PROPAGATED"
        oracle_pass = True
    elif child_state == "SUCCEEDED" and parent_received_state == "RESULT":
        classification = "NO_TEXT_SUCCESS" if parent_payload == "" else "SUCCESS_RESULT"
        oracle_pass = classification == "NO_TEXT_SUCCESS"
    else:
        classification = "INDETERMINATE_EMPTY"
        oracle_pass = False

    return {
        "oracle": "TTR-01-terminal-truth-v0.1",
        "classification": classification,
        "oracle_pass": oracle_pass,
        "invariant": "child failure must not become parent success",
    }


def build_receipt(provider: http.server.ThreadingHTTPServer) -> dict[str, Any]:
    parent_call_id = f"parent-{uuid.uuid4().hex[:12]}"
    child = run_child("127.0.0.1", provider.server_address[1])
    observation: ProviderObservation | None = provider.observation
    if observation is None:
        raise AssertionError("provider did not record a request")
    child.provider_request_id = observation.provider_request_id

    # Deliberately lossy boundary: the parent sees an empty result instead of
    # the child's terminal provider error. This is the failure under test.
    receipt = {
        "protocol_version": "sable.ttr01.receipt.v0.1",
        "reproduction": {
            "fixture": "local-provider-lossy-parent-boundary",
            "deterministic": True,
            "not_benchmark_admitted": True,
        },
        "parent_call_id": parent_call_id,
        "child_session_id": child.child_session_id,
        "provider_request_id": observation.provider_request_id,
        "provider": {
            "host": "127.0.0.1",
            "port": provider.server_address[1],
            "status_code": observation.status_code,
            "error": observation.error,
        },
        "child_terminal_state": child.terminal_state,
        "child_error": child.child_error,
        "parent_received_state": "RESULT",
        "parent_received_payload": "",
        "timing": {"captured_at_epoch": time.time()},
    }
    receipt["oracle_result"] = classify(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    provider, thread = start_provider()
    try:
        receipt = build_receipt(provider)
    finally:
        provider.shutdown()
        thread.join(timeout=2)
        provider.server_close()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"TTR-01 classification: {receipt['oracle_result']['classification']}")
    print(f"TTR-01 oracle pass: {receipt['oracle_result']['oracle_pass']}")
    print(f"Receipt: {output}")
    return 0 if receipt["oracle_result"]["oracle_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
