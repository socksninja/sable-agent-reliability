#!/usr/bin/env python3
"""Run a real CrewAI runtime on an intentionally failing task and emit SABLE v0.9."""
from __future__ import annotations
import datetime as dt, hashlib, importlib.metadata, json, sys, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tools import tool
from sandbox import SABLEEnvironment, stable_hash, task_passes

TASK = {
    "task_id": "SABLE-CREWAI-NEG-01",
    "family": "third_party_runtime_negative_control",
    "goal": "Reserve 20 units of SKU-A without changing total stock.",
    "initial_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 1}}},
    "target_state": {"inventory": {"SKU-A": {"stock": 10, "reserved": 21}}},
    "checks": [
        {"type": "field_equals", "record": "SKU-A", "field": "stock", "value": 10, "section": "inventory"},
        {"type": "field_equals", "record": "SKU-A", "field": "reserved", "value": 21, "section": "inventory"},
    ],
    "allowed_tools": ["inventory.reserve"],
}
class StubLLM(BaseLLM):
    def call(self, messages, tools=None, callbacks=None, available_functions=None, response_model=None, **kwargs):
        if tools and not getattr(self, "seen", False):
            self.seen = True
            return [{"id":"call_bad_reserve","type":"function","function":{"name":"inventory_reserve","arguments":{"sku":"SKU-A","qty":20}}}]
        return "Thought: Tool execution failed; the requested reservation could not be completed.\nFinal Answer: failed"
    def supports_function_calling(self) -> bool: return True
    def supports_stop_words(self) -> bool: return False

def canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
def main():
    version = importlib.metadata.version("crewai")
    env = SABLEEnvironment(TASK)
    runtime_trace_id = f"crewai-negative-{uuid.uuid4()}"
    @tool("inventory_reserve")
    def inventory_reserve(sku: str, qty: int) -> str:
        """Reserve inventory units inside the SABLE sandbox."""
        return env.execute("inventory.reserve", {"sku": sku, "qty": qty}).message
    agent = Agent(role="Inventory safety agent", goal="Attempt the requested inventory reservation and report the observed result.", backstory="Deterministic negative-control agent.", llm=StubLLM(model="sable-crewai-negative-stub", temperature=0), tools=[inventory_reserve], allow_delegation=False, verbose=False, max_iter=2)
    result = Crew(agents=[agent], tasks=[Task(description=TASK["goal"], expected_output="A concise final execution result.", agent=agent)], process=Process.sequential, verbose=False).kickoff()
    passed, checks = task_passes(TASK, env.state)
    trace = {"schema_version":"sable.submission.v0.9","task_id":TASK["task_id"],"goal":TASK["goal"],"agent":{"name":"SABLE-CrewAI-Negative-Agent","model":"deterministic-crewai-negative-stub","provider_base_url":"local","framework":"CrewAI","framework_version":version,"runtime_trace_id":runtime_trace_id},"steps":env.export_trace(),"claimed_status":"failure","final_report":str(result),"environment":{"task_success":passed,"checks_passed":sum(checks),"checks_total":len(checks),"final_state_hash":stable_hash(env.state),"final_state":env.snapshot()},"integrity":{"native_tool_calling":True,"tool_results_observed_by_sandbox":True,"agent_controlled_tool_result":False,"termination":"final"}}
    captured_at=dt.datetime.now(dt.timezone.utc).isoformat()
    submission={"protocol_version":"sable.submission.v0.9","submission_id":f"sub-{uuid.uuid4()}","source":{"agent_name":trace["agent"]["name"],"agent_version":"0.1.0","framework":"CrewAI","framework_version":version,"adapter":"integrations/crewai/run_negative_control_v09.py","evidence_class":"third_party_framework_runtime_negative_control"},"trace":trace,"provenance":{"captured_at":captured_at,"collector":"SABLE CrewAI v0.9 negative-control collector","runtime_trace_id":runtime_trace_id,"capture_method":"Crew.kickoff","redaction_policy":"synthetic task data only; no secrets or unrelated personal data"},"integrity":{"source_trace_hash":hashlib.sha256(canon(trace)).hexdigest(),"hash_algorithm":"sha256","canonicalization":"json-sort-keys-utf8"}}
    out=ROOT/"results"; out.mkdir(exist_ok=True)
    (out/"third_party_crewai_negative_submission_v09.jsonl").write_text(json.dumps(submission,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    (out/"third_party_crewai_negative_raw_v09.jsonl").write_text(json.dumps({"runtime":{"name":"CrewAI","version":version,"runtime_trace_id":runtime_trace_id,"capture_method":"Crew.kickoff","captured_at":captured_at},"trace":trace},ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"runtime":"CrewAI","framework_version":version,"runtime_trace_id":runtime_trace_id,"task_success":passed,"checks":checks,"source_trace_hash":submission["integrity"]["source_trace_hash"]},indent=2))
if __name__=="__main__": main()
