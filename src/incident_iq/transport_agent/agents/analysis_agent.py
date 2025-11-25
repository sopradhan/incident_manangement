import json
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from incident_iq.transport_agent.config import ANALYSIS_SYSTEM_PROMPT, backend


ollama_llm = ChatOllama(
    model="llama3.2",
    base_url="http://localhost:11434",
    num_predict=2048,
    temperature=0.2
)

model = ChatOllama(model="llama3.2")

from typing import TypedDict, List, Dict, Any

class State(TypedDict):
    payload: Dict[str, Any]
    messages: List[Dict[str, str]]
    response: Any

def build_messages(payload):
    messages = [
        {"system",  ANALYSIS_SYSTEM_PROMPT},
        {
            "user", "PROCESS INCIDENT:\n" +
                json.dumps(payload, indent=2)
        }
    ]
    return messages


def run_llm(state: State):
    prompt = ""

    for m in state["messages"]:
        role = m["role"].upper()
        prompt += f"{role}: {m['content']}\n\n"

    response = model.invoke(prompt)
    return {"response": response}


# graph = StateGraph(State)
# graph.add_node("build_messages", build_messages)
# graph.add_node("run_llm", run_llm)

# graph.set_entry_point("build_messages")
# graph.add_edge("build_messages", "run_llm")
# graph.add_edge("run_llm", END)

# app = graph.compile()

def build_analysis_agent():
    print("Strated building analysis agent...")
    agent = create_deep_agent(model=ollama_llm, tools=[], system_prompt=ANALYSIS_SYSTEM_PROMPT, backend=backend)
    return agent

async def analyze_incident(agent, incident: dict, classifier_payload: dict, env_context: str) -> dict:
    payload = {
        "incident": incident,
        "classifier_payload": classifier_payload,
        "env_context": env_context
    }

    # messages = [
    #     {
    #         "role": "system",
    #         "content": ANALYSIS_SYSTEM_PROMPT
    #     },
    #     {
    #         "role": "user",
    #         # CRITICAL: wrap the JSON so the model knows it's a task
    #         "content": f"PROCESS INCIDENT:\n{json.dumps(payload, indent=2)}"
    #     }
    # ]

    print(build_messages(payload),"payload")     
    result = ollama_llm.invoke(build_messages(payload))

    print("\n=== RAW GRAPH RESULT ===")
    print(result["response"])
    plan=""

    # # Extract text
    # text = getattr(resp, "content", None) or str(resp)

    # # Attempt JSON parse
    # try:
    #     plan = json.loads(text)
    # except Exception:
    #     import re
    #     m = re.search(r"(\{.*\})", text, re.S)
    #     if m:
    #         try:
    #             plan = json.loads(m.group(1))
    #         except Exception:
    #             plan = {"error": "failed_to_parse_json", "raw": text}
    #     else:
    #         plan = {"error": "no_json_found", "raw": text}
    
    return plan
