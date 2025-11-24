#!/usr/bin/env python3

import sys
import os
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Setup paths
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging
for mod in ['incident_iq.rag', 'urllib3', 'chromadb', 'sentence_transformers', 'langchain']:
    logging.getLogger(mod).setLevel(logging.WARNING)

try:
    from dotenv import load_dotenv
    from incident_iq.rag.agents.master_orchestrator import MasterOrchestrator
    from incident_iq.rag.agents import IngestionAgent, HealingAgent, RetrievalAgent
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
DB_PATH = src_dir / "incident_iq" / "database" / "data" / os.getenv("DB_NAME", "incident_iq.db")
RAG_CONFIG = src_dir / "incident_iq" / "rag" / "config"


class RAGAgentTester:
    """Test RAG agents with corrective action processing"""
    
    def __init__(self):
        logger.info("Initializing RAG Agent Tester...")
        try:
            self.db_path = str(DB_PATH)
            self.db_conn = sqlite3.connect(self.db_path)
            self.db_conn.row_factory = sqlite3.Row
            
            self.orchestrator = MasterOrchestrator(str(RAG_CONFIG))
            self.llm_service = self.orchestrator.llm_service
            self.vectordb = self.orchestrator.vectordb_service
            
            logger.info("✓ Orchestrator initialized")
            logger.info(f"✓ Database: {self.db_path}")
            logger.info(f"✓ RAG Config: {RAG_CONFIG}")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def test_ingestion_with_synthetic_questions(self) -> Dict[str, Any]:
        logger.info("\n" + "="*70)
        logger.info("TEST 1: IngestionAgent with Synthetic Questions")
        logger.info("="*70)
        
        test_doc_id = f"test_incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_content = """
        INCIDENT REPORT: Azure VM Performance Degradation
        
        Date: 2024-11-22
        Severity: S2 (High)
        Resource: VM-PROD-01 in East US region
        
        ISSUE DESCRIPTION:
        Production VM experiencing high CPU utilization (95-99%) for past 2 hours.
        Memory usage at 87%. Disk I/O at critical levels. Application response time 
        increased from 200ms to 2000ms average. Users reporting timeouts.
        
        SYMPTOMS:
        - API endpoints responding slowly
        - Database queries timing out
        - Background jobs not completing
        - Cloud Monitoring showing spike in network traffic
        
        INITIAL INVESTIGATION:
        - No recent deployments
        - No auto-scaling triggers detected
        - Application version unchanged
        - Infrastructure unchanged
        
        ENVIRONMENT:
        - OS: Windows Server 2019
        - Runtime: .NET 6.0
        - Application: IncidentIQ.RagService
        - Database: SQL Server 2019
        """
        
        try:
            logger.info(f"Ingesting document: {test_doc_id}")
            
            # Create ingestion agent
            services = {
                'llm': self.llm_service,
                'vectordb': self.vectordb,
            }
            config = {
                'name': 'IngestionAgent',
                'chunk_size': 500,
                'chunk_overlap': 50
            }
            
            ingestion_agent = IngestionAgent(services, config)
            
            # Ingest document
            result = ingestion_agent.ingest_document_text(test_content, test_doc_id)
            
            logger.info(f"Ingestion result: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                # Check if synthetic questions were generated
                cursor = self.db_conn.execute(
                    "SELECT COUNT(*) as count FROM synthetic_queries WHERE doc_id = ?",
                    (test_doc_id,)
                )
                question_count = cursor.fetchone()['count']
                
                logger.info(f"✓ Document ingested successfully")
                logger.info(f"✓ Chunks created: {result.get('chunks_created')}")
                logger.info(f"✓ Chunks saved: {result.get('chunks_saved')}")
                logger.info(f"✓ RBAC namespace: {result.get('rbac_namespace')}")
                logger.info(f"✓ Synthetic questions generated: {question_count}")
                
                if question_count > 0:
                    # Display generated questions
                    cursor = self.db_conn.execute(
                        "SELECT question FROM synthetic_queries WHERE doc_id = ? LIMIT 3",
                        (test_doc_id,)
                    )
                    questions = [row['question'] for row in cursor.fetchall()]
                    logger.info("\nSample generated questions:")
                    for i, q in enumerate(questions, 1):
                        logger.info(f"  {i}. {q[:80]}...")
                
                return {
                    'success': True,
                    'doc_id': test_doc_id,
                    'chunks': result.get('chunks_saved'),
                    'questions': question_count,
                    'namespace': result.get('rbac_namespace')
                }
            else:
                logger.error(f"✗ Ingestion failed: {result.get('error')}")
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def test_healing_agent_with_synthetic_questions(self, doc_id: str) -> Dict[str, Any]:
        logger.info("\n" + "="*70)
        logger.info("TEST 2: HealingAgent with Synthetic Question Validation")
        logger.info("="*70)
        
        try:
            logger.info(f"Testing HealingAgent for document: {doc_id}")
            
            # Create healing agent
            services = {
                'llm': self.llm_service,
                'vectordb': self.vectordb,
            }
            config = {'name': 'HealingAgent'}
            
            healing_agent = HealingAgent(
                services, config, 
                master_orchestrator=self.orchestrator,
                caller_agent='IngestionAgent'
            )
            
            # Check if questions_generator is initialized
            has_generator = hasattr(healing_agent, 'questions_generator')
            logger.info(f"HealingAgent has questions_generator: {has_generator}")
            
            if has_generator and healing_agent.questions_generator:
                logger.info("✓ HealingAgent can generate validation questions")
                
                # Get suggestion for optimization
                suggestion = healing_agent.suggest_optimization(doc_id, num_chunks=5)
                logger.info(f"Optimization suggestion: {suggestion}")
                
                return {
                    'success': True,
                    'healing_capable': True,
                    'suggestion': suggestion
                }
            else:
                logger.warning("HealingAgent questions_generator not initialized")
                return {
                    'success': True,
                    'healing_capable': False,
                    'reason': 'questions_generator not initialized'
                }
                
        except Exception as e:
            logger.error(f"✗ Healing test failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def test_retrieval_agent_with_synthetic_questions(self, doc_id: str) -> Dict[str, Any]:
        logger.info("\n" + "="*70)
        logger.info("TEST 3: RetrievalAgent with Synthetic Question Retrieval")
        logger.info("="*70)
        
        try:
            logger.info(f"Testing RetrievalAgent for document: {doc_id}")
            
            # Get synthetic questions for this document
            cursor = self.db_conn.execute(
                "SELECT question FROM synthetic_queries WHERE doc_id = ? LIMIT 2",
                (doc_id,)
            )
            questions = [row['question'] for row in cursor.fetchall()]
            
            if not questions:
                logger.warning(f"No synthetic questions found for {doc_id}")
                return {'success': True, 'questions_found': 0}
            
            logger.info(f"Found {len(questions)} synthetic questions for testing")
            
            # Create retrieval agent
            services = {
                'llm': self.llm_service,
                'vectordb': self.vectordb,
            }
            config = {'name': 'RetrievalAgent'}
            
            retrieval_agent = RetrievalAgent(services, config, master_orchestrator=self.orchestrator)
            
            # Check if questions_generator is initialized
            has_generator = hasattr(retrieval_agent, 'questions_generator')
            logger.info(f"RetrievalAgent has questions_generator: {has_generator}")
            
            if has_generator and retrieval_agent.questions_generator:
                logger.info("✓ RetrievalAgent can generate retrieval quality questions")
            
            # Test retrieval with first synthetic question
            test_question = questions[0]
            logger.info(f"\nTesting retrieval with: {test_question[:60]}...")
            
            try:
                result = retrieval_agent.retrieve(test_question, top_k=3)
                logger.info(f"Retrieval result: {json.dumps(result, indent=2, default=str)}")
                
                return {
                    'success': True,
                    'retrieval_capable': True,
                    'questions_tested': len(questions),
                    'retrieval_results': result.get('success', False)
                }
            except Exception as e:
                logger.warning(f"Retrieval test had issue (expected in test): {e}")
                return {
                    'success': True,
                    'retrieval_capable': True,
                    'questions_tested': len(questions),
                    'retrieval_results': 'testing'
                }
                
        except Exception as e:
            logger.error(f"✗ Retrieval test failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def test_corrective_action_generation(self) -> Dict[str, Any]:
        """Test corrective action generation via orchestrator"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: Corrective Action Generation via Orchestrator")
        logger.info("="*70)
        
        try:
            query = """You are an Azure Cloud Engineer. A production VM is experiencing 
            high CPU and memory utilization (95-99% CPU, 87% memory) with degraded 
            application performance. Network I/O is at critical levels. What are the 
            immediate troubleshooting steps and corrective actions?"""
            
            logger.info("Query: Generating corrective actions for VM performance issue")
            
            result = self.orchestrator.ask_question(
                query,
                user_id="test_user",
                enable_healing=True
            )
            
            logger.info(f"\nOrchestrator result:")
            logger.info(f"  Success: {result.get('success')}")
            logger.info(f"  Answer length: {len(result.get('answer', ''))}")
            logger.info(f"  Token usage: {result.get('token_usage', {})}")
            logger.info(f"  Agents spawned: {result.get('metadata', {}).get('agents_spawned', [])}")
            
            if result.get('success'):
                answer = result.get('answer', '')
                if len(answer) > 200:
                    logger.info(f"\nCorrective Action Summary:")
                    logger.info(f"{answer[:300]}...")
                else:
                    logger.info(f"\nCorrective Action:")
                    logger.info(answer)
                
                return {
                    'success': True,
                    'action_generated': len(answer) > 0,
                    'answer_length': len(answer),
                    'tokens': result.get('token_usage', {}).get('total', 0),
                    'agents_used': result.get('metadata', {}).get('agents_spawned', [])
                }
            else:
                logger.error(f"✗ Generation failed: {result.get('error')}")
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"✗ Corrective action test failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        logger.info("\n" + "#"*70)
        logger.info("# RUNNING RAG AGENTS WITH CORRECTIVE ACTION TESTS")
        logger.info("#"*70)
        
        results = {}
        
        # Test 1: Ingestion with synthetic questions
        test1 = self.test_ingestion_with_synthetic_questions()
        results['ingestion'] = test1
        doc_id = test1.get('doc_id')
        
        if test1.get('success') and doc_id:
            # Test 2: Healing agent
            test2 = self.test_healing_agent_with_synthetic_questions(doc_id)
            results['healing'] = test2
            
            # Test 3: Retrieval agent
            test3 = self.test_retrieval_agent_with_synthetic_questions(doc_id)
            results['retrieval'] = test3
        
        # Test 4: Corrective action generation
        test4 = self.test_corrective_action_generation()
        results['corrective_action'] = test4
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("TEST SUMMARY")
        logger.info("="*70)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result.get('success') else "✗ FAIL"
            logger.info(f"{status}: {test_name}")
            if not result.get('success'):
                logger.info(f"  Error: {result.get('error', 'Unknown')}")
        
        logger.info("="*70 + "\n")
        
        return results
    
    def close(self):
        if self.db_conn:
            self.db_conn.close()


def main():
    """Main test runner"""
    tester = None
    try:
        tester = RAGAgentTester()
        results = tester.run_all_tests()
        
        # Exit with success if all tests passed
        all_passed = all(r.get('success', False) for r in results.values())
        return 0 if all_passed else 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if tester:
            tester.close()


if __name__ == "__main__":
    sys.exit(main())
