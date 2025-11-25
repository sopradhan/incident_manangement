import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Union, List
from langchain_core.tools import tool

@tool
def convert_to_markdown(data: Union[str, Dict, List], source_type: str = "auto") -> str:
    """Convert dict/list/string data to markdown format"""
    try:
        if isinstance(data, dict):
            md = _dict_to_markdown(data)
        elif isinstance(data, list):
            md = _list_to_markdown(data)
        else:
            md = str(data)
        
        return json.dumps({"success": True, "markdown": md, "source_type": source_type})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def _dict_to_markdown(data: Dict) -> str:
    md = []
    for key, value in data.items():
        md.append(f"## {key}")
        if isinstance(value, dict):
            for k, v in value.items():
                md.append(f"**{k}:** {v}")
        elif isinstance(value, list):
            for item in value:
                md.append(f"- {item}")
        else:
            md.append(str(value))
        md.append("")
    return "\n".join(md)

def _list_to_markdown(data: List) -> str:
    if not data:
        return ""
    if isinstance(data[0], dict):
        md = []
        headers = list(data[0].keys())
        md.append("| " + " | ".join(headers) + " |")
        md.append("|" + "|".join(["---"] * len(headers)) + "|")
        for row in data:
            md.append("| " + " | ".join([str(row.get(h, "")) for h in headers]) + " |")
        return "\n".join(md)
    else:
        return "\n".join([f"- {item}" for item in data])

@tool
def sqlite_table_to_markdown(db_path: str, table_name: str, text_columns: List[str]) -> str:
    """Convert SQLite table rows to markdown format"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        conn.close()
        
        data = [dict(row) for row in rows]
        return convert_to_markdown(data, f"sqlite_table:{table_name}")
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def file_to_markdown(file_path: str) -> str:
    """Convert file (JSON/TXT/CSV/PDF/DOCX) to markdown format"""
    try:
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        
        if ext == ".json":
            with open(file_path) as f:
                data = json.load(f)
            return convert_to_markdown(data, "json")
        elif ext == ".txt":
            with open(file_path) as f:
                text = f.read()
            return json.dumps({"success": True, "markdown": text, "source_type": "txt"})
        elif ext in [".csv"]:
            import csv
            rows = []
            with open(file_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return convert_to_markdown(rows, "csv")
        else:
            try:
                from docling.document_converter import DocumentConverter
                converter = DocumentConverter()
                result = converter.convert(file_path)
                markdown = result.document.export_to_markdown()
                return json.dumps({"success": True, "markdown": markdown, "source_type": f"docling:{ext}"})
            except:
                with open(file_path) as f:
                    text = f.read()
                return json.dumps({"success": True, "markdown": text, "source_type": ext})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
