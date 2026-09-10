#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
VERSION='sable.capability_token.v2.2'
SUBJECT_KEYS=('agent_id','model','provider','runtime','framework_version')
BINDING_KEYS=('task_id','task_semantic_key','policy_hash','reputation_hash','credential_hash')
def canon_bytes(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def canon_hash(obj): return hashlib.sha256(canon_bytes(obj)).hexdigest()
def public_key_b64(key): return base64.b64encode(key.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
def load_public_key(value): return Ed25519PublicKey.from_public_bytes(base64.b64decode(value))
def _body(decision,subject,issued_at,expires_at,nonce,key_id):
    return {'schema_version':VERSION,'subject':{k:subject.get(k) for k in SUBJECT_KEYS},'authorization':{'tool':decision['tool'],'tool_class':decision['tool_class'],'decision':decision['decision'],'permission_tier':decision['permission_tier'],'trust_score_observed':decision['trust_score_observed']},'bindings':{k:subject.get(k) for k in BINDING_KEYS},'issued_at':int(issued_at),'expires_at':int(expires_at),'nonce':nonce,'signing':{'alg':'Ed25519','key_id':key_id}}
def issue_signed(decision,subject,private_key,*,issued_at,ttl_seconds,nonce,key_id='sable-dev'):
    if decision.get('decision')!='ALLOW' or not decision.get('executable'): raise ValueError('capability_token_requires_gateway_allow')
    if ttl_seconds<=0: raise ValueError('ttl_seconds_must_be_positive')
    if not nonce: raise ValueError('nonce_required')
    body=_body(decision,subject,issued_at,issued_at+ttl_seconds,nonce,key_id)
    return {**body,'token_hash':canon_hash(body),'signature':base64.b64encode(private_key.sign(canon_bytes(body))).decode()}
def verify_signed(token,public_key,*,now,expected,used_nonces=None):
    reasons=[]; body={k:token[k] for k in token if k not in {'token_hash','signature'}}
    if token.get('schema_version')!=VERSION: reasons.append('schema_version_mismatch')
    if token.get('token_hash')!=canon_hash(body): reasons.append('token_integrity_mismatch')
    try: issued_at,expires_at=int(token['issued_at']),int(token['expires_at'])
    except (KeyError,TypeError,ValueError): reasons.append('invalid_token_times'); issued_at=expires_at=0
    if int(now)<issued_at: reasons.append('token_not_yet_valid')
    if int(now)>=expires_at: reasons.append('token_expired')
    try: public_key.verify(base64.b64decode(token['signature']),canon_bytes(body))
    except Exception: reasons.append('signature_invalid')
    auth,subject,bindings=token.get('authorization',{}),token.get('subject',{}),token.get('bindings',{})
    if auth.get('decision')!='ALLOW': reasons.append('token_not_allow')
    if not isinstance(subject,dict) or not isinstance(bindings,dict): reasons.append('token_subject_or_bindings_invalid'); subject,bindings={},{}
    for key in SUBJECT_KEYS:
        if expected.get(key) is not None and subject.get(key)!=expected[key]: reasons.append(f'binding_mismatch:{key}')
    for key in BINDING_KEYS:
        if expected.get(key) is not None and bindings.get(key)!=expected[key]: reasons.append(f'binding_mismatch:{key}')
    if expected.get('tool') is not None and auth.get('tool')!=expected['tool']: reasons.append('binding_mismatch:tool')
    nonce=str(token.get('nonce',''))
    if not nonce: reasons.append('nonce_missing')
    if used_nonces is not None and nonce in used_nonces: reasons.append('token_replay')
    return not reasons,reasons
