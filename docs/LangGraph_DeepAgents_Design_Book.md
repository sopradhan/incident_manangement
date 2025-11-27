# Comprehensive Design Book for LangGraph and DeepAgents

## Overview
This document provides a detailed description of the LangGraph and DeepAgents systems, their dependencies, workflows, and operations. It covers ingestion of SQL tables and documents, data retrieval, metadata updates, vector database interactions, and the functioning of the healing agent.

---

## 1. LangGraph Agent

### 1.1 Purpose
The LangGraph Agent orchestrates workflows for:
- Document ingestion
- Context retrieval with traceability
- System optimization

### 1.2 Dependencies
- **Tools**: `extract_metadata_tool`, `chunk_document_tool`, `save_to_vectordb_tool`, `update_metadata_tracking_tool`
- **Services**: `LLMService`, `VectorDBService`, `ConfigService`
- **RL Agent**: `RLHealingAgent` for intelligent optimization

### 1.3 Workflows
#### 1.3.1 Ingestion Workflow
- **Nodes**:
  - `extract_metadata`: Extracts metadata from documents.
  - `chunk_document`: Breaks documents into smaller chunks.
  - `save_vectordb`: Saves chunks to the vector database.
  - `update_tracking`: Updates metadata tracking.
- **Process**:
  1. Extract metadata.
  2. Chunk the document.
  3. Save chunks to the vector database.
  4. Update metadata tracking.

#### 1.3.2 Retrieval Workflow
- **Nodes**:
  - `retrieve_context`: Retrieves relevant context from the vector database.
  - `rerank_context`: Reranks the retrieved context by relevance.
  - `answer_question`: Generates an answer from the context.
  - `traceability`: Links the answer to source documents.
- **Integration with RL Agent**:
  - Uses `RLHealingAgent` to decide if optimization is needed.
  - Applies healing actions like reindexing or re-embedding if required.

#### 1.3.3 Optimization Workflow
- **Nodes**:
  - `optimize`: Analyzes performance history and suggests improvements.
  - `apply_config`: Updates system configuration.

---

## 2. DeepAgents Agent

### 2.1 Purpose
The DeepAgents Agent consolidates workflows for:
- Document ingestion
- Context retrieval
- System healing
- Configuration management

### 2.2 Dependencies
- **Tools**: Same as LangGraph Agent
- **Middleware**: `TodoListMiddleware` for persistent task tracking
- **Backend**: `FilesystemBackend` for storing tasks

### 2.3 Features
- **TaskManager**:
  - Plans, tracks, and executes tasks.
  - Uses Chain-of-Thought reasoning for decision-making.
- **Subagents**:
  - `ingestion-agent`: Handles document ingestion.
  - `retrieval-agent`: Manages context retrieval and Q&A.
  - `healing-agent`: Optimizes system performance.
  - `config-agent`: Adjusts system configuration.

---

## 3. Healing Agent

### 3.1 Purpose
The Healing Agent optimizes the RAG system using reinforcement learning (RL).

### 3.2 RL Architecture
- **State**: Document quality, query accuracy, token cost.
- **Actions**: `SKIP`, `OPTIMIZE`, `REINDEX`, `RE_EMBED`.
- **Reward**: `(Quality Improvement - Cost) * Confidence`.
- **Learning**: Tracks effectiveness of actions and improves over time.

### 3.3 Workflow
1. Evaluate the current state.
2. Decide the best action using RL.
3. Execute the action.
4. Observe the reward and update learning.

---

## 4. How to Invoke

### 4.1 Ingesting a Document
1. Use the `ingest_document` method in LangGraph or DeepAgents Agent.
2. Provide the document text and a unique document ID.
3. The agent will:
   - Extract metadata.
   - Chunk the document.
   - Save chunks to the vector database.
   - Update metadata tracking.

### 4.2 Retrieving Context
1. Use the `ask_question` method.
2. Provide the question and optional document ID.
3. The agent will:
   - Retrieve and rerank context.
   - Generate an answer.
   - Provide traceability.

### 4.3 Optimizing the System
1. Use the `optimize_system` method.
2. Provide performance history and configuration updates.
3. The agent will:
   - Analyze performance.
   - Suggest and apply optimizations.

---

## 5. LangGraph Nodes

### 5.1 Ingestion Nodes
- `extract_metadata`: Extracts metadata from documents.
- `chunk_document`: Breaks documents into smaller chunks.
- `save_vectordb`: Saves chunks to the vector database.
- `update_tracking`: Updates metadata tracking.

### 5.2 Retrieval Nodes
- `retrieve_context`: Retrieves relevant context from the vector database.
- `rerank_context`: Reranks the retrieved context by relevance.
- `answer_question`: Generates an answer from the context.
- `traceability`: Links the answer to source documents.

### 5.3 Optimization Nodes
- `optimize`: Analyzes performance history and suggests improvements.
- `apply_config`: Updates system configuration.

---

## 6. Conclusion
This design book provides a comprehensive overview of the LangGraph and DeepAgents systems, their workflows, and dependencies. By leveraging modular tools, RL-based healing, and workflow orchestration, these agents enable efficient and intelligent RAG operations.