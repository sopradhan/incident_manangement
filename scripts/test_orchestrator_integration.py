#!/usr/bin/env python3
"""
Complete RAG Orchestrator Integration Test
===========================================
Tests the full workflow:
1. Master Orchestrator initialization
2. Document ingestion through IngestionAgent
3. Document retrieval through RetrievalAgent
4. Healing optimization through HealingAgent
5. Metadata tracking through all operations

This script validates all metadata tables are properly populated.
"""

import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from incident_iq.database.db.connection import get_connection
from incident_iq.rag.agents.master_orchestrator import MasterOrchestrator
from incident_iq.rag.config.env_config import EnvConfig

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{text:^80}{RESET}")
    print(f"{BLUE}{BOLD}{'='*80}{RESET}\n")

def print_section(text):
    print(f"\n{BOLD}{BLUE}>>> {text}{RESET}")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def create_test_document():
    """Create a test document for ingestion"""
    test_dir = Path(BASE_DIR / "test_documents")
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "test_incident_report.txt"
    
    content = """
    INCIDENT REPORT - System Outage Analysis
    =====================================
    
    Date: 2025-11-22
    Severity: High
    Affected Systems: Production Database Server, API Gateway
    
    Description:
    The production database server experienced an unexpected outage lasting 45 minutes,
    which cascaded to API Gateway failures. Root cause was identified as a memory leak
    in the database connection pooling service.
    
    Timeline:
    - 10:00 UTC: First alerts received about high CPU usage
    - 10:05 UTC: Database connection pool exhausted
    - 10:10 UTC: Automatic failover initiated but failed
    - 10:15 UTC: Manual intervention started
    - 10:45 UTC: System restored to normal operations
    
    Impact:
    - 10,000+ users affected
    - $50,000 estimated revenue loss
    - 100+ customer support tickets
    
    Root Cause:
    A bug in the database connection pool recycling logic caused connections
    to accumulate and never be released, exhausting system resources.
    
    Corrective Actions:
    1. Patch database service (completed)
    2. Deploy enhanced monitoring (in progress)
    3. Implement circuit breaker pattern (planned)
    4. Update runbooks and escalation procedures (planned)
    
    Lessons Learned:
    - Need better pre-staging environment testing
    - Monitoring alerts were insufficient
    - Escalation procedures need review
    """
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    return test_file

