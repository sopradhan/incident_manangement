"""
CONSOLIDATED DeepAgents RAG Agent
Integrates:
- DeepAgents orchestration with Flashpoint master agent
- FilesystemBackend + TodoListMiddleware for persistent todo planning
- TaskManager with Chain-of-Thought tracking
- All subagents (Ingestion, Retrieval, Healing, Config)

Single agent file for all RAG operations with native DeepAgents persistence.
"""

import os
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict, field

try:
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend
    from deepagents.middleware import TodoListMiddleware
except ImportError:
    print("WARNING: deepagents not installed. Core features may not work.")
    FilesystemBackend = None
    TodoListMiddleware = None

from langchain_core.tools import tool

# Import RAG tools
from ...tools.ingestion_tools import (
    extract_metadata_tool,
    chunk_document_tool,
    save_to_vectordb_tool,
    update_metadata_tracking_tool,
    ingest_sqlite_table_tool,
    record_agent_memory_tool,
)
from ...tools.retrieval_tools import (
    retrieve_context_tool,
    rerank_context_tool,
    answer_question_tool,
    traceability_tool,
)
from ...tools.healing_tools import (
    check_embedding_health_tool,
    get_context_cost_tool,
    optimize_chunk_size_tool,
)
from ...tools.adjust_config_tool import adjust_config_tool
from ...tools.services.llm_service import LLMService
from ...tools.services.vectordb_service import VectorDBService
from ...config.env_config import EnvConfig


# ============================================================================
# TASK MANAGER - EMBEDDED (from task_manager.py)
# ============================================================================

