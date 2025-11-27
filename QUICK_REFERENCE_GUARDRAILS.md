# Quick Reference: Guardrails & Document Ingestion

## 🚀 Five Minute Start

### Install Optional Dependencies
```bash
pip install pdfplumber PyPDF2 python-docx guardrails-ai
```

### Basic Usage
```python
from src.incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# 1. Ingest documents from folder (auto doc_id)
result = agent.invoke("ingest_from_path", 
    path="./docs",
    recursive=True
)
print(f"✓ Ingested {result['documents_ingested']} documents")

# 2. Ask question with Guardrails validation
response = agent.ask_question(
    question="What are critical issues?",
    response_mode="concise"  # Uses hallucination + security validation
)
print(f"✓ Answer: {response['answer']}")
print(f"✓ Guardrails: {response['guardrails_applied']}")
```

## 📋 Operations Reference

### invoke("ingest_from_path", **kwargs)
Discover and ingest documents from file path.

**Parameters:**
- `path` (str): Directory or file path to scan
- `doc_id_prefix` (str, default="doc"): Prefix for auto-generated doc_ids
- `file_type` (str, default="auto"): "pdf", "text", "word", or "auto"
- `recursive` (bool, default=True): Scan subdirectories

**Returns:**
```python
{
    "success": bool,
    "documents_discovered": int,
    "documents_ingested": int,
    "documents_failed": int,
    "errors": [list of errors],
    "ingestion_details": {...}
}
```

**Examples:**
```python
# Ingest all PDFs
agent.invoke("ingest_from_path", path="./docs", file_type="pdf")

# Ingest all text files
agent.invoke("ingest_from_path", path="./knowledge_base", file_type="text")

# Ingest everything (auto-detect)
agent.invoke("ingest_from_path", path="./data")
```

### ask_question(question, response_mode="concise", **kwargs)
Query with response mode specific validation.

**Response Modes:**

1. **"concise"** (default) - User-friendly
   - Validation: hallucination_check + security_incident_policy
   - Output: { success, question, answer, session_id, guardrails_applied, errors }
   - Debug: Minimal
   ```python
   response = agent.ask_question(
       question="What happened?",
       response_mode="concise"
   )
   # Returns: {"answer": "...", "guardrails_applied": true}
   ```

2. **"internal"** - System integration
   - Validation: hallucination_check only
   - Output: { success, answer, quality_score, sources_count, source_docs, metadata, ... }
   - Debug: Moderate
   ```python
   response = agent.ask_question(
       question="What happened?",
       response_mode="internal"
   )
   # Returns: {"answer": "...", "quality_score": 0.85, "sources_count": 3}
   ```

3. **"verbose"** - Engineer/Debug
   - Validation: None (raw data)
   - Output: All metadata, traceability, RL info
   - Debug: Full
   ```python
   response = agent.ask_question(
       question="What happened?",
       response_mode="verbose"
   )
   # Returns: {all fields, traceability, rl_recommendation, ...}
   ```

## 🔧 Configuration (data_sources.json)

### Enable/Disable Document Types
```json
{
  "data_sources": {
    "pdf": {"enabled": true, "chunk_size": 1000},
    "text": {"enabled": true, "chunk_size": 512},
    "word": {"enabled": true, "chunk_size": 800}
  }
}
```

### Set Default Search Paths
```json
{
  "document_paths": {
    "enabled": true,
    "default_directories": ["./docs", "./knowledge_base"],
    "recursive": true,
    "follow_symlinks": false
  }
}
```

### Configure Guardrails
```json
{
  "guardrails": {
    "response_mode_policies": {
      "concise": {
        "validators": ["hallucination_check", "security_incident_policy"]
      },
      "internal": {
        "validators": ["hallucination_check"]
      },
      "verbose": {
        "validators": []
      }
    }
  }
}
```

## 🛠️ Advanced Examples

### Example 1: Batch Ingest Multiple Formats
```python
# Ingest PDFs
result1 = agent.invoke("ingest_from_path", 
    path="./pdf_docs", file_type="pdf"
)

# Ingest Text files
result2 = agent.invoke("ingest_from_path", 
    path="./text_docs", file_type="text"
)

# Ingest Word documents
result3 = agent.invoke("ingest_from_path", 
    path="./word_docs", file_type="word"
)

total = result1['documents_ingested'] + \
        result2['documents_ingested'] + \
        result3['documents_ingested']
print(f"Total ingested: {total}")
```

