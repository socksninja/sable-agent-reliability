#!/usr/bin/env python3
"""SABLE v2.8 reference HTTP verifier.

POST /v1/verify with a v0.9 submission or v2.5/v2.6 signed receipt.
The service never treats a self-reported success claim as cryptographic proof:
v0.9 submissions can be structurally valid, while signed receipts can be
cryptographically verified.
"""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from submit_v27 import verify_submission
from verification_receipt_v25 import verify_signed_receipt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import base64


def verify_payload(payload: dict) -> dict:
    schema = payload.get('schema_version') or payload.get('protocol_version')
    if schema == 'sable.submission.v0.9':
        r = verify_submission(payload)
        r['verification_level'] = 'STRUCTURALLY_VALID' if r['verified'] else 'REJECTED'
        r['execution_proof'] = False
        return r
    if schema in {'sable.verification_receipt.v2.5', 'sable.verification_receipt.v2.6'}:
        try:
            public = Ed25519PublicKey.from_public_bytes(base64.b64decode(payload['public_key']))
            ok, reasons = verify_signed_receipt(payload, public)
        except Exception as exc:
            ok, reasons = False, [f'public_key_or_signature_error:{type(exc).__name__}']
        return {
            'schema_version': 'sable.verifier_service.v2.8',
            'verified': ok,
            'decision': 'VERIFIED' if ok else 'REJECTED',
            'reasons': reasons,
            'verification_level': 'CRYPTOGRAPHICALLY_VERIFIED' if ok else 'REJECTED',
            'execution_proof': ok,
            'receipt_hash': payload.get('receipt_hash'),
        }
    return {'schema_version':'sable.verifier_service.v2.8','verified':False,'decision':'REJECTED','reasons':['unsupported_schema'],'verification_level':'REJECTED','execution_proof':False}


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, obj: dict):
        raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()
        self.send_response(status); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path == '/v1/health': self._json(200, {'service':'sable-verifier','schema_version':'sable.verifier_service.v2.8','status':'ok'})
        else: self._json(404, {'error':'not_found'})
    def do_POST(self):
        if self.path != '/v1/verify': return self._json(404, {'error':'not_found'})
        try:
            n=int(self.headers.get('Content-Length','0')); payload=json.loads(self.rfile.read(n))
            result=verify_payload(payload); self._json(200 if result['verified'] else 422, result)
        except Exception as exc:
            self._json(400, {'error':'invalid_json','detail':type(exc).__name__})
    def log_message(self, fmt, *args): return


def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8787); a=p.parse_args()
    print(f'SABLE verifier listening on http://{a.host}:{a.port}/v1/verify')
    HTTPServer((a.host,a.port),Handler).serve_forever()

if __name__=='__main__': main()
