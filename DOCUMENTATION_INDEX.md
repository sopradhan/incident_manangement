# LangGraph RAG Agent Documentation Index

## 📚 Complete Documentation Set

### 1. **AGENT_TOOL_REFERENCE.md** 
**For:** Understanding what each tool does
- Detailed breakdown of all 16+ tools
- When each tool gets invoked
- Input/output specifications
- Tool dependency matrix
- Error handling strategy
- **Read this if:** You want to know how the system works

### 2. **TOOL_DECISION_TREE.md**
**For:** Making decisions about which tool/operation to use
- Visual decision trees for all operations
- Complete workflow sequences with ASCII diagrams
- Tool compatibility matrix
- Performance optimization triggers
- API usage examples
- **Read this if:** You're building on top of the agent

### 3. **AGENT_SYSTEM_PROMPTS.md**
**For:** Understanding when tools are invoked and how response modes work
- Quick reference table of tool invocation sequences
- Tool decision matrices
- System prompts by response mode (concise/internal/verbose)
- Debug output triggers
- Usage patterns and performance considerations
- **Read this if:** You're debugging behavior or tuning performance

### 4. **REFACTORING_SUMMARY.md**
**For:** Understanding what was fixed and improved
- Issues fixed during refactoring
- Tool utilization review
- Code documentation added
- Architecture improvements
- Testing recommendations
- **Read this if:** You're reviewing the changes or upgrading

---

## 🎯 Quick Start By Use Case

### "I want to ingest documents"
1. Read: **TOOL_DECISION_TREE.md** → "Which Tool to Use When" section
2. Use: `agent.invoke("ingest_document", text="...", doc_id="...")`
3. Or: `agent.invoke("ingest_from_path", path="./docs", recursive=True)`
4. Tools Used: extract_metadata_tool → chunk_document_tool → save_to_vectordb_tool → update_metadata_tracking_tool

### "I want to ask questions"
1. Read: **AGENT_SYSTEM_PROMPTS.md** → "Usage Patterns" section
2. Choose response mode: "concise" (users) | "internal" (systems) | "verbose" (engineers)
3. Use: `agent.invoke("ask_question", question="...", response_mode="concise")`
4. Tools Used: retrieve_context_tool → rerank_context_tool → answer_question_tool → guardrails

### "I want to understand the architecture"
1. Read: **AGENT_TOOL_REFERENCE.md** → "Overview" section
2. Study: **TOOL_DECISION_TREE.md** → "Workflow Sequences" section
3. Reference: **AGENT_SYSTEM_PROMPTS.md** → "Tool Invocation Sequence Diagrams"

### "I want to debug behavior"
1. Read: **AGENT_SYSTEM_PROMPTS.md** → "Debug Output Triggers" section
2. Use: `agent.invoke(..., response_mode="verbose")` for detailed logs
3. Check: **TOOL_DECISION_TREE.md** → "Tool Dependency Matrix" for what might fail

### "I want to see code examples"
1. Read: **TOOL_DECISION_TREE.md** → "API Usage Examples" section
2. Reference: **AGENT_SYSTEM_PROMPTS.md** → "Usage Patterns" section

### "I want to understand what changed"
1. Read: **REFACTORING_SUMMARY.md** → "Issues Fixed" section
2. Check: **REFACTORING_SUMMARY.md** → "Tool Utilization Review" section

---

## 📊 Document Relationship Map

```
REFACTORING_SUMMARY.md (What was done)
    ├─→ List of fixed issues
    ├─→ Import errors resolved
    └─→ No breaking changes

AGENT_TOOL_REFERENCE.md (Complete Reference)
    ├─→ Detailed tool documentation
    ├─→ Workflow stages explained
    ├─→ Response modes documented
    └─→ Error handling strategy

TOOL_DECISION_TREE.md (Practical Workflows)
    ├─→ Visual decision trees
    ├─→ Workflow sequences
    ├─→ Compatibility matrix
    └─→ API examples

AGENT_SYSTEM_PROMPTS.md (Quick Reference)
    ├─→ Tool invocation tables
    ├─→ System prompts by mode
    ├─→ Debug triggers
    └─→ Performance tips
```

---

## 🔧 Key Concepts

### Response Modes
- **Concise**: User-friendly, validated (hallucination + security)
- **Internal**: System integration, structured, validated (hallucination only)
- **Verbose**: Engineering debug, unfiltered, no guardrails

### Tool Categories
1. **Ingestion Tools** (4): Extract metadata, chunk, embed, track
2. **Retrieval Tools** (4): Retrieve, rerank, answer, trace
3. **Optimization Tools** (4): Cost analysis, optimization, config

### Workflows
1. **Ingestion**: Single document, table, or batch folder
2. **Retrieval**: Question answering with 3 response modes
3. **Optimization**: Performance tuning and configuration

---

## 📋 All Tools Reference

