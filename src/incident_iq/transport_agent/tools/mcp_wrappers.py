import asyncio
import json
from typing import Any, Dict
# Try to import your real tools; if not available, use stubs for local testing
# try:
# 	from incident_iq.transport.tools import create_jira_issue as real_create_jira_issue
# 	from incident_iq.transport.tools import post_slack_alert as real_post_slack_alert
# # Optionally your pagerduty tool
# 	from incident_iq.transport.tools import trigger_pagerduty as real_trigger_pagerduty
# except Exception:

async def real_create_jira_issue(args: Dict[str, Any]):
	return {"status": "created", "ticket": "JIRA-LOCAL-1", "args": args}


async def real_post_slack_alert(args: Dict[str, Any]):
	return {"status": "sent", "channel": args.get("channel", "#incidents"), "args": args}


async def real_trigger_pagerduty(args: Dict[str, Any]):
	return {"status": "paged", "service": args.get("service", "PD-LOCAL"), "args": args}




async def wrapped_create_jira_issue(tool_input: Dict[str, Any]) -> Dict[str, Any]:
	args = {
	"summary": tool_input.get("summary"),
	"description": tool_input.get("description"),
	"priority": tool_input.get("priority", "Medium"),
	"labels": tool_input.get("labels", []),
	"properties": tool_input.get("properties", {}),
	}
	res = await real_create_jira_issue(args)
	try:
		json.dumps(res)
	except Exception:
		res = {"status": "error", "message": "non-serializable result from create_jira_issue"}
	return res




async def wrapped_post_slack_alert(tool_input: Dict[str, Any]) -> Dict[str, Any]:
	args = {
	"channel": tool_input.get("channel", "#incidents"),
	"message": tool_input.get("message", ""),
	"attachments": tool_input.get("attachments", []),
	}
	res = await real_post_slack_alert(args)
	try:
		json.dumps(res)
	except Exception:
		res = {"status": "error", "message": "non-serializable result from post_slack_alert"}
	return res




async def wrapped_trigger_pagerduty(tool_input: Dict[str, Any]) -> Dict[str, Any]:
	args = {
	"service": tool_input.get("service", "pagerduty-service"),
	"summary": tool_input.get("summary", "PagerDuty page"),
	"details": tool_input.get("details", {}),
	}
	res = await real_trigger_pagerduty(args)
	try:
		json.dumps(res)
	except Exception:
		res = {"status": "error", "message": "non-serializable result from trigger_pagerduty"}
	return res

def create_jira_issue_sync(tool_input: Dict[str, Any]) -> Dict[str, Any]:
	return asyncio.run(wrapped_create_jira_issue(tool_input))

def post_slack_alert_sync(tool_input: Dict[str, Any]) -> Dict[str, Any]:
	return asyncio.run(wrapped_post_slack_alert(tool_input))

def trigger_pagerduty_sync(tool_input: Dict[str, Any]) -> Dict[str, Any]:
	return asyncio.run(wrapped_trigger_pagerduty(tool_input))