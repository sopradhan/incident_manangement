from dotenv import load_dotenv
import httpx
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from datetime import datetime

from langchain_ollama import ChatOllama
from incident_iq.database.db.connection import get_connection
from incident_iq.transport.transport_models import IncidentContext
from typing import Any
import json

from incident_iq.transport.transporter.transport_utils import build_incident_prompt_context
from incident_iq.database.models.classifier_output import ClassifierOutputsModel

from incident_iq.transport.tools import create_jira_issue, post_slack_alert
import json

client = httpx.Client(verify=False) 

load_dotenv()

class IntelligentTicketingAgent:
    """Intelligent agent that autonomously decides which MCP tools to call"""

    def __init__(self):
        self.llm = self.llm = ChatOllama(
            model="llama3.2",
            base_url="http://localhost:11434",
        )    
        
        # Define the tools the LLM can use
        self.tools = [
            create_jira_issue,
            post_slack_alert
        ]
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _describe_context(self, context: IncidentContext) -> str:
        parts = []
        if not context.business_hours:
            parts.append("OFF-HOURS (2-4 AM) - Engineers are asleep")
        elif context.peak_traffic_hours:
            parts.append("PEAK TRAFFIC - Maximum user activity")
        else:
            parts.append("BUSINESS HOURS - Team available")
        
        if context.weekend:
            parts.append("WEEKEND")
        
        if context.customer_facing:
            parts.append("CUSTOMER-FACING")
        else:
            parts.append("NTERNAL ONLY")
        
        if context.revenue_impacting:
            parts.append("REVENUE-IMPACTING")
        
        return "\n".join(parts)



    async def make_decision_and_execute(
        self,
        incident,
        context,
    ) -> dict:
        """Let the LLM autonomously decide which MCP tools to call and execute them."""

        incident_context = build_incident_prompt_context(incident)

        conn = get_connection()
        classifier_output_model = ClassifierOutputsModel(conn)

        payload_record = classifier_output_model.get_by_payload_id(incident['payload_id'])
        payload_str = dict(payload_record).get("payload", {})
        payload_data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
        payload_metadata = {
            k: v for k, v in payload_data.items() if k != "payload"
        }

        formatted_payload = json.dumps(payload_data, indent=2) if payload_data else "N/A"
        system_prompt = """You are an expert incident coordinator with 15+ years of SRE experience.

    You have access to tools for managing incidents. Analyze the incident carefully and decide which tools to call.

    DECISION GUIDELINES:
    - ALWAYS create a Jira ticket for tracking (choose appropriate priority)
    - Send Slack alerts for team visibility (choose channel based on severity)
    - ONLY create PagerDuty incidents for truly critical issues:
    * Customer-facing outages affecting many users
    * Revenue-impacting payment/checkout failures
    * Security breaches or data loss
    - DO NOT wake engineers for:
    * Internal tools during off-hours
    * Issues that can wait until business hours
    * Potential issues without confirmed customer impact

    Think: "Would I want to be woken at 3 AM for this?" If no, don't page.

    Analyze the incident, explain your reasoning, then call the appropriate tools.
    """

        user_prompt = f"""ANALYZE THIS INCIDENT:
        **Classifier Metadata:**
        - Severity ID: {payload_metadata.get("severity_id", "N/A")}
        - Matched Pattern: {payload_metadata.get("matched_pattern", "N/A")}
        - Is Incident: {payload_metadata.get("is_incident", "N/A")}

        **Environment & Context Summary:**
        {incident_context}

        **Context:**
        {self._describe_context(context)}

        **Payload (from classifier_outputs):**
        {formatted_payload}

        **Questions to Consider:**
        1. Would YOU want to be woken up for this at this time?
        2. How many customers are affected RIGHT NOW?
        3. Can this wait until business hours?
        4. Is this causing revenue loss or just potential issues?

        Think through your decision and call the appropriate tools now.
        """

        messages = [
            HumanMessage(content=system_prompt + "\n\n" + user_prompt)
        ]
        tool_calls_made = []
        reasoning_text = ""
        try:
            # Get LLM response with tool binding
            response = self.llm_with_tools.invoke(messages)
            print(response) 

            # Check if LLM wants to call tools
            if hasattr(response, "tool_calls") and response.tool_calls:
                print(f"LLM decided to call {len(response.tool_calls)} tool(s)")

                messages.append(response)

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call.get("id", "unknown")

                    try:
                        # Run the correct tool
                        if tool_name == "create_jira_issue":
                            result = await self.tools[0].ainvoke(tool_args)
                        elif tool_name == "post_slack_alert":
                            result = await self.tools[1].ainvoke(tool_args)
                        else:
                            result = {"status": "error", "message": f"Unknown tool: {tool_name}"}

                        print(f"  Result: {result}")

                        tool_calls_made.append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": result
                        })

                        # Add response back to conversation
                        messages.append(ToolMessage(
                            content=json.dumps(result),
                            tool_call_id=tool_id
                        ))

                    except Exception as e:
                        error_result = {"status": "error", "message": str(e)}
                        messages.append(ToolMessage(
                            content=json.dumps(error_result),
                            tool_call_id=tool_id
                        ))

            else:
                # LLM finished decision-making
                if hasattr(response, "content") and response.content:
                    reasoning_text = response.content
                    print(f"\nReasoning: {reasoning_text[:300]}...")
            
        except Exception as e:
            import traceback
            traceback.print_exc()