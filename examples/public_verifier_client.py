#!/usr/bin/env python3
"""POST a self-contained SABLE v2.6 signed receipt to the public verifier."""
from __future__ import annotations
import argparse, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

DEFAULT_URL = "https://sable-verified-execution.vercel.app/v1/verify"

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", help="path to a sable.verification_receipt.v2.6 JSON file")
    ap.add_argument("--url", default=DEFAULT_URL)
    args = ap.parse_args()
    with open(args.receipt, "rb") as f:
        data = f.read()
    req = Request(args.url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            result = json.load(resp)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body)
        raise SystemExit(exc.code)

if __name__ == "__main__":
    main()
