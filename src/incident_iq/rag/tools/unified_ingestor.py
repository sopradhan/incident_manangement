import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .doc_converter import DocConverter

logger = logging.getLogger(__name__)

class UnifiedIngestor:
    def __init__(self, llm_service, vectordb_service, db_path: str):
        self.llm = llm_service
        self.vectordb = vectordb_service
        self.db_path = db_path
        self.converter = DocConverter()
        self.chunk_size = 512
        self.chunk_overlap = 50

    def ingest_file(self, file_path: str, domain: str = "general", rbac_tag: str = "public") -> Dict[str, Any]:
        result = self.converter.convert(file_path)
        if result["status"] == "error":
            return result
        
        markdown = result["markdown"]
        filename = result["filename"]
        chunks = self._chunk_text(markdown, self.chunk_size, self.chunk_overlap)
        
        doc_id = f"{Path(filename).stem}_{len(chunks)}_chunks"
        metadata = {"filename": filename, "domain": domain, "rbac_tag": rbac_tag, "chunk_count": len(chunks), "source": "file"}
        
        return self._save_chunks(doc_id, chunks, metadata)

    def ingest_sqlite_table(self, db_path: str, table_name: str, text_columns: List[str], metadata_columns: Optional[List[str]] = None, domain: str = "database", rbac_tag: str = "public") -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            conn.close()
            all_text = "\n\n".join([" | ".join([str(row[col]) for col in text_columns if col in row.keys()]) for row in rows])
            chunks = self._chunk_text(all_text, self.chunk_size, self.chunk_overlap)
            doc_id = f"{table_name}_{len(chunks)}_chunks"
            metadata = {"table_name": table_name, "domain": domain, "rbac_tag": rbac_tag, "chunk_count": len(chunks), "source": "sqlite", "row_count": len(rows)}
            return self._save_chunks(doc_id, chunks, metadata)
        except Exception as e:
            logger.error(f"Error ingesting table {table_name}: {e}")
            return {"status": "error", "error": str(e), "table_name": table_name}

    def ingest_markdown(self, markdown_text: str, doc_id: str, domain: str = "general", rbac_tag: str = "public") -> Dict[str, Any]:
        chunks = self._chunk_text(markdown_text, self.chunk_size, self.chunk_overlap)
        metadata = {"doc_id": doc_id, "domain": domain, "rbac_tag": rbac_tag, "chunk_count": len(chunks), "source": "markdown"}
        return self._save_chunks(doc_id, chunks, metadata)

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return [c for c in chunks if c.strip()]

    def _save_chunks(self, doc_id: str, chunks: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            embeddings = [self.llm.generate_embedding(chunk) for chunk in chunks]
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            
            self.vectordb.collection.upsert(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=[metadata] * len(chunks)
            )
            
            logger.info(f"✓ Ingested {len(chunks)} chunks for {doc_id}")
            return {"status": "success", "doc_id": doc_id, "chunks": len(chunks), "metadata": metadata}
        except Exception as e:
            logger.error(f"Error saving chunks: {e}")
            return {"status": "error", "error": str(e), "doc_id": doc_id}
