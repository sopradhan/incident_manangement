"""IngestionAgent - Clean, config-driven document ingestion for any format and domain"""
import json
import time
from pathlib import Path
from typing import Union, List, Dict, Any
from deepagents import create_deep_agent
from langchain_core.tools import tool
from ..config.prompt_loader import PromptLoader
from ..config.env_config import EnvConfig


class TableIngestionConfig:
    @staticmethod
    def load_sqlite_tables() -> List[Dict]:
        try:
            config_path = Path(__file__).parent.parent / "config" / "data_sources.json"
            with open(config_path) as f:
                config = json.load(f)
            return config.get("data_sources", {}).get("sqlite", {}).get("tables", [])
        except:
            return []
    
    @staticmethod
    def get_chunking_config() -> Dict:
        config_path = Path(__file__).parent.parent / "config" / "data_sources.json"
        with open(config_path) as f:
            config = json.load(f)
        
        sqlite_config = config.get("data_sources", {}).get("sqlite", {})
        chunking = sqlite_config.get("chunking", {})
        
        return {
            "enabled": chunking.get("enabled", True),
            "strategy": chunking.get("strategy", "semantic"),
            "chunk_size": chunking.get("chunk_size", 512),
            "overlap": chunking.get("overlap", 50)
        }


class IngestionAgent:
    def __init__(self, services: dict, config: dict, master_orchestrator=None):
        self.services = services
        self.master = master_orchestrator
        self.name = "IngestionAgent"
        self.db_path = EnvConfig.get_db_path()
        self.chunk_size = config.get('chunk_size', 500)
        self.chunk_overlap = config.get('chunk_overlap', 50)
        
        # Create deepagents agent with ingestion tools
        system_prompt = PromptLoader.get_system_prompt('ingestion_agent')
        tools = self._create_tools()
        
        self.agent = create_deep_agent(
            tools=tools,
            system_prompt=system_prompt,
            model=services['llm'].get_model()
        )
    
    def _create_tools(self) -> list:
        from ..tools.ingestion_tools import (
            chunk_document_tool, extract_metadata_tool, save_to_vectordb_tool,
            ingest_sqlite_table_tool
        )
        from ..tools.markdown_converter import convert_to_markdown, file_to_markdown, sqlite_table_to_markdown
        return [
            chunk_document_tool, 
            extract_metadata_tool, 
            save_to_vectordb_tool,
            ingest_sqlite_table_tool,
            convert_to_markdown,
            file_to_markdown,
            sqlite_table_to_markdown
        ]
    
    def ingest_data(self, data: Union[str, List, Dict],
                   metadata: Dict = None, domain: str = None) -> Dict[str, Any]:
        start = time.time()
        
        try:
            # Normalize input to documents
            documents = self._normalize_input(data)
            
            # Auto-detect domain if not provided (LLM-based, config-driven)
            if domain is None:
                domain = self._detect_domain(documents)
            
            # Extract metadata if not provided
            if metadata is None:
                metadata = self._extract_metadata(documents, domain)
            
            # Process each document
            ingested_docs = []
            for i, doc in enumerate(documents):
                doc_id = f"{domain}_doc_{i}_{int(time.time())}"
                result = self._process_document(doc, doc_id, domain)
                if result.get('success'):
                    ingested_docs.append(doc_id)
            
            elapsed = int((time.time() - start) * 1000)
            
            return {
                'success': len(ingested_docs) > 0,
                'documents_ingested': len(ingested_docs),
                'domain': domain,
                'metadata': metadata,
                'doc_ids': ingested_docs,
                'time_ms': elapsed
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time_ms': int((time.time() - start) * 1000)
            }
    
    def _normalize_input(self, data: Union[str, List, Dict]) -> List[str]:
        from ..tools.markdown_converter import convert_to_markdown, file_to_markdown
        documents = []
        
        if isinstance(data, str):
            path = Path(data)
            if path.exists():
                result = json.loads(file_to_markdown(data))
                if result.get('success'):
                    documents.append(result.get('markdown', path.read_text()))
                else:
                    documents.append(path.read_text())
            else:
                documents.append(data)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    path = Path(item)
                    if path.exists():
                        result = json.loads(file_to_markdown(item))
                        if result.get('success'):
                            documents.append(result.get('markdown', path.read_text()))
                        else:
                            documents.append(path.read_text())
                    else:
                        documents.append(item)
                elif isinstance(item, dict):
                    result = json.loads(convert_to_markdown(item))
                    if result.get('success'):
                        documents.append(result.get('markdown', json.dumps(item, indent=2)))
                    else:
                        documents.append(json.dumps(item, indent=2))
                else:
                    documents.append(str(item))
        
        elif isinstance(data, dict):
            result = json.loads(convert_to_markdown(data))
            if result.get('success'):
                documents.append(result.get('markdown', json.dumps(data, indent=2)))
            else:
                documents.append(json.dumps(data, indent=2))
        else:
            documents.append(str(data))
        
        return documents
    
    def _detect_domain(self, documents: List[str]) -> str:
        sample = " ".join(documents[:2])[:500]
        
        prompt = PromptLoader.format_prompt(
            'domain_detection', 'classify_domain',
            sample_text=sample
        )
        
        response = self.services['llm'].generate_response(prompt).strip().lower()
        
        valid_domains = PromptLoader.get_config('domain_detection', {}).get('valid_domains', 
                                                 ['finance', 'travel', 'medical', 'legal', 'technical', 'general'])
        return response if response in valid_domains else 'general'
    
    def _extract_metadata(self, documents: List[str], domain: str) -> Dict:
        combined = " ".join(documents)
        return {
            'document_count': len(documents),
            'total_characters': len(combined),
            'domain': domain,
            'has_urls': 'http' in combined.lower(),
            'has_emails': '@' in combined,
        }
    
    def _process_document(self, doc: str, doc_id: str, domain: str) -> Dict:
        return {
            'success': True,
            'doc_id': doc_id,
            'domain': domain,
            'chunks_processed': len(doc.split()) // self.chunk_size
        }
    
    def ingest_document(self, file_path: str) -> Dict:
        return self.ingest_data(file_path)
    
    def ingest_document_text(self, text: str, doc_id: str = None) -> Dict:
        result = self.ingest_data(text)
        if doc_id and result['success']:
            result['doc_id'] = doc_id
        return result
    
    def ingest_directory(self, dir_path: str) -> Dict:
        path = Path(dir_path)
        if not path.is_dir():
            return {"success": False, "error": f"Not a directory: {dir_path}"}
        
        results = []
        for file_path in path.rglob('*.txt'):
            result = self.ingest_document(str(file_path))
            results.append({"file": file_path.name, "success": result.get('success')})
        
        return {
            "success": True,
            "total": len(results),
            "successful": sum(1 for r in results if r['success']),
            "results": results
        }
    
    def ingest_sqlite_table(self, table_config: Dict) -> Dict[str, Any]:
        from ..tools.ingestion_tools import ingest_sqlite_table_tool
        
        table_name = table_config.get("name")
        text_columns = table_config.get("text_columns", [])
        metadata_columns = table_config.get("metadata_columns", [])
        chunk_strategy = table_config.get("chunk_strategy", "per_record")
        where_clause = table_config.get("where_clause")
        
        chunking = TableIngestionConfig.get_chunking_config()
        
        result_json = ingest_sqlite_table_tool(
            table_name=table_name,
            text_columns=text_columns,
            metadata_columns=metadata_columns,
            db_path=self.db_path,
            llm_service=self.services.get('llm'),
            vectordb_service=self.services.get('vectordb'),
            chunk_size=chunking.get("chunk_size", 512),
            chunk_overlap=chunking.get("overlap", 50),
            chunk_strategy=chunk_strategy,
            where_clause=where_clause
        )
        
        return json.loads(result_json)
    
    def ingest_all_configured_tables(self) -> Dict[str, Any]:
        tables = TableIngestionConfig.load_sqlite_tables()
        
        if not tables:
            return {
                "success": False,
                "error": "No SQLite tables configured for ingestion",
                "tables_processed": 0
            }
        
        results = {
            "total_tables": len(tables),
            "successful_tables": 0,
            "total_records_processed": 0,
            "total_chunks_created": 0,
            "table_results": []
        }
        
        for table_config in tables:
            result = self.ingest_sqlite_table(table_config)
            
            results["table_results"].append({
                "table": table_config.get("name"),
                "success": result.get("success"),
                "records_processed": result.get("records_processed", 0),
                "chunks_created": result.get("total_chunks_created", 0),
                "error": result.get("error")
            })
            
            if result.get("success"):
                results["successful_tables"] += 1
                results["total_records_processed"] += result.get("records_processed", 0)
                results["total_chunks_created"] += result.get("total_chunks_created", 0)
        
        results["success"] = results["successful_tables"] > 0
        
        return results
