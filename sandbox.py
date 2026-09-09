#!/usr/bin/env python3
"""SABLE Sandbox v0.4: executable deterministic task environments.

The agent may request tool calls, but it cannot author tool results. The sandbox
validates arguments, enforces per-task tool authorization, mutates state, returns
an observed result, and records a state hash after every call.
"""
from __future__ import annotations
import copy, hashlib, json
from dataclasses import dataclass
from typing import Any

ALLOWED_TOOLS = {
    'file.move', 'file.rename', 'file.delete', 'file.copy',
    'record.set', 'record.add_to_array', 'record.delete',
    'inventory.reserve', 'reservation.cancel', 'reorder.create',
    'event.create', 'event.update', 'event.cancel', 'reminder.create',
    'transaction.refund', 'order.ship', 'cart.apply_coupon', 'ticket.close'
}

def stable_hash(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()

def get_path(state: dict, path: str) -> Any:
    cur: Any = state
    for part in path.split('.'):
        if isinstance(cur, list): cur = cur[int(part)]
        elif isinstance(cur, dict): cur = cur[part]
        else: raise KeyError(path)
    return cur

@dataclass
class Observation:
    tool: str
    args: dict[str, Any]
    ok: bool
    message: str
    before_hash: str
    after_hash: str
    state: dict[str, Any] | None = None

class SABLEEnvironment:
    def __init__(self, task: dict):
        self.task_id = task['task_id']
        self.state = copy.deepcopy(task['initial_state'])
        self.observations: list[Observation] = []
        self.human_intervention_count = 0
        self.allowed_tools = set(task.get('allowed_tools', ALLOWED_TOOLS))

    def snapshot(self) -> dict[str, Any]: return copy.deepcopy(self.state)
    def state_hash(self) -> str: return stable_hash(self.state)

    def execute(self, tool: str, args: dict[str, Any], *, human_intervention: bool = False) -> Observation:
        before = self.state_hash()
        if human_intervention: self.human_intervention_count += 1
        if tool not in ALLOWED_TOOLS:
            obs = Observation(tool, args, False, f'unknown_tool:{tool}', before, before, self.snapshot())
            self.observations.append(obs); return obs
        if tool not in self.allowed_tools:
            obs = Observation(tool, args, False, f'unauthorized_tool:{tool}', before, before, self.snapshot())
            self.observations.append(obs); return obs
        try:
            message = self._apply(tool, args); ok = True
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            message = f'{type(exc).__name__}:{exc}'; ok = False
        after = self.state_hash()
        obs = Observation(tool, copy.deepcopy(args), ok, message, before, after, self.snapshot())
        self.observations.append(obs); return obs

    def _require_keys(self, args: dict, keys: list[str]) -> None:
        missing = [k for k in keys if k not in args]
        if missing: raise ValueError(f'missing_args:{missing}')

    def _apply(self, tool: str, args: dict) -> str:
        if tool in {'file.move','file.rename','file.copy'}:
            self._require_keys(args, ['source','destination'] if tool != 'file.rename' else ['source','new_name'])
            src = args['source']; dst = args.get('destination', args.get('new_name')); files = self.state.setdefault('files', [])
            if src not in files: raise ValueError(f'source_absent:{src}')
            if dst in files: raise ValueError(f'destination_exists:{dst}')
            if tool == 'file.copy': files.append(dst); return f'copied:{src}->{dst}'
            files.remove(src); files.append(dst); return f'{tool.split(".")[1]}:{src}->{dst}'
        if tool == 'file.delete':
            self._require_keys(args, ['path']); files = self.state.setdefault('files', [])
            if args['path'] not in files: raise ValueError(f'file_absent:{args["path"]}')
            files.remove(args['path']); return f'deleted:{args["path"]}'
        if tool == 'record.set':
            self._require_keys(args, ['section','record','field','value']); sec = get_path(self.state, args['section']); rid = args['record']
            if rid not in sec: raise KeyError(rid)
            sec[rid][args['field']] = args['value']; return f'set:{args["section"]}/{rid}/{args["field"]}'
        if tool == 'record.add_to_array':
            self._require_keys(args, ['section','record','field','value']); sec = get_path(self.state, args['section']); rid=args['record']
            if rid not in sec: raise KeyError(rid)
            arr=sec[rid][args['field']]
            if args['value'] not in arr: arr.append(args['value'])
            return f'array_add:{rid}/{args["field"]}'
        if tool == 'record.delete':
            self._require_keys(args, ['section','record']); sec=get_path(self.state,args['section']); rid=args['record']
            if rid not in sec: raise KeyError(rid)
            del sec[rid]; return f'deleted_record:{rid}'
        if tool == 'inventory.reserve':
            self._require_keys(args,['sku','qty']); inv=self.state['inventory'][args['sku']]; qty=args['qty']
            if not isinstance(qty,int) or qty <= 0: raise ValueError('qty_must_be_positive_int')
            if qty > inv['stock']-inv['reserved']: raise ValueError('insufficient_available_stock')
            inv['reserved'] += qty; return f'reserved:{qty}:{args["sku"]}'
        if tool == 'reservation.cancel':
            self._require_keys(args,['reservation_id']); rid=args['reservation_id']; r=self.state['reservations'][rid]
            if r['status'] != 'active': raise ValueError('reservation_not_active')
            r['status']='cancelled'; self.state['inventory'][r['sku']]['reserved'] -= r['qty']; return f'cancelled:{rid}'
        if tool == 'reorder.create':
            self._require_keys(args,['sku','qty']); self.state['reorders'].append({'sku':args['sku'],'qty':args['qty']}); return f'reorder_created:{args["sku"]}'
        if tool == 'event.create': self.state.setdefault('events',[]).append(copy.deepcopy(args)); return f'event_created:{args.get("id")}'
        if tool == 'event.update':
            self._require_keys(args,['id']); found=False
            for e in self.state['events']:
                if e['id']==args['id']: e.update({k:v for k,v in args.items() if k!='id'}); found=True; break
            if not found: raise KeyError(args['id'])
            return f'event_updated:{args["id"]}'
        if tool == 'event.cancel':
            self._require_keys(args,['id']); old=len(self.state['events']); self.state['events']=[e for e in self.state['events'] if e['id']!=args['id']]
            if len(self.state['events'])==old: raise KeyError(args['id'])
            return f'event_cancelled:{args["id"]}'
        if tool == 'reminder.create': self.state.setdefault('reminders',[]).append(copy.deepcopy(args)); return f'reminder_created:{args.get("id")}'
        if tool == 'transaction.refund':
            self._require_keys(args,['transaction_id','amount']); tx=self.state['transactions'][args['transaction_id']]; amt=args['amount']
            if amt<=0 or tx['refunded']+amt>tx['amount']: raise ValueError('invalid_refund_amount')
            tx['refunded'] += amt; tx['status']='refunded_full' if tx['refunded']==tx['amount'] else 'refunded_partial'; return f'refunded:{amt}'
        if tool == 'order.ship':
            self._require_keys(args,['order_id','tracking']); o=self.state['orders'][args['order_id']]; o['status']='shipped'; o['tracking']=args['tracking']; return f'shipped:{args["order_id"]}'
        if tool == 'cart.apply_coupon':
            self._require_keys(args,['cart_id','coupon']); d=self.state['carts'][args['cart_id']]['discounts']
            if args['coupon'] not in d: d.append(args['coupon'])
            return f'coupon_applied:{args["coupon"]}'
        if tool == 'ticket.close':
            self._require_keys(args,['ticket_id']); t=self.state['tickets'][args['ticket_id']]; t['status']='closed'; return f'ticket_closed:{args["ticket_id"]}'
        raise ValueError(f'unhandled_tool:{tool}')

    def export_trace(self) -> list[dict[str, Any]]:
        return [{'tool':o.tool,'args':o.args,'observed_result':{'ok':o.ok,'message':o.message},'before_state_hash':o.before_hash,'after_state_hash':o.after_hash,'state_after':o.state} for o in self.observations]

def task_passes(task: dict, state: dict) -> tuple[bool, list[bool]]:
    results=[]
    for check in task['checks']:
        t=check['type']
        if t=='file_exists': results.append(check['path'] in state.get('files',[]))
        elif t=='file_absent': results.append(check['path'] not in state.get('files',[]))
        elif t=='field_equals':
            container = state if not check.get('section') else get_path(state,check['section']); results.append(container.get(check['record'],{}).get(check['field'])==check['value'])
        elif t=='array_contains':
            container = state if not check.get('section') else get_path(state,check['section']); results.append(check['value'] in container.get(check['record'],{}).get(check['field'],[]))
        elif t=='record_absent':
            container=state if not check.get('section') else get_path(state,check['section']); results.append(check['record'] not in container)
        elif t=='record_exists':
            container=state if not check.get('section') else get_path(state,check['section']); results.append(check['record'] in container)
        elif t in {'array_object_exists','array_object_absent'}:
            arr=get_path(state,check['section']); found=any(all(x.get(k)==v for k,v in check['match'].items()) for x in arr); results.append(found if t=='array_object_exists' else not found)
        elif t=='array_length': results.append(len(get_path(state,check['section']))==check['value'])
        elif t=='array_object_contains_string': results.append(check['value'] in get_path(state,check['section']))
        else: raise ValueError(f'unknown_check:{t}')
    return all(results), results