### Ingestion Tools
- ✅ `extract_metadata_tool` - LLM-powered metadata extraction
- ✅ `chunk_document_tool` - Semantic text splitting
- ✅ `save_to_vectordb_tool` - Embedding generation and VectorDB storage
- ✅ `update_metadata_tracking_tool` - Audit trail and tracking
- ✅ `ingest_sqlite_table_tool` - Database table ingestion
- ✅ `ingest_documents_from_path_tool` - Batch document discovery
- ⏸ `extract_document_text_tool` - Multi-format extraction (optional)
- ⏸ `record_agent_memory_tool` - Agent self-reflection (optional)

### Retrieval Tools
- ✅ `retrieve_context_tool` - Semantic search and retrieval
- ✅ `rerank_context_tool` - LLM-based relevance re-ranking
- ✅ `answer_question_tool` - Answer synthesis from context
- ✅ `traceability_tool` - Source attribution and audit trail

### Optimization Tools
- ✅ `check_embedding_health_tool` - Vector DB health check
- ✅ `get_context_cost_tool` - Token estimation and cost analysis
- ✅ `optimize_chunk_size_tool` - Parameter optimization recommendations
- ✅ `adjust_config_tool` - Configuration management and updates

### Validation Tools
- ✅ `Guard` (from Guardrails) - Response validation
- ✅ `hallucination_check()` - Fact verification
- ✅ `security_incident_policy()` - Policy compliance check

---

## 🚀 Getting Started

### Step 1: Read the Overview
Start with **AGENT_TOOL_REFERENCE.md** section 1 for the big picture.

### Step 2: Understand Your Use Case
Find your use case in **TOOL_DECISION_TREE.md** and follow the flowchart.

### Step 3: Look Up Details
Use **AGENT_SYSTEM_PROMPTS.md** for quick reference on tool invocation.

### Step 4: Debug if Needed
Use **AGENT_SYSTEM_PROMPTS.md** debug section with `response_mode="verbose"`.

### Step 5: Check the Code
Inline comments in `langgraph_rag_agent.py` explain each tool invocation.

---

## 📖 Documentation Standards

Each document follows a consistent structure:

1. **Title & Purpose** - What is this document for?
2. **Overview/Quick Reference** - High-level summary
3. **Detailed Sections** - Comprehensive information
4. **Examples** - Practical usage examples
5. **Reference Tables** - Quick lookup information
6. **Troubleshooting** - Common issues and solutions

---

## ✅ Verification Checklist

- ✅ All 16+ tools documented
- ✅ All workflows explained
- ✅ All response modes covered
- ✅ Error handling documented
- ✅ API examples provided
- ✅ Decision trees created
- ✅ System prompts explained
- ✅ Code inline comments added
- ✅ No breaking changes
- ✅ Backward compatible

---

## 🎓 Learning Path

### Beginner (Just want to use it)
1. **AGENT_SYSTEM_PROMPTS.md** → "Usage Patterns" section
2. Copy and run the examples

### Intermediate (Need to understand it)
1. **AGENT_TOOL_REFERENCE.md** → "Overview" section
2. **TOOL_DECISION_TREE.md** → "Which Tool to Use When"
3. Study the workflow sequences

### Advanced (Building extensions)
1. **AGENT_TOOL_REFERENCE.md** → Complete reference
2. **TOOL_DECISION_TREE.md** → "Workflow Sequences" 
3. **REFACTORING_SUMMARY.md** → "No Breaking Changes" section
4. Study the code comments in `langgraph_rag_agent.py`

---

## 🔗 Quick Links

### By Component
- **Ingestion**: See TOOL_DECISION_TREE.md "Ingestion Workflow"
- **Retrieval**: See TOOL_DECISION_TREE.md "Retrieval Workflow"
- **Optimization**: See AGENT_TOOL_REFERENCE.md "Optimization Workflow"

### By Operation
- **Single Document**: TOOL_DECISION_TREE.md "Sequence 1"
- **Answer Question**: TOOL_DECISION_TREE.md "Sequence 2"
- **Batch Folder**: TOOL_DECISION_TREE.md "Sequence 3"

### By Response Mode
- **Concise**: AGENT_SYSTEM_PROMPTS.md "Concise Mode"
- **Internal**: AGENT_SYSTEM_PROMPTS.md "Internal Mode"
- **Verbose**: AGENT_SYSTEM_PROMPTS.md "Verbose Mode"

---

## 📞 Support

### Common Questions

**Q: Which response mode should I use?**
- A: See AGENT_SYSTEM_PROMPTS.md "System Prompts by Response Mode"

**Q: How do I ingest a PDF folder?**
- A: See TOOL_DECISION_TREE.md "Sequence 3: Ingest Folder of Documents"

**Q: Why isn't my question getting answered?**
- A: See AGENT_SYSTEM_PROMPTS.md "Debug Output Triggers" and use verbose mode

**Q: What tools are required?**
- A: See AGENT_TOOL_REFERENCE.md "Tool Dependency Matrix"

**Q: Can I use this with guardrails?**
- A: See AGENT_SYSTEM_PROMPTS.md "Guardrails Validation Pipeline"

---

## 📝 Documentation Maintenance

- Last Updated: November 27, 2025
- Agent Version: LangGraph-based RAG (3 workflows, 16+ tools)
- Status: Production Ready ✅
- Breaking Changes: None
- Backward Compatible: Yes ✅

---

**For detailed information, consult the specific documentation file that matches your need.**
