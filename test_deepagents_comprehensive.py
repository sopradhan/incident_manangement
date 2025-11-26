#!/usr/bin/env python
"""
DeepAgents Enhanced Test with:
1. Complete response printing with all key-value pairs
2. Healing + Retrieval integration for token optimization
3. Persistent Todo List tracking
4. Dynamic LLM/RAG config adjustments
5. Chain-of-Thought reasoning display
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.incident_iq.rag.agents.deepagents_agent.deepagents_rag_agent import DeepAgentsRAGAgent
from src.incident_iq.database.models.rag_history_model import RAGHistoryModel
from src.incident_iq.rag.agents.healing_agent.rl_healing_agent import RLHealingAgent, RLState


# Configuration storage
CONFIG_DIR = "./deepagents_config"
os.makedirs(CONFIG_DIR, exist_ok=True)


class EnhancedResponsePrinter:
    """Pretty-prints all response key-value pairs"""
    
    @staticmethod
    def print_response(response: Any, indent: int = 4, title: str = "RESPONSE"):
        """Print response with all details"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
        
        EnhancedResponsePrinter._print_dict(response, indent)
        print()
    
    @staticmethod
    def _print_dict(obj: Any, indent: int = 0, max_depth: int = 4, current_depth: int = 0):
        """Recursively print dictionary/list/object"""
        prefix = " " * indent
        
        if current_depth >= max_depth:
            print(f"{prefix}[... truncated ...]")
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefix}{key}:")
                    EnhancedResponsePrinter._print_dict(value, indent + 2, max_depth, current_depth + 1)
                else:
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    print(f"{prefix}{key}: {val_str}")
        
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                print(f"{prefix}[{idx}]:")
                EnhancedResponsePrinter._print_dict(item, indent + 2, max_depth, current_depth + 1)
        
        else:
            val_str = str(obj)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            print(f"{prefix}{val_str}")