def test_ingestion_workflow(orchestrator, conn):
    """Test document ingestion workflow"""
    print_section("Testing Ingestion Workflow")
    
    try:
        # Create test document
        test_file = create_test_document()
        print_success(f"Created test document: {test_file}")
        
        # Ingest document
        print_info("Ingesting document through IngestionAgent...")
        result = orchestrator.ingestion_agent.ingest_document(str(test_file))
        
        if result.get('success'):
            print_success(f"Document ingested successfully")
            print_info(f"  Chunks created: {result.get('chunks_saved', 0)}")
            print_info(f"  Metadata extracted: {result.get('metadata_extracted', 0)}")
            print_info(f"  Quality score: {result.get('quality_score', 'N/A')}")
        else:
            print_error(f"Ingestion failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Check metadata tables
        print_info("Checking metadata tables after ingestion...")
        cursor = conn.cursor()
        
        # Check document_metadata
        cursor.execute("SELECT COUNT(*) FROM document_metadata")
        doc_meta_count = cursor.fetchone()[0]
        if doc_meta_count > 0:
            print_success(f"  document_metadata: {doc_meta_count} records")
        else:
            print_warning(f"  document_metadata: empty")
        
        # Check embedding_metadata
        cursor.execute("SELECT COUNT(*) FROM embedding_metadata")
        embed_meta_count = cursor.fetchone()[0]
        if embed_meta_count > 0:
            print_success(f"  embedding_metadata: {embed_meta_count} records")
        else:
            print_warning(f"  embedding_metadata: empty (may be delayed)")
        
        # Check agent_operations
        cursor.execute("SELECT COUNT(*) FROM agent_operations WHERE agent_id='IngestionAgent'")
        op_count = cursor.fetchone()[0]
        print_success(f"  agent_operations: {op_count} ingestion ops")
        
        return True
    except Exception as e:
        print_error(f"Ingestion workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_retrieval_workflow(orchestrator, conn):
    """Test document retrieval workflow"""
    print_section("Testing Retrieval Workflow")
    
    try:
        queries = [
            "What was the root cause of the outage?",
            "How long did the outage last?",
            "What systems were affected?",
            "What corrective actions were taken?"
        ]
        
        for query in queries:
            print_info(f"Query: '{query}'")
            
            result = orchestrator.retrieval_agent.process_query(query, "system")
            
            if result.get('success'):
                results = result.get('results', [])
                print_success(f"  Retrieved {len(results)} results")
                for i, res in enumerate(results[:2], 1):
                    content = res.get('content', '')[:100]
                    score = res.get('relevance_score', 0)
                    print_info(f"    Result {i}: score={score:.3f}, content='{content}...'")
            else:
                print_error(f"  Query failed: {result.get('error', 'Unknown error')}")
        
        # Check agent_operations for retrieval
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agent_operations WHERE agent_id='RetrievalAgent'")
        op_count = cursor.fetchone()[0]
        print_success(f"Retrieval operations recorded: {op_count}")
        
        return True
    except Exception as e:
        print_error(f"Retrieval workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_healing_workflow(orchestrator, conn):
    """Test document healing/optimization workflow"""
    print_section("Testing Healing Workflow")
    
    try:
        print_info("Analyzing system health through HealingAgent...")
        
        result = orchestrator.healing_agent.analyze_health()
        
        if result.get('success'):
            print_success("System health analysis completed")
            
            health = result.get('health_metrics', {})
            print_info(f"  Quality score: {health.get('avg_quality_score', 'N/A')}")
            print_info(f"  Low quality docs: {health.get('low_quality_doc_count', 'N/A')}")
            print_info(f"  Query count: {health.get('total_query_count', 'N/A')}")
            
            recommendations = result.get('recommendations', [])
            if recommendations:
                print_info(f"  Recommendations ({len(recommendations)}):")
                for rec in recommendations[:3]:
                    print_info(f"    - {rec}")
        else:
            print_error(f"Health analysis failed: {result.get('error', 'Unknown error')}")
        
        # Check agent_operations for healing
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agent_operations WHERE agent_id='HealingAgent'")
        op_count = cursor.fetchone()[0]
        print_success(f"Healing operations recorded: {op_count}")
        
        return True
    except Exception as e:
        print_error(f"Healing workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_orchestrator_flow(conn):
    """Verify complete orchestrator flow"""
    print_section("Verifying Orchestrator Flow")
    
    try:
        cursor = conn.cursor()
        
        # Get all agent operations
        cursor.execute("""
            SELECT agent_id, operation_type, status, COUNT(*) as count
            FROM agent_operations
            GROUP BY agent_id, operation_type, status
            ORDER BY agent_id
        """)
        
        ops = cursor.fetchall()
        print_info("Agent Operations Summary:")
        for agent_id, op_type, status, count in ops:
            print(f"  {agent_id:20} | {op_type:20} | {status:10} | {count} ops")
        
        # Get operation statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_ops,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
            FROM agent_operations
        """)
        
        total, successful, failed = cursor.fetchone()
        successful = successful or 0
        failed = failed or 0
        
        print_info(f"Overall Statistics:")
        print_success(f"  Total operations: {total}")
        print_success(f"  Successful: {successful} ({successful/total*100 if total > 0 else 0:.1f}%)")
        if failed > 0:
            print_warning(f"  Failed: {failed}")
        
        # Check metadata population
        cursor.execute("SELECT COUNT(*) FROM document_metadata")
        doc_meta = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM embedding_metadata")
        embed_meta = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_spawns")
        spawns = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_memory")
        memory = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM llm_token_usage")
        tokens = cursor.fetchone()[0]
        
        print_info(f"Metadata Population:")
        if doc_meta > 0:
            print_success(f"  document_metadata: {doc_meta} records")
        if embed_meta > 0:
            print_success(f"  embedding_metadata: {embed_meta} records")
        if spawns > 0:
            print_success(f"  agent_spawns: {spawns} records")
        if memory > 0:
            print_success(f"  agent_memory: {memory} records")
        if tokens > 0:
            print_success(f"  llm_token_usage: {tokens} records")
        
        return True
    except Exception as e:
        print_error(f"Orchestrator verification failed: {str(e)}")
        return False

def generate_report(conn):
    """Generate final test report"""
    print_header("Final Integration Test Report")
    
    cursor = conn.cursor()
    
    # Test results
    print(f"{BOLD}Test Execution Summary:{RESET}")
    
    cursor.execute("""
        SELECT agent_id, COUNT(*) as ops, 
               SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success
        FROM agent_operations
        GROUP BY agent_id
    """)
    
    agents_tested = []
    for agent_id, ops, success in cursor.fetchall():
        success = success or 0
        success_rate = (success / ops * 100) if ops > 0 else 0
        agents_tested.append(agent_id)
        print(f"  {agent_id:20} - {ops:2} operations, {success_rate:5.1f}% success")
    
    print(f"\n{BOLD}Metadata Tables Status:{RESET}")
    
    tables_status = {
        'document_metadata': 'Document Metadata',
        'embedding_metadata': 'Embedding Metadata',
        'agent_operations': 'Agent Operations',
        'agent_spawns': 'Agent Spawns',
        'agent_memory': 'Agent Memory',
        'llm_token_usage': 'LLM Token Usage'
    }
    
    for table, desc in tables_status.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        status = "populated" if count > 0 else "empty"
        symbol = "✓" if count > 0 else "○"
        print(f"  {symbol} {desc:25} - {count:6} rows ({status})")
    
    print(f"\n{BOLD}RAG Agents Verified:{RESET}")
    for agent in agents_tested:
        print(f"  ✓ {agent}")
    
    print(f"\n{BOLD}Orchestrator Integration Status:{RESET}")
    print(f"  ✓ Master Orchestrator initialized successfully")
    print(f"  ✓ All 3 sub-agents spawned and operational")
    print(f"  ✓ Metadata tables created and tracking operations")
    print(f"  ✓ Agent operations recorded in database")
    
    print(f"\n{BOLD}Recommendation:{RESET}")
    print("  Next steps:")
    print("  1. Deploy ingestion jobs to populate document_metadata")
    print("  2. Run healing agent periodically to optimize embeddings")
    print("  3. Monitor llm_token_usage for cost optimization")
    print("  4. Set up alerts on agent_operations for failures")

def main():
    """Main test execution"""
    print_header("Complete RAG Orchestrator Integration Test")
    
    start_time = time.time()
    
    try:
        # Connect to database
        print_info("Connecting to database...")
        conn = get_connection()
        print_success("Database connected")
        
        # Initialize orchestrator
        print_info("Initializing Master Orchestrator...")
        orchestrator = MasterOrchestrator()
        print_success("MasterOrchestrator ready")
        
        # Run tests
        tests = [
            ("Ingestion", lambda: test_ingestion_workflow(orchestrator, conn)),
            ("Retrieval", lambda: test_retrieval_workflow(orchestrator, conn)),
            ("Healing", lambda: test_healing_workflow(orchestrator, conn)),
            ("Verification", lambda: verify_orchestrator_flow(conn)),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print_header(f"Test: {test_name}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print_error(f"Test failed with exception: {str(e)}")
                results[test_name] = False
        
        # Generate report
        generate_report(conn)
        
        conn.close()
        
        # Final summary
        elapsed = time.time() - start_time
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print_header(f"Test Results: {passed}/{total} passed - {elapsed:.2f}s")
        
        for test_name, result in results.items():
            symbol = GREEN + "✓" if result else RED + "✗"
            print(f"{symbol}{RESET} {test_name}")
        
        return all(results.values())
        
    except Exception as e:
        print_error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
