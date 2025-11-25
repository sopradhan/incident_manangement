import json
from typing import Dict, Any
from incident_iq.transport_agent.config import backend, ROOT_DIR
from incident_iq.transport_agent.tools.mcp_wrappers import wrapped_create_jira_issue, wrapped_post_slack_alert, wrapped_trigger_pagerduty
from datetime import datetime


LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def _write_log(name: str, obj: Dict[str, Any]):
    path = LOG_DIR / name
    with open(path, "a") as f:
        f.write(json.dumps(obj, default=str) + "\n")

class Executor:
    def __init__(self):
        self.tool_map = {
        "create_jira_issue": wrapped_create_jira_issue,
        "post_slack_alert": wrapped_post_slack_alert,
        "pagerduty_escalate": wrapped_trigger_pagerduty,
        }


async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = plan.get("incident_id", "unknown")
    decisions = plan.get("decisions", [])
    results = []


    for idx, d in enumerate(decisions):
        tool = d.get("tool")
        args = d.get("args", {})
        reason = d.get("reason", "")
        entry = {
        "incident_id": incident_id,
        "step": idx,
        "tool": tool,
        "args": args,
        "reason": reason,
        "started_at": datetime.utcnow().isoformat() + "Z"
        }
        _write_log(f"{incident_id}_plan.log", {"planned": entry})

        if tool not in self.tool_map:
            entry["result"] = {"status": "error", "message": f"unknown tool {tool}"}
        results.append(entry)
        _write_log(f"{incident_id}_exec.log", {"executed": entry})
        continue

    fn = self.tool_map[tool]
    try:
        res = await fn(args)
    except Exception as e:
        res = {"status": "error", "message": str(e)}
    entry["result"] = res
    entry["finished_at"] = datetime.utcnow().isoformat() + "Z"
    results.append(entry)
    _write_log(f"{incident_id}_exec.log", {"executed": entry})


    final = {"incident_id": incident_id, "results": results}
    _write_log(f"{incident_id}_final.log", final)
    return final