### Example 2: Quality-Aware Query
```python
# Get quality metrics
verbose_response = agent.ask_question(
    question="How to fix X?",
    response_mode="verbose"
)

quality = verbose_response['retrieval_quality']
sources = verbose_response['sources_count']

if quality < 0.6:
    print("⚠️ Low confidence answer, consider adding more docs")
elif sources < 3:
    print("⚠️ Limited sources, may need more context")
else:
    print("✓ High confidence answer based on multiple sources")
```

### Example 3: Error Handling
```python
result = agent.invoke("ingest_from_path", path="./docs")

if result['documents_failed'] > 0:
    print(f"⚠️ {result['documents_failed']} documents failed:")
    for error in result['errors']:
        print(f"  - {error['doc_id']}: {error['error']}")

if not result['success']:
    print(f"❌ Ingestion failed: {result.get('error')}")
```

### Example 4: Response Validation Check
```python
response = agent.ask_question(
    question="What is the incident?",
    response_mode="concise"
)

if response['guardrails_applied']:
    print("✓ Answer has passed security validation")
else:
    print("⚠️ Guardrails were not applied (disabled or errors)")
```

## 📊 Expected Output Examples

### Successful Ingestion
```
[📋 RETRIEVE CONTEXT NODE - VERBOSE MODE]
  Question: What are the critical incidents?
  Retrieving top-k=5 relevant documents...
  ✓ Retrieved 5 documents (quality score: 1.00)

[📊 RERANK CONTEXT NODE - VERBOSE MODE]
  Reranking 5 documents for relevance...
  ✓ Reranked to 5 documents (sorted by relevance)
    [1] Score: 0.95 | Doc: incident_001
    [2] Score: 0.87 | Doc: incident_002
    [3] Score: 0.82 | Doc: incident_003

[📋 ANSWER GENERATION NODE - VERBOSE MODE]
  Question: What are the critical incidents?...
  Response Mode: verbose
  ✓ Answer Generated (45 words)

[📊 LOGGING QUERY TO DATABASE]
  Reranked Sources: 5
  Database Path: ./db/incident.db
  Target Doc ID: incident_001
  ✓ Query Logged: ID=12345
  Database Total QUERY Events: 127
```

### Concise Mode (Clean Output)
```python
response = agent.ask_question("What happened?", response_mode="concise")
print(response['answer'])
# Output: "Three critical incidents were detected..."
```

## ❌ Troubleshooting

### Missing Optional Dependencies
```
[WARNING] Failed to initialize Guardrails: No module named 'guardrails'
```
**Fix:** `pip install guardrails-ai`

### PDF Extraction Fails
```
[ERROR] PDF extraction failed: module not found
```
**Fix:** `pip install pdfplumber PyPDF2`

### Document Not Found
```
{
  "success": false,
  "documents_discovered": 0,
  "error": "No documents found at path"
}
```
**Fix:** Check path, ensure recursive=true, verify file types are enabled

### Guardrails Validation Error
```
[⚠] Guardrails validation warning: validation failed
```
**Fix:** This is normal, answer is returned anyway. Check response_mode and available validators.

## 📚 Document Type Support

| Format | Extension | Tool | Extraction | Status |
|--------|-----------|------|-----------|--------|
| PDF | .pdf | pdfplumber/PyPDF2 | Text + Tables | ✅ |
| Text | .txt | Built-in | Full text | ✅ |
| Markdown | .md, .markdown | Built-in | Full text | ✅ |
| Word | .docx | python-docx | Text + Tables | ✅ |
| Word | .doc | python-docx | Text + Tables | ✅ |

## 🎯 Best Practices

1. **Use Concise Mode for Users** - Simplest output with validation
2. **Use Internal Mode for APIs** - Structured data without overhead
3. **Use Verbose Mode for Debugging** - Full traceability and metrics
4. **Pre-ingest documents** - Better performance than on-demand
5. **Use file_type="auto"** - Let system detect format
6. **Check quality_score** - Lower scores mean fewer sources
7. **Monitor guardrails_applied** - Ensure validation is active

## 🔐 Security Notes

- Concise mode has full security validation (hallucination + policy checks)
- Internal mode checks for hallucinations only
- Verbose mode has no validation (debug data)
- All responses are logged to database with session IDs
- No passwords or secrets in extracted text