class TaskStatus(Enum):
    """Task lifecycle states"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELEGATED = "delegated"


class TaskType(Enum):
    """Task classification by domain"""
    INGESTION = "ingestion"
    RETRIEVAL = "retrieval"
    HEALING = "healing"
    CONFIGURATION = "configuration"
    ORCHESTRATION = "orchestration"


@dataclass
class ChainOfThought:
    """Chain-of-Thought reasoning record"""
    step: str
    reasoning: str
    decision: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Task:
    """Individual task record with execution tracking"""
    task_id: str
    task_type: TaskType
    description: str
    status: TaskStatus = TaskStatus.PLANNED
    planned_subagent: Optional[str] = None
    delegated_to: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    reasoning: List[ChainOfThought] = field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        data = asdict(self)
        data['task_type'] = self.task_type.value
        data['status'] = self.status.value
        data['reasoning'] = [asdict(r) for r in self.reasoning]
        return data


class TaskManager:
    """Manages task planning, execution, and tracking"""
    
    def __init__(self):
        """Initialize task manager"""
        self.planned_tasks: List[Task] = []
        self.executed_tasks: List[Task] = []
        self.active_task: Optional[Task] = None
        self.task_counter = 0
    
    def plan_task(self, task_type: TaskType, description: str, 
                  planned_subagent: str = None, input_data: Dict[str, Any] = None) -> Task:
        """Plan a new task"""
        self.task_counter += 1
        task = Task(
            task_id=f"task_{self.task_counter:04d}",
            task_type=task_type,
            description=description,
            planned_subagent=planned_subagent,
            input_data=input_data or {}
        )
        self.planned_tasks.append(task)
        return task
    
    def start_task(self, task: Task) -> None:
        """Mark task as in progress"""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()
        self.active_task = task
    
    def add_reasoning(self, step: str, reasoning: str, decision: str) -> None:
        """Add Chain-of-Thought reasoning step"""
        if self.active_task:
            cot = ChainOfThought(step=step, reasoning=reasoning, decision=decision)
            self.active_task.reasoning.append(cot)
    
    def complete_task(self, output_data: Dict[str, Any] = None, error: str = None) -> Task:
        """Mark active task as completed"""
        if not self.active_task:
            raise RuntimeError("No active task to complete")
        
        task = self.active_task
        task.output_data = output_data or {}
        task.error = error
        task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        
        if task.started_at:
            start = datetime.fromisoformat(task.started_at)
            end = datetime.fromisoformat(task.completed_at)
            task.execution_time_ms = (end - start).total_seconds() * 1000
        
        self.executed_tasks.append(task)
        self.active_task = None
        
        return task
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get summary of planned vs executed tasks"""
        planned_count = len(self.planned_tasks)
        executed_count = len(self.executed_tasks)
        completed_count = sum(1 for t in self.executed_tasks if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in self.executed_tasks if t.status == TaskStatus.FAILED)
        
        avg_execution_time = 0.0
        if self.executed_tasks:
            total_time = sum(t.execution_time_ms for t in self.executed_tasks)
            avg_execution_time = total_time / len(self.executed_tasks)
        
        return {
            "planned_tasks": planned_count,
            "executed_tasks": executed_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "success_rate": (completed_count / executed_count * 100) if executed_count > 0 else 0,
            "avg_execution_time_ms": avg_execution_time,
            "task_types": self._count_by_type(),
            "subagent_distribution": self._count_by_subagent()
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count tasks by type"""
        counts = {}
        for task in self.executed_tasks:
            key = task.task_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def _count_by_subagent(self) -> Dict[str, int]:
        """Count tasks by delegated subagent"""
        counts = {}
        for task in self.executed_tasks:
            subagent = task.delegated_to or "unknown"
            counts[subagent] = counts.get(subagent, 0) + 1
        return counts
    
    def export_tasks_json(self) -> str:
        """Export all tasks as JSON"""
        data = {
            "planned_tasks": [t.to_dict() for t in self.planned_tasks],
            "executed_tasks": [t.to_dict() for t in self.executed_tasks],
            "summary": self.get_task_summary(),
            "exported_at": datetime.now().isoformat()
        }
        return json.dumps(data, indent=2)
    
    def print_task_report(self) -> None:
        """Print detailed task report"""
        print("\n" + "="*80)
        print("  TASK EXECUTION REPORT")
        print("="*80)
        
        summary = self.get_task_summary()
        print(f"\nPLANNED vs EXECUTED:")
        print(f"  Planned Tasks: {summary['planned_tasks']}")
        print(f"  Executed Tasks: {summary['executed_tasks']}")
        print(f"  Completed: {summary['completed_tasks']}")
        print(f"  Failed: {summary['failed_tasks']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Avg Execution Time: {summary['avg_execution_time_ms']:.1f}ms")
        
        if summary['task_types']:
            print(f"\nTASK TYPES:")
            for task_type, count in summary['task_types'].items():
                print(f"  {task_type}: {count}")
        
        if summary['subagent_distribution']:
            print(f"\nSUBAGENT DISTRIBUTION:")
            for subagent, count in summary['subagent_distribution'].items():
                print(f"  {subagent}: {count}")
        
        print(f"\nDETAILED EXECUTION LOG:")
        for task in self.executed_tasks:
            status_icon = "[OK]" if task.status == TaskStatus.COMPLETED else "[ERROR]"
            print(f"\n  {status_icon} {task.task_id}: {task.description}")
            print(f"     Status: {task.status.value}")
            print(f"     Delegated To: {task.delegated_to}")
            print(f"     Execution Time: {task.execution_time_ms:.1f}ms")
            
            if task.reasoning:
                print(f"     Chain-of-Thought:")
                for cot in task.reasoning:
                    print(f"       - {cot.step}: {cot.reasoning}")
                    print(f"         Decision: {cot.decision}")
            
            if task.error:
                print(f"     Error: {task.error}")
        
        print("\n" + "="*80 + "\n")


# ============================================================================
# MAIN DEEPAGENTS RAG AGENT - CONSOLIDATED
# ============================================================================

class DeepAgentsRAGAgent:
    """
    Consolidated DeepAgents RAG Agent with:
    - Flashpoint master orchestrator
    - Four specialized subagents (Ingestion, Retrieval, Healing, Config)
    - TaskManager with Chain-of-Thought tracking
    - FilesystemBackend + TodoListMiddleware for persistent todo planning
    """
    
    def __init__(self, todo_dir: str = "./deepagents_workflow"):
        """Initialize consolidated agent with all features.
        
        Args:
            todo_dir: Directory for persistent todo storage via FilesystemBackend
        """
        self.task_manager = TaskManager()
        self.todo_dir = todo_dir
        os.makedirs(todo_dir, exist_ok=True)
        
        self.llm_service, self.vectordb_service, self.config_service = self._init_services()
        
        # Create FilesystemBackend for persistence
        self.backend = FilesystemBackend(root_dir=todo_dir) if FilesystemBackend else None
        
        self.ingestion_subagent = self._create_ingestion_subagent()
        self.retrieval_subagent = self._create_retrieval_subagent()
        self.healing_subagent = self._create_healing_subagent()
        self.config_subagent = self._create_config_subagent()
        self.master_agent = self._create_master_agent()

    def _init_services(self):
        """Initialize services using environment configuration."""
        # Get configuration paths from EnvConfig
        rag_config_path = EnvConfig.get_rag_config_path()
        llm_config_path = os.getenv("LLM_CONFIG_PATH", os.path.join(rag_config_path, "llm_config.json"))
        
        try:
            with open(llm_config_path, "r") as f:
                llm_config = json.load(f)
        except FileNotFoundError:
            llm_config = {"default_provider": "ollama", "llm_providers": {}, "embedding_providers": {}}
        
        llm_service = LLMService(llm_config)
        
        # Use EnvConfig for VectorDB paths
        chroma_db_path = EnvConfig.get_chroma_db_path()
        vectordb_service = VectorDBService(
            persist_directory=chroma_db_path,
            collection_name=os.getenv("CHROMA_COLLECTION", "rag_embeddings")
        )
        
        # config_service is not used; use EnvConfig directly
        return llm_service, vectordb_service, None

    def _create_ingestion_subagent(self) -> Dict[str, Any]:
        """Create ingestion subagent with tools."""
        @tool
        def extract_metadata(text: str) -> str:
            """Extract metadata from document."""
            return extract_metadata_tool(text, llm_service=self.llm_service)

        @tool
        def chunk_document(text: str, doc_id: str) -> str:
            """Chunk document into smaller pieces."""
            return chunk_document_tool(text, doc_id)

        @tool
        def save_to_db(chunks: str, doc_id: str, metadata: str = None, rbac_namespace: str = "general") -> str:
            """Save chunks to vector database."""
            return save_to_vectordb_tool(
                chunks, doc_id,
                llm_service=self.llm_service,
                vectordb_service=self.vectordb_service,
                metadata=metadata,
                rbac_namespace=rbac_namespace
            )

        @tool
        def update_tracking(doc_id: str, source_path: str, rbac_namespace: str, metadata: str, chunks_saved: int) -> str:
            """Update metadata tracking."""
            return update_metadata_tracking_tool(doc_id, source_path, rbac_namespace, metadata, chunks_saved)

        tools = [extract_metadata, chunk_document, save_to_db, update_tracking]
        
        return {
            "name": "ingestion-agent",
            "description": "Handles document ingestion, chunking, embedding, and storage",
            "system_prompt": """You are a professional document ingestion specialist with expertise in RAG systems.

RESPONSIBILITIES:
1. EXTRACT METADATA: Identify key metadata from documents (title, author, date, topic, keywords)
2. CHUNK DOCUMENTS: Break documents into semantically meaningful chunks (300-500 tokens)
3. GENERATE EMBEDDINGS: Create embeddings for each chunk using the embedding service
4. STORE IN DATABASE: Save all chunks with metadata to the vector database
5. TRACK METADATA: Update metadata tracking with ingestion status and statistics

PROCESS:
- Extract and preserve all important metadata
- Create logical chunks that preserve meaning across boundaries
- Ensure chunks are indexed with proper doc_id and chunk_id
- Return SUCCESS with ingestion statistics or ERROR with details

TOOL SEQUENCE: extract_metadata → chunk_document → save_to_db → update_tracking""",
            "tools": tools,
            "model": self.llm_service.get_model()
        }

    def _create_retrieval_subagent(self) -> Dict[str, Any]:
        """Create retrieval subagent with tools."""
        @tool
        def retrieve_context(question: str, top_k: int = 5, rbac_namespace: str = "general") -> str:
            """Retrieve context from vector database."""
            return retrieve_context_tool(
                question,
                llm_service=self.llm_service,
                vectordb_service=self.vectordb_service,
                top_k=top_k,
                rbac_namespace=rbac_namespace
            )

        @tool
        def rerank_context(context: str) -> str:
            """Rerank retrieved context by relevance."""
            return rerank_context_tool(context, llm_service=self.llm_service)

        @tool
        def answer_question(question: str, context: str) -> str:
            """Generate answer from context."""
            return answer_question_tool(question, context, llm_service=self.llm_service)

        @tool
        def get_traceability(question: str, context: str) -> str:
            """Generate traceability for answer."""
            return traceability_tool(question, context, vectordb_service=self.vectordb_service)

        tools = [retrieve_context, rerank_context, answer_question, get_traceability]
        
        return {
            "name": "retrieval-agent",
            "description": "Retrieves, reranks, and answers questions with traceability",
            "system_prompt": """You are an expert retrieval and generation specialist for RAG systems.

RESPONSIBILITIES:
1. RETRIEVE CONTEXT: Search vector database for relevant documents matching the query
2. RERANK CONTEXT: Sort retrieved documents by relevance to the question
3. GENERATE ANSWER: Synthesize a comprehensive, accurate answer from the best context
4. PROVIDE TRACEABILITY: Link answer to source documents with confidence scores

PROCESS:
- Use retrieve_context to find top matching documents (top_k=5)
- Apply rerank_context to sort by relevance
- Use answer_question to generate a direct, specific answer
- Include source attribution and confidence scores
- Return: ANSWER, SOURCES, CONFIDENCE, TRACEABILITY

CRITICAL: ALWAYS provide a complete, well-formed answer. Never say "No answer generated".
If context is limited, synthesize what you can and note uncertainty.""",
            "tools": tools,
            "model": self.llm_service.get_model()
        }

    def _create_healing_subagent(self) -> Dict[str, Any]:
        """Create healing subagent with tools."""
        @tool
        def check_health(embeddings: List[List[float]], doc_id: str) -> str:
            """Check embedding health."""
            return check_embedding_health_tool(embeddings, doc_id, llm_service=self.llm_service)

        @tool
        def estimate_cost(context: List[Dict[str, str]], model_name: str = "gemini-2.5-pro") -> str:
            """Estimate context cost."""
            return get_context_cost_tool(context, llm_service=self.llm_service, model_name=model_name)

        @tool
        def optimize_params(performance_history: List[Dict[str, Any]]) -> str:
            """Optimize RAG parameters."""
            return optimize_chunk_size_tool(performance_history, llm_service=self.llm_service)

        tools = [check_health, estimate_cost, optimize_params]
        
        return {
            "name": "healing-agent",
            "description": "Monitors health, cost, and optimizes parameters",
            "system_prompt": """You are a RAG system optimization and healing specialist.

RESPONSIBILITIES:
1. HEALTH MONITORING: Check embedding quality, index health, and system performance
2. COST ANALYSIS: Estimate token costs and optimize for efficiency
3. PARAMETER OPTIMIZATION: Analyze performance history and recommend optimizations
4. HEALING ACTIONS: Execute optimization strategies

OPTIMIZATION STRATEGIES:
- OPTIMIZE: Tune chunk size and parameters
- RERANK: Improve reranking model
- CACHE: Cache frequently accessed embeddings
- REINDEX: Refresh indexes for better performance

PROCESS:
- Monitor quality score trends across queries
- Track token consumption and latency metrics
- Identify performance bottlenecks
- Recommend and execute healing actions

RETURN: Analysis + Issues + Recommendations + Improvements + Status""",
            "tools": tools,
            "model": self.llm_service.get_model()
        }

    def _create_config_subagent(self) -> Dict[str, Any]:
        """Create config subagent with tools."""
        @tool
        def adjust_system_config(updates: Dict[str, Any]) -> str:
            """Adjust system configuration."""
            # Create a simple config wrapper using EnvConfig
            class ConfigWrapper:
                def get_config(self):
                    return {
                        "RAG_K_FINAL": int(os.getenv("RAG_K_FINAL", "5")),
                        "CHUNK_SIZE": int(os.getenv("CHUNK_SIZE", "500")),
                        "CHUNK_OVERLAP": int(os.getenv("CHUNK_OVERLAP", "50")),
                    }
                def update_config(self, updates):
                    for key, value in updates.items():
                        os.environ[key] = str(value)
            
            config_wrapper = ConfigWrapper()
            return adjust_config_tool(config_wrapper, updates)

        tools = [adjust_system_config]
        
        return {
            "name": "config-agent",
            "description": "Dynamically adjusts system configuration",
            "system_prompt": """You are a system configuration and settings management specialist.

RESPONSIBILITIES:
1. CONFIGURATION MANAGEMENT: Update system settings based on requirements
2. VALIDATION: Ensure configuration changes are valid and don't conflict
3. IMPLEMENTATION: Apply configuration updates to the system
4. VERIFICATION: Confirm changes took effect and system is healthy

PROCESS:
- Validate all requested changes
- Apply changes in logical order (dependencies first)
- Verify system functionality after each change
- Report status: SUCCESS with new settings or ERROR with details
- Track configuration history for audit trails""",
            "tools": tools,
            "model": self.llm_service.get_model()
        }

    def _create_master_agent(self):
        """Create master agent (Flashpoint) with enhanced orchestration."""
        middleware = []
        if TodoListMiddleware:
            middleware.append(TodoListMiddleware())
        
        master = create_deep_agent(
            name="Flashpoint",
            model=self.llm_service.get_model(),
            system_prompt="""You are the **Master Orchestrator Agent (Flashpoint)** for an Autonomous, Self-Optimizing RAG system.
Your mission is to analyze user intent and perform strategic, single-point delegation to the most qualified subagent.

═══════════════════════════════════════════════════════════════════════════════

**MANDATORY INTERNAL PROCESS (Chain-of-Thought Analysis):**

**STEP 1: ANALYZE INTENT**
- Examine the user's request carefully
- Extract the core requirement (question, document, optimization need, config change)
- Classify into one of four domains:
  * INGESTION: Document upload, chunking, indexing, metadata extraction
  * RETRIEVAL: Questions, answers, context synthesis, traceability
  * HEALING: Performance analysis, optimization, cost reduction, health checks
  * CONFIGURATION: System settings, parameters, service endpoints

Reasoning: "The user is requesting [action]. This is fundamentally a [DOMAIN] task because [reason]."

---

**STEP 2: SUBAGENT SELECTION**
- Based on the domain classification, select the appropriate subagent:
  * INGESTION → 'ingestion-agent'
  * RETRIEVAL → 'retrieval-agent'
  * HEALING → 'healing-agent'
  * CONFIGURATION → 'config-agent'
- Articulate WHY this subagent is the best fit
- Identify what context/data it will need

Reasoning: "The best fit is [subagent] because [specific capabilities]."

---

**STEP 3: REFORMULATE & DELEGATE**
- Rephrase the user's request as explicit instructions for the subagent
- Include all necessary context (parameters, constraints, expected outcomes)
- Pass the reformulated instruction to the selected subagent
- Await the subagent's response

Delegation: "I am delegating this [DOMAIN] task to [subagent-name]. The instruction is: [detailed description]"

---

**STEP 4: RETURN RESULT**
- Present the subagent's response to the user
- Do NOT modify or synthesize the subagent's output—pass it through directly

═══════════════════════════════════════════════════════════════════════════════

**DELEGATION MATRIX:**

| Subagent         | Handles                                          |
|------------------|--------------------------------------------------|
| ingestion-agent  | Document loading, chunking, embedding, indexing |
| retrieval-agent  | Q&A, context retrieval, synthesis, traceability |
| healing-agent    | Performance eval, optimization, health checks   |
| config-agent     | System parameters, settings, service endpoints  |

═══════════════════════════════════════════════════════════════════════════════

**KEY CONSTRAINTS:**
1. REASONING IS MANDATORY: Always articulate your analysis before delegating
2. SINGLE DELEGATION: Delegate to only ONE subagent per request
3. NO SELF-EXECUTION: Never use tools yourself
4. COMPLETE REFORMULATION: Provide complete context to the subagent
5. DIRECT PASSTHROUGH: Return the subagent's output directly

Remember: You are Flashpoint. Think before you act. Reason explicitly. Delegate strategically.""",
            subagents=[
                self.ingestion_subagent,
                self.retrieval_subagent,
                self.healing_subagent,
                self.config_subagent
            ],
            backend=self.backend,
            middleware=middleware if middleware else None
        )
        return master

    def ingest_document(self, text: str, doc_id: str) -> Dict[str, Any]:
        """Ingest document with task tracking and persistent todo planning."""
        try:
            start_time = time.time()
            
            # Create todo task description for persistent planning
            todo_task = f"""Plan and execute document ingestion for {doc_id}:
1. Extract metadata from the document
2. Chunk the document into semantic pieces
3. Create embeddings for each chunk
4. Save chunks to vector database
5. Update metadata tracking

Confirm completion of each step using write_todos and read_todos tools."""
            
            # Plan task via master agent with todo middleware
            todo_plan = self.master_agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"Plan the following task and track progress: {todo_task}"
                }]
            })
            
            # Plan task in task manager
            task = self.task_manager.plan_task(
                task_type=TaskType.INGESTION,
                description=f"Ingest document: {doc_id}",
                planned_subagent="ingestion-agent",
                input_data={"doc_id": doc_id, "text_length": len(text)}
            )
            
            self.task_manager.start_task(task)
            
            self.task_manager.add_reasoning(
                step="ANALYZE_INTENT",
                reasoning="User wants to ingest and index a document with persistent todo tracking via FilesystemBackend",
                decision="Classify as INGESTION domain task"
            )
            
            self.task_manager.add_reasoning(
                step="SELECT_SUBAGENT",
                reasoning="The ingestion-agent handles document loading, chunking, and indexing with TodoListMiddleware",
                decision="Delegate to ingestion-agent"
            )
            
            instruction = f"""Ingest and index the following document:

DOCUMENT_ID: {doc_id}
CONTENT (first 500 chars): {text[:500]}...

Steps:
1. Extract metadata using extract_metadata tool
2. Chunk the document using chunk_document tool
3. Save chunks to database using save_to_db tool
4. Update metadata tracking using update_tracking tool

Return: SUCCESS with ingestion statistics or ERROR with details"""
            
            result = self.master_agent.invoke({
                "messages": [{"role": "user", "content": instruction}]
            })
            
            task.delegated_to = "ingestion-agent"
            output_data = {"result": result, "doc_id": doc_id, "todo_persisted": bool(todo_plan)}
            self.task_manager.complete_task(output_data=output_data)
            
            return {
                "success": True,
                "doc_id": doc_id,
                "result": result,
                "task_id": task.task_id,
                "todo_persisted": True,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        except Exception as e:
            if self.task_manager.active_task:
                self.task_manager.complete_task(error=str(e))
            
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }

    def ask_question(self, question: str) -> Dict[str, Any]:
        """Answer question with task tracking and persistent todo planning."""
        try:
            start_time = time.time()
            
            # Create todo task description
            todo_task = f"""Plan and execute answering this question with persistent tracking:
Question: {question}

Steps:
1. Analyze the question intent
2. Retrieve relevant context from vector database
3. Rerank context by relevance
4. Generate a comprehensive answer
5. Provide source attribution

Confirm completion of each step using write_todos and read_todos tools."""
            
            # Plan query via master agent with todo middleware
            todo_plan = self.master_agent.invoke({
                "messages": [{"role": "user", "content": f"Plan the following task: {todo_task}"}]
            })
            
            task = self.task_manager.plan_task(
                task_type=TaskType.RETRIEVAL,
                description=f"Answer question: {question}",
                planned_subagent="retrieval-agent",
                input_data={"question": question}
            )
            
            self.task_manager.start_task(task)
            
            self.task_manager.add_reasoning(
                step="ANALYZE_INTENT",
                reasoning="User is asking a question requiring context retrieval and synthesis with persistent todo tracking",
                decision="Classify as RETRIEVAL domain task"
            )
            
            self.task_manager.add_reasoning(
                step="SELECT_SUBAGENT",
                reasoning="The retrieval-agent specializes in Q&A, synthesis, and traceability with TodoListMiddleware",
                decision="Delegate to retrieval-agent"
            )
            
            instruction = f"""Please answer this question completely and comprehensively:

QUESTION: {question}

Use these tools in sequence:
1. retrieve_context: Find relevant documents
2. rerank_context: Sort by relevance
3. answer_question: Generate a complete answer
4. get_traceability: Link to sources

IMPORTANT: Provide a complete, well-structured answer with:
- Direct answer to the question
- Supporting details from retrieved context
- Source attribution
- Confidence assessment"""
            
            result = self.master_agent.invoke({
                "messages": [{"role": "user", "content": instruction}]
            })
            
            task.delegated_to = "retrieval-agent"
            
            answer_text = ""
            if isinstance(result, dict):
                answer_text = (result.get('content') or result.get('answer') or 
                              result.get('text') or result.get('result') or str(result))
            else:
                answer_text = str(result)
            
            output_data = {
                "answer": answer_text if answer_text and answer_text.strip() else "Unable to generate answer",
                "raw_response": result,
                "todo_persisted": bool(todo_plan)
            }
            self.task_manager.complete_task(output_data=output_data)
            
            return {
                "success": True,
                "question": question,
                "result": output_data,
                "task_id": task.task_id,
                "todo_persisted": True,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        except Exception as e:
            if self.task_manager.active_task:
                self.task_manager.complete_task(error=str(e))
            
            return {
                "success": False,
                "question": question,
                "error": str(e)
            }

    def optimize_system(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize system with task tracking and persistent todo planning."""
        try:
            start_time = time.time()
            
            perf_summary = json.dumps(performance_history, indent=2)
            todo_task = f"""Plan and execute system optimization with persistent tracking:

Performance History:
{perf_summary}

Steps:
1. Analyze performance metrics and identify bottlenecks
2. Check system health (latency, cost, quality)
3. Estimate optimization impact
4. Recommend parameter changes
5. Plan and schedule optimizations

Confirm completion using write_todos and read_todos tools."""
            
            # Plan optimization via master agent with todo middleware
            todo_plan = self.master_agent.invoke({
                "messages": [{"role": "user", "content": f"Plan this optimization task: {todo_task}"}]
            })
            
            task = self.task_manager.plan_task(
                task_type=TaskType.HEALING,
                description="Optimize RAG system based on performance history",
                planned_subagent="healing-agent",
                input_data={"metrics_count": len(performance_history)}
            )
            
            self.task_manager.start_task(task)
            
            self.task_manager.add_reasoning(
                step="ANALYZE_INTENT",
                reasoning="User wants to optimize system performance with persistent todo tracking via FilesystemBackend",
                decision="Classify as HEALING/OPTIMIZATION domain task"
            )
            
            self.task_manager.add_reasoning(
                step="SELECT_SUBAGENT",
                reasoning="The healing-agent specializes in performance analysis and optimization with TodoListMiddleware",
                decision="Delegate to healing-agent"
            )
            
            instruction = f"""Analyze the following performance history and optimize the RAG system:

PERFORMANCE_HISTORY:
{json.dumps(performance_history, indent=2)}

Analysis steps:
1. Identify performance bottlenecks (latency, cost, quality)
2. Recommend optimization strategies using healing tools
3. Execute recommended optimizations
4. Return detailed analysis with expected improvements

Use healing tools:
- check_health: Evaluate system health
- estimate_cost: Calculate token efficiency
- optimize_params: Recommend parameter changes

Provide: ANALYSIS + RECOMMENDATIONS + EXPECTED_IMPROVEMENTS"""
            
            result = self.master_agent.invoke({
                "messages": [{"role": "user", "content": instruction}]
            })
            
            task.delegated_to = "healing-agent"
            output_data = {"result": result, "todo_persisted": bool(todo_plan)}
            self.task_manager.complete_task(output_data=output_data)
            
            return {
                "success": True,
                "result": result,
                "task_id": task.task_id,
                "todo_persisted": True,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        except Exception as e:
            if self.task_manager.active_task:
                self.task_manager.complete_task(error=str(e))
            
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # REPORTING METHODS
    # ========================================================================

    def get_task_report(self) -> Dict[str, Any]:
        """Get comprehensive task execution report with chain-of-thought"""
        return self.task_manager.get_task_summary()
    
    def print_task_report(self) -> None:
        """Print detailed task execution report with reasoning"""
        self.task_manager.print_task_report()
    
    def export_tasks(self) -> str:
        """Export all tasks as JSON with full traceability"""
        return self.task_manager.export_tasks_json()
    
    def get_todos(self) -> List[Dict[str, Any]]:
        """Get persistent todo list from FilesystemBackend"""
        todo_file = os.path.join(self.todo_dir, "todos.json")
        if os.path.exists(todo_file):
            try:
                with open(todo_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def print_todo_status(self) -> None:
        """Print persistent todo list status"""
        todos = self.get_todos()
        
        print(f"\n{'='*80}")
        print(f"  PERSISTENT TODO LIST (FilesystemBackend)")
        print(f"{'='*80}\n")
        
        if not todos:
            print("No todos. Start with ingest_document(), ask_question(), or optimize_system().")
            return
        
        completed = sum(1 for t in todos if t.get("status") == "completed")
        total = len(todos)
        
        print(f"Progress: {completed}/{total} completed\n")
        
        for idx, todo in enumerate(todos, 1):
            status_icon = "[X]" if todo.get("status") == "completed" else "[ ]"
            print(f"{status_icon} {idx}. {todo.get('title', 'Untitled')}")
            if todo.get('description'):
                desc = todo.get('description')[:100]
                print(f"   {desc}")
        
        print(f"\n{'='*80}\n")
    
    def print_combined_report(self) -> None:
        """Print combined report with both TaskManager and FilesystemBackend todos"""
        print(f"\n{'='*80}")
        print(f"  CONSOLIDATED EXECUTION REPORT")
        print(f"  (TaskManager Chain-of-Thought + FilesystemBackend Todos)")
        print(f"{'='*80}\n")
        
        # Print task report
        self.print_task_report()
        
        # Print todo status
        self.print_todo_status()
        
        print(f"Todos persisted to: {self.todo_dir}")
    
    def adjust_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate config adjustment to config subagent"""
        try:
            result = self.master_agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"Use the config-agent to adjust configuration with these updates: {json.dumps(updates)}"
                }]
            })
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
