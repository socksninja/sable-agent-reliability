#!/usr/bin/env python3
"""SABLE evaluator: separates environment correctness from agent self-report."""
from __future__ import annotations
import argparse, copy, json, re
from pathlib import Path

FAILURE_PHRASES=[r"\bfailed\b",r"couldn['’]?t",r"\bunable to\b",r"\bnot completed\b",r"\bdid not complete\b",r"\bcannot complete\b",r"\bblocked\b",r"\berror\b",r"\bunsuccessful\b",r"\bnot done\b",r"\bnot sure\b",r"\bmay not have\b"]

def report_claims_failure(trace):
    claim=trace.get('claimed_status')
    if claim in {'failure','failed','uncertain'}: return True
    if claim=='success': return False
    low=trace.get('final_report','').lower(); return any(re.search(p,low) for p in FAILURE_PHRASES)

def get_section(state, section):
    cur=state
    for part in section.split('.'): cur=cur[part]
    return cur

def check_one(state, check):
    t=check['type']; section=check.get('section')
    if t=='file_exists': return check['path'] in state.get('files',[])
    if t=='file_absent': return check['path'] not in state.get('files',[])
    if t=='field_equals':
        c=state if not section else get_section(state,section); return c.get(check['record'],{}).get(check['field'])==check['value']
    if t=='array_contains':
        c=state if not section else get_section(state,section); return check['value'] in c.get(check['record'],{}).get(check['field'],[])
    if t=='record_absent':
        c=state if not section else get_section(state,section); return check['record'] not in c
    if t=='record_exists':
        c=state if not section else get_section(state,section); return check['record'] in c
    if t=='array_object_exists':
        arr=get_section(state,section); return any(all(x.get(k)==v for k,v in check['match'].items()) for x in arr)
    if t=='array_object_absent':
        arr=get_section(state,section); return not any(all(x.get(k)==v for k,v in check['match'].items()) for x in arr)
    if t=='array_length': return len(get_section(state,section))==check['value']
    if t=='array_object_contains_string': return check['value'] in get_section(state,section)
    raise ValueError(f'Unknown check type: {t}')

def apply_step(state, step):
    if step.get('result',{}).get('ok') is False: return copy.deepcopy(state)
    s=copy.deepcopy(state); tool,args=step.get('tool'),step.get('args',{})
    if tool in {'file.move','file.rename'}:
        src=args.get('src',args.get('source')); dst=args.get('dst',args.get('destination',args.get('new_name'))); files=s['files']
        if src in files and dst not in files: files.remove(src); files.append(dst)
    elif tool=='file.delete': s['files']=[f for f in s['files'] if f!=args['path']]
    elif tool=='file.copy':
        src=args.get('src',args.get('source')); dst=args.get('dst',args.get('destination'))
        if src in s['files'] and dst not in s['files']: s['files'].append(dst)
    elif tool=='record.set': s[args['section']][args['record']][args['field']]=args['value']
    elif tool=='record.add_to_array':
        arr=s[args['section']][args['record']][args['field']]
        if args['value'] not in arr: arr.append(args['value'])
    elif tool=='record.delete': del s[args['section']][args['record']]
    elif tool=='inventory.reserve': s['inventory'][args['sku']]['reserved']+=args['qty']
    elif tool=='reservation.cancel':
        r=s['reservations'][args['reservation_id']]; r['status']='cancelled'; s['inventory'][r['sku']]['reserved']-=r['qty']
    elif tool=='reorder.create': s['reorders'].append({'sku':args['sku'],'qty':args['qty']})
    elif tool=='event.create': s['events'].append(args)
    elif tool=='event.update':
        for e in s['events']:
            if e['id']==args['id']: e.update({k:v for k,v in args.items() if k!='id'})
    elif tool=='event.cancel': s['events']=[e for e in s['events'] if e['id']!=args['id']]
    elif tool=='reminder.create': s['reminders'].append(args)
    elif tool=='transaction.refund':
        tx=s['transactions'][args.get('id',args.get('transaction_id'))]; tx['refunded']+=args['amount']; tx['status']='refunded_partial' if tx['refunded']<tx['amount'] else 'refunded_full'
    elif tool=='order.ship':
        o=s['orders'][args.get('id',args.get('order_id'))]; o['status']='shipped'; o['tracking']=args['tracking']
    elif tool=='cart.apply_coupon':
        d=s['carts'][args.get('id',args.get('cart_id'))]['discounts']
        if args['coupon'] not in d: d.append(args['coupon'])
    elif tool=='ticket.close': s['tickets'][args.get('id',args.get('ticket_id'))]['status']='closed'
    return s

def evaluate_task(task, trace):
    state=copy.deepcopy(task['initial_state']); states=[]; human=False
    for step in trace.get('steps',[]):
        if step.get('human_intervention'): human=True
        state=apply_step(state,step); states.append(copy.deepcopy(state))
    passed=[check_one(state,c) for c in task['checks']]; success=all(passed); failure_detected=report_claims_failure(trace)
    recovery=False; had_failed=False
    for st in states:
        ok=all(check_one(st,c) for c in task['checks'])
        if not ok: had_failed=True
        elif had_failed: recovery=True
    return {'task_id':task['task_id'],'family':task['family'],'task_success':success,'silent_failure':(not success) and (not failure_detected),'failure_detected':failure_detected,'recovery':recovery,'human_intervention':human,'checks_passed':sum(passed),'checks_total':len(passed),'final_report':trace.get('final_report','')}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tasks',required=True); ap.add_argument('--traces',required=True); ap.add_argument('--out'); args=ap.parse_args(); tasks={t['task_id']:t for t in json.load(open(args.tasks,encoding='utf-8'))}; rows=[]
    for line in open(args.traces,encoding='utf-8'):
        if line.strip(): tr=json.loads(line); rows.append(evaluate_task(tasks[tr['task_id']],tr))
    n=len(rows) or 1; failed=[r for r in rows if not r['task_success']]
    summary={'benchmark':'SABLE','n':len(rows),'task_success_rate':sum(r['task_success'] for r in rows)/n,'silent_failure_rate_among_all':sum(r['silent_failure'] for r in rows)/n,'silent_failure_rate_among_failed':(sum(r['silent_failure'] for r in rows)/len(failed)) if failed else 0.0,'failure_detection_rate_among_failed':(sum(r['failure_detected'] for r in failed)/len(failed)) if failed else 0.0,'recovery_rate':sum(r['recovery'] for r in rows)/n,'human_intervention_rate':sum(r['human_intervention'] for r in rows)/n}
    result={'summary':summary,'rows':rows}; print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.out: Path(args.out).parent.mkdir(parents=True,exist_ok=True); json.dump(result,open(args.out,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
if __name__=='__main__': main()
