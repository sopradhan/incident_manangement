from src.incident_iq.rag.agents.master_orchestrator import RAGMasterAgent

agent = RAGMasterAgent()

# First, let's see what tools are available to the agent
print("🔧 [DEBUG] Checking available tools and capabilities...")
tools_check = agent.agent.invoke({"input": "What tools and functions do you have available? List them all."})
print(f"📋 Available tools: {getattr(tools_check, 'content', str(tools_check))}")

print("\n" + "="*80)
print("Now testing simple ingestion...")
print("="*80)

# Test 1: Ingestion Request
print("="*80)
print("🧪 Testing Document Ingestion...")
print("="*80)
ingestion_result = agent.agent.invoke({"input": "Please ingest the document at test_documents/test_incident_report.txt"})
print(f"🎯 Ingestion Result: {ingestion_result}")

print("\n" + "="*80)
print("🧪 Testing Search/Retrieval...")
print("="*80)

# Test 2: Retrieval Request
retrieval_result = agent.agent.invoke({"input": "What information is in the incident report?"})
print(f"🎯 Retrieval Result: {retrieval_result}")