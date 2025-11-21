#!/usr/bin/env python
"""Process classifier outputs through RAG Master Orchestrator for corrective actions."""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Minimal logging config
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
for mod in ['incident_iq.rag', 'urllib3', 'chromadb', 'sentence_transformers']:
    logging.getLogger(mod).setLevel(logging.WARNING)

try:
    import sqlite3
    from dotenv import load_dotenv
    from incident_iq.database.models.classifier_output import ClassifierOutputsModel
    from incident_iq.rag.agents.master_orchestrator import MasterOrchestrator
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
DB_PATH = src_dir / "incident_iq" / "database" / "data" / os.getenv("DB_NAME", "incident_iq.db")
RAG_CONFIG = src_dir / "incident_iq" / "rag" / "config"


class CorrectiveActionProcessor:
    """Generate corrective actions via RAG orchestrator"""
    
    SEVERITY_MAP = {'S1': 'Critical', 'S2': 'High', 'S3': 'Medium', 'S4': 'Low'}
    
    def __init__(self):
        try:
            self.db_conn = sqlite3.connect(str(DB_PATH))
            self.db_conn.row_factory = sqlite3.Row
            self.classifier = ClassifierOutputsModel(self.db_conn)
            self.orchestrator = MasterOrchestrator(str(RAG_CONFIG))
            self.llm_service = self.orchestrator.llm_service
            self._last_result = {}
            logger.info("✓ Initialized")
        except Exception as e:
            logger.error(f"Init failed: {e}")
            raise
    
    def fetch_records(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch unprocessed records"""
        try:
            cursor = self.db_conn.execute(
                "SELECT * FROM classifier_outputs WHERE corrective_action IS NULL LIMIT ?", (limit,)
            )
            records = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Fetched {len(records)} records")
            return records
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            return []
    
    def generate_action(self, record: Dict[str, Any]) -> Optional[str]:
        """Generate corrective action"""
        try:
            payload_id = record.get('payload_id', 'N/A')
            severity = self.SEVERITY_MAP.get(record.get('severity_id', 'S3'), 'Medium')
            resource = record.get('resource_type', 'Unknown')
            env = record.get('environment', 'unknown')
            payload = record.get('payload', '')
            
            logger.info(f"Processing: {payload_id} ({severity}/{resource})")
            
            query = f"""You are an Azure Cloud Engineer. Resolve this incident:
- ID: {payload_id}
- Severity: {severity}
- Resource: {resource}
- Environment: {env}
- Issue: {payload}

Provide step-by-step corrective action."""
            
            result = self.orchestrator.ask_question(query, "system", enable_healing=True)
            self._last_result = result
            
            if result.get('success'):
                tokens = result.get('token_usage', {}).get('total', 0)
                answer = result.get('answer', '').strip()
                logger.info(f"  ✓ Generated {len(answer)} chars | Tokens: {tokens}")
                return answer
            else:
                logger.error(f"  ✗ {result.get('error', 'Unknown error')}")
                return None
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None
    
    def update_db(self, record_id: int, action: str) -> bool:
        """Update database"""
        try:
            self.db_conn.execute(
                "UPDATE classifier_outputs SET corrective_action = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (action, record_id)
            )
            self.db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.db_conn.rollback()
            return False
    
    def process_batch(self, limit: int = 5) -> Dict[str, Any]:
        """Process batch"""
        logger.info("=" * 60)
        logger.info("BATCH PROCESSING START")
        
        records = self.fetch_records(limit)
        if not records:
            logger.info("No records")
            return {'processed': 0, 'failed': 0, 'tokens': 0}
        
        processed, failed, total_tokens = 0, 0, 0
        agents, tags = set(), set()
        
        for record in records:
            try:
                action = self.generate_action(record)
                if action and self.update_db(record.get('id'), action):
                    processed += 1
                    tokens = self._last_result.get('token_usage', {}).get('total', 0)
                    total_tokens += tokens
                    agents.update(self._last_result.get('metadata', {}).get('agents_spawned', []))
                    tags.update(self._last_result.get('tags', []))
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error: {e}")
                failed += 1
        
        summary = f"\nRESULTS: ✓ {processed} | ✗ {failed} | Tokens: {total_tokens}"
        summary += f" | Agents: {', '.join(agents) or 'N/A'}"
        logger.info(summary)
        logger.info("=" * 60)
        
        return {
            'processed': processed,
            'failed': failed,
            'tokens': total_tokens,
            'agents': list(agents),
            'tags': list(tags)
        }
    
    def close(self):
        if self.db_conn:
            self.db_conn.close()


def main():
    processor = None
    try:
        processor = CorrectiveActionProcessor()
        return processor.process_batch(limit=5)
    except Exception as e:
        logger.error(f"Fatal: {e}")
        return {'error': str(e)}
    finally:
        if processor:
            processor.close()


if __name__ == "__main__":
    main()