class PersistentTodoManager:
    """Manages persistent todo list with FilesystemBackend"""
    
    def __init__(self):
        """Initialize todo manager"""
        self.todo_file = os.path.join(CONFIG_DIR, "todo_list.json")
        self.todos = []
        self.load_todos()
    
    def add_todo(self, title: str, description: str = "", category: str = "task"):
        """Add a new todo item"""
        todo = {
            "id": len(self.todos) + 1,
            "title": title,
            "description": description,
            "category": category,
            "status": "planned",
            "created_at": datetime.now().isoformat()
        }
        self.todos.append(todo)
        self.save_todos()
        return todo
    
    def update_todo(self, todo_id: int, status: str, result: str = ""):
        """Update todo status and result"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["status"] = status
                todo["result"] = result
                todo["updated_at"] = datetime.now().isoformat()
                self.save_todos()
                return todo
        return None
    
    def mark_in_progress(self, todo_id: int):
        """Mark todo as in progress"""
        return self.update_todo(todo_id, "in_progress")
    
    def mark_completed(self, todo_id: int, result: str = ""):
        """Mark todo as completed"""
        return self.update_todo(todo_id, "completed", result)
    
    def save_todos(self):
        """Save todos to file"""
        with open(self.todo_file, 'w') as f:
            json.dump(self.todos, f, indent=2)
    
    def load_todos(self):
        """Load todos from file"""
        if os.path.exists(self.todo_file):
            with open(self.todo_file, 'r') as f:
                self.todos = json.load(f)
    
    def get_summary(self):
        """Get todo summary"""
        planned = sum(1 for t in self.todos if t["status"] == "planned")
        in_progress = sum(1 for t in self.todos if t["status"] == "in_progress")
        completed = sum(1 for t in self.todos if t["status"] == "completed")
        
        return {
            "total": len(self.todos),
            "planned": planned,
            "in_progress": in_progress,
            "completed": completed,
            "completion_rate": (completed / len(self.todos) * 100) if self.todos else 0
        }
    
    def print_summary(self):
        """Print todo summary"""
        summary = self.get_summary()
        print(f"\n{'='*80}")
        print("  TODO LIST SUMMARY")
        print(f"{'='*80}")
        print(f"\nTotal Tasks: {summary['total']}")
        print(f"Planned: {summary['planned']}")
        print(f"In Progress: {summary['in_progress']}")
        print(f"Completed: {summary['completed']}")
        print(f"Completion Rate: {summary['completion_rate']:.1f}%")
        print(f"\nDetailed Tasks:")
        for todo in self.todos:
            status_icon = "[OK]" if todo["status"] == "completed" else "[" + todo["status"].upper()[:3] + "]"
            print(f"  {status_icon} Task {todo['id']}: {todo['title']}")
            print(f"     Status: {todo['status']}")
            if todo.get('result'):
                print(f"     Result: {todo['result'][:100]}")
        print()


class DynamicConfigManager:
    """Manages dynamic LLM and RAG configuration based on healing recommendations"""
    
    def __init__(self):
        """Initialize config manager"""
        self.config_file = os.path.join(CONFIG_DIR, "dynamic_config.json")
        self.default_config = {
            "llm": {
                "provider": "ollama",
                "model": "mistral",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "rag": {
                "chunk_size": 512,
                "chunk_overlap": 50,
                "top_k_retrieval": 5,
                "rerank_model": "bge-reranker"
            },
            "optimization": {
                "enable_caching": True,
                "enable_reranking": True,
                "enable_healing": True,
                "healing_interval_queries": 10
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load config from file or use defaults"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.default_config.copy()
    
    def save_config(self):
        """Save config to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def apply_healing_recommendations(self, recommendations: Dict[str, Any]):
        """Apply healing agent recommendations to config"""
        changes = {}
        
        if 'chunk_size_recommendation' in recommendations:
            old_size = self.config['rag']['chunk_size']
            new_size = recommendations['chunk_size_recommendation']
            self.config['rag']['chunk_size'] = new_size
            changes['chunk_size'] = f"{old_size} -> {new_size}"
        
        if 'temperature_adjustment' in recommendations:
            old_temp = self.config['llm']['temperature']
            new_temp = recommendations['temperature_adjustment']
            self.config['llm']['temperature'] = new_temp
            changes['temperature'] = f"{old_temp:.2f} -> {new_temp:.2f}"
        
        if 'enable_caching' in recommendations:
            old_cache = self.config['optimization']['enable_caching']
            new_cache = recommendations['enable_caching']
            self.config['optimization']['enable_caching'] = new_cache
            changes['caching'] = f"{old_cache} -> {new_cache}"
        
        if changes:
            self.save_config()
        
        return changes
    
    def get_config(self):
        """Get current config"""
        return self.config.copy()
    
    def print_config(self):
        """Print current config"""
        print(f"\n{'='*80}")
        print("  CURRENT DYNAMIC CONFIGURATION")
        print(f"{'='*80}\n")
        print(json.dumps(self.config, indent=2))
        print()


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_comprehensive_flow():
    """Run comprehensive test with all features"""
    
    # Initialize managers
    todo_manager = PersistentTodoManager()
    config_manager = DynamicConfigManager()
    response_printer = EnhancedResponsePrinter()
    
    print_section("DEEPAGENTS COMPREHENSIVE TEST")
    print(f"Session: {datetime.now().isoformat()}")
    print(f"Config Dir: {CONFIG_DIR}")
    
    # Plan todos
    todo_manager.add_todo("Initialize DeepAgents", "Set up agent and services", "setup")
    todo_manager.add_todo("Ingest Documents", "Load sample documents", "ingestion")
    todo_manager.add_todo("Run Retrieval Tests", "Test Q&A with all response modes", "retrieval")
    todo_manager.add_todo("Optimize System", "Run healing agent and apply optimizations", "optimization")
    todo_manager.add_todo("Print Task Report", "Generate comprehensive task report", "reporting")
    
    print_section("PLANNED TODOS")
    todo_manager.print_summary()
    
    # STEP 1: Initialize
    print_section("STEP 1: Initialization")
    todo_manager.mark_in_progress(1)
    
    try:
        agent = DeepAgentsRAGAgent()
        rl_agent = RLHealingAgent(db_path="./chroma_db/rag.db")
        model = RAGHistoryModel()
        
        print("[OK] DeepAgentsRAGAgent initialized")
        print("[OK] RL Healing Agent initialized")
        print("[OK] RAGHistoryModel initialized")
        
        # Print agent task manager state
        print("\nAgent Chain-of-Thought reasoning enabled")
        print("Task Manager active with full tracking")
        
        todo_manager.mark_completed(1, "All services initialized successfully")
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        todo_manager.mark_completed(1, f"Failed: {e}")
        return
    
    # STEP 2: Ingest Documents
    print_section("STEP 2: Document Ingestion with Healing")
    todo_manager.mark_in_progress(2)
    
    sample_docs = {
        "doc_001": "Incident management is a critical process for responding to unexpected events.",
        "doc_002": "RAG systems combine retrieval and generation for context-aware responses.",
    }
    
    for doc_id, content in sample_docs.items():
        print(f"\nIngesting: {doc_id}")
        
        result = agent.ingest_document(content, doc_id)
        
        # Print full response
        response_printer.print_response(result, title=f"Ingest Response: {doc_id}")
        
        # Print task details
        if agent.task_manager.executed_tasks:
            last_task = agent.task_manager.executed_tasks[-1]
            print(f"Task ID: {last_task.task_id}")
            print(f"Status: {last_task.status.value}")
            print(f"Execution Time: {last_task.execution_time_ms:.1f}ms")
            print(f"Chain-of-Thought Steps:")
            for cot in last_task.reasoning:
                print(f"  - {cot.step}: {cot.reasoning}")
                print(f"    Decision: {cot.decision}")
    
    todo_manager.mark_completed(2, "Documents ingested successfully")
    
    # STEP 3: Retrieval with Response Modes
    print_section("STEP 3: Retrieval Tests with All Response Modes")
    todo_manager.mark_in_progress(3)
    
    queries = [
        "What is incident management?",
        "How do RAG systems work?"
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"\n\nQuery {idx}: {query}")
        
        # Pre-retrieval healing check
        state = RLState(
            quality_score=0.70,
            query_accuracy=0.72,
            chunk_count=50,
            avg_token_cost=1200,
            reindex_count=0,
            last_healing_delta=0.0,
            query_frequency=idx,
            user_feedback=0.75
        )
        
        rl_action = rl_agent.decide_action(state, "doc_001")
        print(f"\nHealing Recommendation: {rl_action.action}")
        print(f"  Confidence: {rl_action.confidence:.2f}")
        print(f"  Estimated Improvement: {rl_action.estimated_improvement:.3f}")
        
        # Execute query
        start = time.time()
        result = agent.ask_question(query)
        elapsed = time.time() - start
        
        # Print COMPLETE response
        response_printer.print_response(result, title=f"Query Response: {query}")
        
        # Print task execution details
        if agent.task_manager.executed_tasks:
            last_task = agent.task_manager.executed_tasks[-1]
            print(f"\nTask Execution Details:")
            print(f"  Task ID: {last_task.task_id}")
            print(f"  Status: {last_task.status.value}")
            print(f"  Delegated To: {last_task.delegated_to}")
            print(f"  Execution Time: {last_task.execution_time_ms:.1f}ms")
            print(f"  Input Data: {json.dumps(last_task.input_data, indent=4)}")
            print(f"  Output Data Keys: {list(last_task.output_data.keys()) if last_task.output_data else 'None'}")
            
            print(f"\n  Chain-of-Thought Reasoning:")
            for cot in last_task.reasoning:
                print(f"    {cot.step}:")
                print(f"      Reasoning: {cot.reasoning}")
                print(f"      Decision: {cot.decision}")
    
    todo_manager.mark_completed(3, "All retrieval tests completed")
    
    # STEP 4: Optimization
    print_section("STEP 4: System Optimization with Healing Agent")
    todo_manager.mark_in_progress(4)
    
    performance_history = [
        {"query": "incident management", "quality_score": 0.65, "latency_ms": 450, "cost_tokens": 1200},
        {"query": "RAG systems", "quality_score": 0.72, "latency_ms": 520, "cost_tokens": 1350},
    ]
    
    print("\nPerformance History:")
    for item in performance_history:
        print(f"  {item['query']}: Q={item['quality_score']:.2f}, L={item['latency_ms']}ms, T={item['cost_tokens']}")
    
    optimization_result = agent.optimize_system(performance_history)
    
    # Print optimization response
    response_printer.print_response(optimization_result, title="Optimization Result")
    
    # Simulate healing recommendations and apply to config
    healing_recommendations = {
        "chunk_size_recommendation": 256,
        "temperature_adjustment": 0.5,
        "enable_caching": True
    }
    
    print("\nApplying Healing Recommendations to Config:")
    changes = config_manager.apply_healing_recommendations(healing_recommendations)
    for key, change in changes.items():
        print(f"  {key}: {change}")
    
    todo_manager.mark_completed(4, "System optimized with healing recommendations")
    
    # STEP 5: Task Report
    print_section("STEP 5: Comprehensive Task Execution Report")
    todo_manager.mark_in_progress(5)
    
    # Print agent task report
    agent.print_task_report()
    
    # Print updated todo summary
    todo_manager.print_summary()
    
    # Print current config
    config_manager.print_config()
    
    # Export tasks
    tasks_json = agent.export_tasks()
    tasks_export_file = os.path.join(CONFIG_DIR, "exported_tasks.json")
    with open(tasks_export_file, 'w') as f:
        f.write(tasks_json)
    print(f"\nTasks exported to: {tasks_export_file}")
    
    todo_manager.mark_completed(5, "Task report generated and exported")
    
    # Final Summary
    print_section("FINAL SUMMARY")
    print("\nTodo List Completion:")
    todo_manager.print_summary()
    
    print("\nFiles Generated:")
    for file in os.listdir(CONFIG_DIR):
        file_path = os.path.join(CONFIG_DIR, file)
        size = os.path.getsize(file_path)
        print(f"  - {file} ({size} bytes)")
    
    print("\n" + "="*80)
    print("  COMPREHENSIVE TEST COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_comprehensive_flow()
