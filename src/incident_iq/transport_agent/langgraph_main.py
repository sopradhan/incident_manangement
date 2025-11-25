from langchain_ollama import ChatOllama
from langchain_core.messages import convert_to_messages
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch

from dotenv import load_dotenv
import os   
load_dotenv('.env')

llm = ChatOllama(
model="llama3.1:8b",
temperature=0,
base_url="http://localhost:11434")

web_search = TavilySearch(max_results=3)

def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")

def add(a: float, b: float):
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float):
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float):
    """Divide two numbers."""
    return a / b

math_agent = create_react_agent(
    model=llm,
    tools=[add, multiply, divide],
    prompt=(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="math_agent",
)

research_agent = create_react_agent(
    model=llm,
    tools=[web_search],
    prompt=(
        "You are a research agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with research-related tasks, DO NOT do any math\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="research_agent",
)

supervisor = create_supervisor(
    model=llm,
    agents=[research_agent, math_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research_agent. Assign research-related tasks to this agent\n"
        "- a math_agent. Assign math-related tasks to this agent, solving addition, multiplication, division\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()

if __name__ == "__main__":

    for chunk in supervisor.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "multiply 3 and 5",
                }
            ]
        },
    ):
        pretty_print_messages(chunk, last_message=True)

    final_message_history = chunk["supervisor"]["messages"]

    for chunk in supervisor.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "find US and New York state GDP in 2024. what % of US GDP was New York state?",
                }
            ]
        },
    ):
        pretty_print_messages(chunk, last_message=True)
    final_message_history = chunk["supervisor"]["messages"]    
