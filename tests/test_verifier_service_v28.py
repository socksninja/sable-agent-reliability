import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from verifier_service_v28 import verify_payload
from verification_receipt_v25 import sign_receipt


def submission():
    trace={
        'schema_version':'sable.submission.v0.9','task_id':'T1','goal':'do task',
        'agent':{'framework':'CrewAI','framework_version':'1.15.20','model':'m','provider_base_url':'local'},
        'steps':[{'tool':'inventory.reserve','args':{},'observed_result':{'ok':True}}],
        'environment':{'task_success':True},
        'integrity':{'native_tool_calling':True,'tool_results_observed_by_sandbox':True,'agent_controlled_tool_result':False,'termination':'final'},
    }
    from submit_v27 import sha
    return {'protocol_version':'sable.submission.v0.9','submission_id':'s1','trace':trace,'integrity':{'source_trace_hash':sha(trace)}}


def receipt_v24():
    return {
      'schema_version':'sable.verification_receipt.v2.4',
      'execution':{'task_id':'T1','runtime':'CrewAI','framework_version':'1.15.20','model':'m','provider':'local','runtime_trace_id':'tr1'},
      'authorization':{'permission':'ALLOW','verified':True,'reasons':[],'capability_token_hash':'cap'},
      'evidence':{'evidence_hash':'ev','task_success':True,'replay_match':True,'before_state_hash':'b','after_state_hash':'a','termination':'final','tool_calls':1,'tools':['inventory.reserve']},
      'receipt_hash':'placeholder'
    }


def test_submission_is_only_structural():
    r=verify_payload(submission()); assert r['verified']; assert r['verification_level']=='STRUCTURALLY_VALID'; assert r['execution_proof'] is False


def test_signed_receipt_is_crypto_verified():
    p=Ed25519PrivateKey.generate(); signed=sign_receipt(receipt_v24(),p); signed['public_key']=base64.b64encode(p.public_key().public_bytes_raw()).decode()
    r=verify_payload(signed); assert r['verified']; assert r['verification_level']=='CRYPTOGRAPHICALLY_VERIFIED'; assert r['execution_proof'] is True


def test_unknown_schema_rejected():
    r=verify_payload({'schema_version':'x'}); assert not r['verified'] and r['decision']=='REJECTED'
