#!/usr/bin/env python3
"""
Quick Start Guide - Agentic RAG System

This file shows how to quickly test the refactored RAG system.
"""

# =============================================================================
# OPTION 1: Run the full test suite (RECOMMENDED)
# =============================================================================
# From the incident_manangement directory:
# 
# python scripts/test_rag_ingestion.py
#
# This will:
# 1. Initialize the agent
# 2. Ingest a sample document
# 3. Ask multiple questions with traceability
# 4. Check vector database status
# 5. Run optimization workflow
# 6. Test config adjustment
#
# Expected output: 5 test sections with ✅ success indicators

# =============================================================================
# OPTION 2: Use the agent programmatically
# =============================================================================
# 
# from src.incident_iq.rag.agent.autonomous_rag_agent import AutonomousRAGAgent
# import json
# 
# # Initialize agent
# agent = AutonomousRAGAgent()
# 
# # Ingest document
# result = agent.ingest_document(
#     text="Your document here...",
#     doc_id="doc_001"
# )
# print("Ingestion result:", json.loads(result['save']))
# 
# # Ask question with traceability
# result = agent.ask_question("What is the document about?")
# print("Answer:", json.loads(result['answer']))
# print("Traceability:", json.loads(result['traceability']))

# =============================================================================
# OPTION 3: Start the Streamlit dashboard
# =============================================================================
#
# Terminal 1 - Start FastAPI backend:
# python -m uvicorn src.incident_iq.rag.dashboard.dashboard_app:app --reload
#
# Terminal 2 - Start Streamlit frontend:
# streamlit run src/incident_iq/rag/dashboard/dashboard.py
#
# Open browser to: http://localhost:8501

# =============================================================================
# REQUIREMENTS
# =============================================================================
#
# Python 3.8+
# Install dependencies:
#   pip install -r requirements.txt
#
# OR manually:
#   pip install deepagents langchain langchain-core langchain-ollama chromadb pydantic fastapi streamlit requests

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================
#
# Create .env.local or set environment variables:
#
# LLM_CONFIG_PATH=llm_config.json
# CHROMA_DB_PATH=./chroma_db
# CHROMA_COLLECTION=rag_embeddings
#
# Create llm_config.json in project root with your LLM provider settings

# =============================================================================
# TROUBLESHOOTING
# =============================================================================
#
# Q: "ModuleNotFoundError: No module named 'incident_iq'"
# A: Make sure you're running from project root, or add to PYTHONPATH:
#    export PYTHONPATH="${PYTHONPATH}:/path/to/incident_manangement/src"
#
# Q: "LLMService failed to initialize"
# A: Check llm_config.json exists and has valid provider configuration
#    Ensure Ollama is running: ollama serve
#
# Q: "ChromaDB error"
# A: Check CHROMA_DB_PATH is writable
#    Default: ./chroma_db (created automatically)
#
# Q: "Vector database is empty"
# A: Run document ingestion first:
#    python scripts/test_rag_ingestion.py
#    Then run questions

# =============================================================================
# KEY FILES
# =============================================================================
#
# Agent Orchestration:
# src/incident_iq/rag/agent/autonomous_rag_agent.py
#
# Tools:
# src/incident_iq/rag/tools/ingestion_tools.py
# src/incident_iq/rag/tools/retrieval_tools.py
# src/incident_iq/rag/tools/healing_tools.py
# src/incident_iq/rag/tools/adjust_config_tool.py
#
# Services:
# src/incident_iq/rag/tools/services/llm_service.py
# src/incident_iq/rag/tools/services/vectordb_service.py
#
# Dashboard:
# src/incident_iq/rag/dashboard/dashboard.py (Streamlit)
# src/incident_iq/rag/dashboard/dashboard_app.py (FastAPI)
#
# Tests:
# scripts/test_rag_ingestion.py
#
# Documentation:
# RAG_SYSTEM_README.txt
# RAG_REFACTOR_SUMMARY.txt

# =============================================================================
# EXAMPLE: Full workflow
# =============================================================================
"""
from src.incident_iq.rag.agent.autonomous_rag_agent import AutonomousRAGAgent
import json

# 1. Initialize
print("Initializing agent...")
agent = AutonomousRAGAgent()

# 2. Ingest
print("Ingesting document...")
doc_text = '''
Incident Management Best Practices:
- Respond within 15 minutes for P1 incidents
- Keep detailed incident logs
- Communicate status to stakeholders
'''
result = agent.ingest_document(doc_text, "practices_001")
print(f"Ingested successfully: {json.loads(result['save']).get('chunks_saved')} chunks")

# 3. Ask
print("Asking question...")
result = agent.ask_question("What is the response time for P1 incidents?")
answer_data = json.loads(result['answer'])
trace_data = json.loads(result['traceability'])
print(f"Answer: {answer_data.get('answer')}")
print(f"Sources: {trace_data.get('traceability', {}).get('sources_used')} documents used")

# 4. Optimize
print("Optimizing...")
perf = [{"params": {"k": 5}, "metrics": {"accuracy": 0.9}}]
result = agent.optimize(perf)
print(f"Optimization suggestion: {result}")

print("✅ Complete workflow finished!")
"""
