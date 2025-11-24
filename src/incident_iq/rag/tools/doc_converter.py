import json
import logging
from pathlib import Path
from typing import Dict, Any
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

logger = logging.getLogger(__name__)

class DocConverter:
    def __init__(self):
        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend),
            InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
        }
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF, InputFormat.DOCX, InputFormat.PPTX, InputFormat.HTML, InputFormat.IMAGE, InputFormat.XLSX],
            format_options=format_options
        )
        logger.info("DocConverter initialized")

    def convert(self, file_path: str) -> Dict[str, Any]:
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            markdown = doc.export_to_markdown()
            stats = self._extract_stats(doc)
            return {"status": "success", "markdown": markdown, "stats": stats, "filename": Path(file_path).name}
        except Exception as e:
            logger.error(f"Error converting {file_path}: {e}")
            return {"status": "error", "error": str(e), "filename": Path(file_path).name}

    def _extract_stats(self, doc) -> Dict[str, int]:
        stats = {"pages": len(doc.pages), "tables": 0, "images": 0, "blocks": 0}
        for page in doc.pages:
            stats["blocks"] += len(page.blocks)
            for block in page.blocks:
                if hasattr(block, 'kind'):
                    block_kind = str(block.kind).lower()
                    if 'table' in block_kind:
                        stats["tables"] += 1
                    elif 'image' in block_kind or 'picture' in block_kind:
                        stats["images"] += 1
        return stats
