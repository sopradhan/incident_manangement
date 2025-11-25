from incident_iq.transport_agent.agents.analysis_agent import build_analysis_agent, analyze_incident
from incident_iq.transport_agent.agents.escalation_agent import build_escalation_agent, decide_paging
from incident_iq.transport_agent.agents.execution_agent import Executor


def build_pipeline():
    """
    Builds the three-subagent DeepAgents pipeline:
      - Analysis subagent: interprets incident + classifier payload, produces plan
      - Escalation subagent: decides if paging (PagerDuty) is required
      - Execution subagent: runs all tool actions (Jira, Slack, PD)
    """
    reasoner = build_analysis_agent()
    escalation = build_escalation_agent()
    executor = Executor()

    return {
        "analysis": reasoner,
        "escalation": escalation,
        "executor": executor,
    }


async def handle_incident(
    incident: dict,
    classifier_payload: dict,
    env_context: str
):
    """
    Full incident-processing pipeline:

        1. Analysis subagent → produce structured plan
        2. Escalation subagent → optionally add paging
        3. Execution subagent → run the plan (calls Jira, Slack, PD)

    Returns:
        {
            "plan": {...},
            "execution": {...}
        }
    """

    print("Started handle pipeline ..")

    pipeline = build_pipeline()

    print("Pipeline created : ",pipeline)
    
    analysis_agent = pipeline["analysis"]
    escalation_agent = pipeline["escalation"]
    executor = pipeline["executor"]

    # 1) --- ANALYSIS SUBAGENT ---
    plan = await analyze_incident(
        analysis_agent,
        incident,
        classifier_payload,
        env_context
    )

    # Ensure the plan includes incident_id
    if "incident_id" not in plan:
        plan["incident_id"] = incident.get("payload_id", "unknown")

    # Ensure decisions exist
    plan.setdefault("decisions", [])

    # 2) --- ESCALATION SUBAGENT ---
    # If analysis subagent did not already decide on paging,
    # ask escalation agent.
    if not plan.get("page"):
        escalation_decision = await decide_paging(
            escalation_agent,
            incident,
            classifier_payload,
            plan
        )

        if escalation_decision.get("page"):
            plan["decisions"].append({
                "tool": "pagerduty_escalate",
                "args": {
                    "summary": plan.get("summary", "PagerDuty Auto-Escalation"),
                    "details": escalation_decision.get("reason")
                },
                "reason": "Escalation subagent recommended paging"
            })

            # Mark paging in final plan
            plan["page"] = True

    # 3) --- EXECUTION SUBAGENT ---
    execution_result = await executor.execute_plan(plan)

    return {
        "plan": plan,
        "execution": execution_result
    }
