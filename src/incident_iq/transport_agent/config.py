from pathlib import Path
from deepagents.backends import FilesystemBackend


ROOT_DIR = Path("./agent_workspace").resolve()
ROOT_DIR.mkdir(parents=True, exist_ok=True)


backend = FilesystemBackend(root_dir=str(ROOT_DIR))


# System prompts for subagents
ANALYSIS_SYSTEM_PROMPT = """
You will receive an input object shaped like this:

{
  "incident": {...},             // the main incident details
  "classifier_payload": {...},   // severity classifier output
  "env_context": {...}           // metadata such as oncall hours
}

Use ONLY "incident" for fields like incident_id, summary, severity, description.
Use classifier_payload to adjust severity.
Use env_context to decide paging.

Always return:

{
  "incident_id": "...",
  "summary": "...",
  "severity": 1-5,
  "actions": [...],
  "decisions": [],
  "page": true/false
}

"""


ESCALATION_PROMPT = """
You are the Escalation subagent.
Given incident metadata and a proposed plan, decide if immediate paging (PagerDuty) is required.
Return JSON: {"page": true|false, "reason": "..."}
"""


EXECUTION_PROMPT = """
You are the Execution subagent.
You will receive a validated, structured plan and should execute each decision in order by calling the provided tools.
Return a JSON summary of each step's result.
"""