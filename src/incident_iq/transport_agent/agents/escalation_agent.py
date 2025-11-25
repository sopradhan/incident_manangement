import json
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from incident_iq.transport_agent.config import ESCALATION_PROMPT, backend


ollama_llm = ChatOllama(
    model="llama3.2",
    base_url="http://localhost:11434",
)

def build_escalation_agent():
    return create_deep_agent(model=ollama_llm,tools=[], system_prompt=ESCALATION_PROMPT, backend=backend)

async def decide_paging(agent, incident: dict, classifier_payload: dict, proposed_plan: dict) -> dict:
    payload = {"incident": incident, "classifier_payload": classifier_payload, "proposed_plan": proposed_plan}
    messages = [{"role": "user", "content": json.dumps(payload)}]
    if hasattr(agent, "ainvoke"):
        resp = await agent.ainvoke({"messages": messages})
    else:
        resp = agent.invoke({"messages": messages})

    text = getattr(resp, "content", None) or str(resp)
    try:
        return json.loads(text)
    except Exception:
        import re
        m = re.search(r"(\{.*\})", text, re.S)
    if m:
        return json.loads(m.group(1))
    return {"page": False, "reason": "unable_to_parse_response"}