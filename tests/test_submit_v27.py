from submit_v27 import verify_submission, sha


def base():
    trace={
        'schema_version':'sable.submission.v0.9',
        'task_id':'T1',
        'goal':'do task',
        'agent':{'framework':'CrewAI','framework_version':'1.15.20','model':'m','provider_base_url':'local'},
        'steps':[{'tool':'inventory.reserve','args':{},'observed_result':{'ok':True}}],
        'environment':{'task_success':True},
        'integrity':{'native_tool_calling':True,'tool_results_observed_by_sandbox':True,'agent_controlled_tool_result':False,'termination':'final'},
    }
    return {'protocol_version':'sable.submission.v0.9','submission_id':'sub-1','trace':trace,'integrity':{'source_trace_hash':sha(trace)}}


def test_valid_submission():
    r=verify_submission(base()); assert r['verified'] and r['decision']=='VERIFIED'


def test_tamper_rejected():
    s=base(); s['trace']['environment']['task_success']=False
    r=verify_submission(s); assert not r['verified'] and 'source_trace_hash_mismatch' in r['reasons']


def test_missing_observation_rejected():
    s=base(); s['trace']['integrity']['tool_results_observed_by_sandbox']=False; s['integrity']['source_trace_hash']=sha(s['trace'])
    r=verify_submission(s); assert not r['verified'] and 'sandbox_observation_not_attested' in r['reasons']
