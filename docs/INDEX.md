# LangGraph RAG Documentation Index

## 🎯 Quick Navigation

### For First-Time Users
Start here to understand the system:
1. **[README_HEALING_INTEGRATION.md](README_HEALING_INTEGRATION.md)** - Overview of what was implemented
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick guide with examples
3. **[LANGGRAPH_HEALING_WORKFLOW.md](LANGGRAPH_HEALING_WORKFLOW.md)** - Visual workflows and diagrams

### For Developers
Implementation and integration details:
1. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Complete technical summary
2. **[LANGGRAPH_HEALING_WORKFLOW.md](LANGGRAPH_HEALING_WORKFLOW.md)** - Architecture and decision logic
3. **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - SQLite schema and relationships

### For Data Analysts
Metadata inspection and reporting:
1. **[METADATA_TRACKING.md](METADATA_TRACKING.md)** - What data is collected and stored
2. **[SQL_METADATA_QUERIES.md](SQL_METADATA_QUERIES.md)** - 100+ SQL queries for analysis
3. **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Schema reference and indexes

### For Operations
Monitoring and optimization:
1. **[SQL_METADATA_QUERIES.md](SQL_METADATA_QUERIES.md)** - Dashboard and monitoring queries
2. **[METADATA_TRACKING.md](METADATA_TRACKING.md)** - Performance metrics tracked
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common troubleshooting

---

## 📄 Document Descriptions

### README_HEALING_INTEGRATION.md
**Purpose:** Executive summary of the intelligent healing integration
**Contents:**
- What's been delivered
- SQLite tables and what they store
- Intelligent decision logic
- Complete data flow examples
- File locations and modifications
- Usage examples
- Next steps

**Best for:** Getting oriented, understanding scope, high-level overview

---

### QUICK_REFERENCE.md
**Purpose:** Cheat sheet and quick lookup
**Contents:**
- 30-second system overview
- SQLite tables quick reference
- Decision tree diagram
- API quick start
- Key metrics tracked
- Common SQL queries (copy-paste)
- File locations
- Troubleshooting guide
- Learning path

**Best for:** Quick lookups, refreshing memory, finding specific info fast

---

### LANGGRAPH_HEALING_WORKFLOW.md
**Purpose:** Visual architecture and workflow diagrams
**Contents:**
- Complete workflow architecture (ASCII diagrams)
- Retrieval phase with intelligent healing
- SQLite table update flow
- Decision logic and conditional routing
- Data state through pipeline
- Performance metrics captured
- Decision logic examples with scenarios

**Best for:** Understanding the flow, visualizing the system, presentations

---

### METADATA_TRACKING.md
**Purpose:** Comprehensive guide to metadata collection and storage
**Contents:**
- SQLite tables updated (detailed descriptions)
- Data flow: Ingestion to Optimization
- Example: Complete query lifecycle
- Metadata fields tracked (by table)
- Accessing metadata programmatically
- Intelligent healing integration in LangGraph
- Performance metrics tracked

**Best for:** Understanding what data is collected, querying metadata, integration

---

### DATABASE_SCHEMA.md
**Purpose:** Complete database schema reference
**Contents:**
- Entity relationship diagram (ERD)
- Data flow through tables
- Table relationships summary
- Critical joins for analysis
- Schema creation SQL (copy-paste)
- Data volume examples
- Backup & maintenance procedures
- Access patterns and indexes

**Best for:** Database administrators, schema understanding, optimization

---

### SQL_METADATA_QUERIES.md
**Purpose:** Ready-to-use SQL queries for analysis
**Contents:**
- 7 sections of SQL queries (100+ total)
- 1. Document metadata queries
- 2. Embedding metadata queries
- 3. Query heatmap analysis
- 4. Healing operations analysis
- 5. Synthetic queries
- 6. Cross-table analysis
- 7. Dashboard-ready summaries
- Python helper functions
- Index definitions

**Best for:** Running analysis, creating dashboards, reporting

---

### IMPLEMENTATION_SUMMARY.md
**Purpose:** Complete technical documentation
**Contents:**
- Overview and key features
- Architecture diagram
- Data flow (Phase 1, 2, 3)
- SQLite tables (with examples)
- Response format
- File locations
- Usage examples
- Healing decision examples
- Performance metrics
- Next steps (future enhancements)
- Quick start commands

**Best for:** Understanding full implementation, reference documentation

---

## 🔄 Reading Paths

### Path 1: Quick Start (5 minutes)
1. README_HEALING_INTEGRATION.md (skim)
2. QUICK_REFERENCE.md (read "What You Need to Know")
3. Start coding!

### Path 2: Understanding the System (20 minutes)
1. README_HEALING_INTEGRATION.md (full read)
2. LANGGRAPH_HEALING_WORKFLOW.md (read flowcharts)
3. QUICK_REFERENCE.md (read all)

### Path 3: Integration & Customization (1 hour)
1. IMPLEMENTATION_SUMMARY.md (full read)
2. LANGGRAPH_HEALING_WORKFLOW.md (understand decision logic)
3. DATABASE_SCHEMA.md (understand schema)
4. Customize as needed

### Path 4: Analysis & Reporting (2 hours)
1. METADATA_TRACKING.md (understand what's tracked)
2. DATABASE_SCHEMA.md (understand relationships)
3. SQL_METADATA_QUERIES.md (run example queries)
4. Create your own dashboards/reports

### Path 5: Deep Dive (4+ hours)
Read everything in order:
1. README_HEALING_INTEGRATION.md
2. QUICK_REFERENCE.md
3. LANGGRAPH_HEALING_WORKFLOW.md
4. METADATA_TRACKING.md
5. IMPLEMENTATION_SUMMARY.md
6. DATABASE_SCHEMA.md
7. SQL_METADATA_QUERIES.md

---

## 📊 Document Cross-References

### Key Concepts Explained In
- **Intelligent Healing Decision**
  - LANGGRAPH_HEALING_WORKFLOW.md (Decision Logic section)
  - IMPLEMENTATION_SUMMARY.md (Healing Decision Examples)
  - QUICK_REFERENCE.md (Decision Tree)

- **SQLite Tables**
  - METADATA_TRACKING.md (detailed descriptions)
  - DATABASE_SCHEMA.md (ERD and schema creation)
  - SQL_METADATA_QUERIES.md (query examples)

- **Data Flow**
  - LANGGRAPH_HEALING_WORKFLOW.md (visual diagrams)
  - METADATA_TRACKING.md (text description)
  - IMPLEMENTATION_SUMMARY.md (phases breakdown)

- **Performance Metrics**
  - METADATA_TRACKING.md (what's tracked)
  - SQL_METADATA_QUERIES.md (how to query)
  - QUICK_REFERENCE.md (key metrics)

- **Usage Examples**
  - QUICK_REFERENCE.md (quick examples)
  - IMPLEMENTATION_SUMMARY.md (detailed examples)
  - SQL_METADATA_QUERIES.md (query examples)

---

## 🔍 Finding Answers

### "How does healing work?"
→ LANGGRAPH_HEALING_WORKFLOW.md → Decision Logic section

### "What data is being stored?"
→ METADATA_TRACKING.md → SQLite Tables section

### "Show me SQL queries"
→ SQL_METADATA_QUERIES.md → All sections

### "How do I use the API?"
→ QUICK_REFERENCE.md → Quick API Usage section
→ IMPLEMENTATION_SUMMARY.md → Usage Example section

### "What SQLite tables exist?"
→ DATABASE_SCHEMA.md → Schema Creation SQL section
→ METADATA_TRACKING.md → SQLite Tables section

### "How do I monitor performance?"
→ SQL_METADATA_QUERIES.md → Dashboard-Ready Queries section
→ QUICK_REFERENCE.md → Common Queries section

### "What are the response fields?"
→ IMPLEMENTATION_SUMMARY.md → Response Format section
→ QUICK_REFERENCE.md → Response Structure

### "How do I troubleshoot?"
→ QUICK_REFERENCE.md → Troubleshooting section

### "What files were modified?"
→ README_HEALING_INTEGRATION.md → Key Files Modified section
→ IMPLEMENTATION_SUMMARY.md → File Locations section

### "What metrics are tracked?"
→ METADATA_TRACKING.md → Metadata Fields Tracked section
→ QUICK_REFERENCE.md → Key Metrics Tracked section

---

## 📍 File Locations

### Documentation Files
All in: `docs/`
- README_HEALING_INTEGRATION.md
- QUICK_REFERENCE.md
- LANGGRAPH_HEALING_WORKFLOW.md
- METADATA_TRACKING.md
- IMPLEMENTATION_SUMMARY.md
- DATABASE_SCHEMA.md
- SQL_METADATA_QUERIES.md
- INDEX.md (this file)

### Implementation Files
- Agent: `src/incident_iq/rag/agents/langgraph_agent/langgraph_rag_agent.py`
- Tools: `src/incident_iq/rag/tools/`
- Services: `src/incident_iq/rag/tools/services/`
- Models: `src/incident_iq/database/models/`

### Test Files
- `scripts/test_langgraph_rag.py` (basic tests)
- `scripts/test_langgraph_with_healing.py` (comprehensive demo)

### Configuration
- `src/incident_iq/rag/config/llm_config.json` (LLM settings)

---

## 🎓 Topics by Complexity

### Beginner
- What is intelligent healing?
- How does the system work?
- How do I use it?
→ Read: QUICK_REFERENCE.md + README_HEALING_INTEGRATION.md

### Intermediate
- How does the decision logic work?
- What data is stored where?
- How do I query the metadata?
→ Read: LANGGRAPH_HEALING_WORKFLOW.md + METADATA_TRACKING.md + SQL_METADATA_QUERIES.md

### Advanced
- How is the system architected?
- What is the complete data flow?
- How do I extend/modify it?
→ Read: IMPLEMENTATION_SUMMARY.md + DATABASE_SCHEMA.md + (source code)

### Expert
- All of the above + source code deep dive
→ Read everything + examine: `langgraph_rag_agent.py` + `retrieval_tools.py`

---

## ✨ Key Statistics

### Documentation
- 7 comprehensive guides
- 100+ SQL queries
- 50+ ASCII diagrams and flowcharts
- 3000+ lines of documentation

### Code
- 1 main agent file (langgraph_rag_agent.py)
- 5 tool files (ingestion, retrieval, healing, config, adjust_config)
- 5 database model files (metadata, embedding, tracking, etc)
- 2 test scripts

### Database
- 5 SQLite tables
- 50+ fields total
- 7 indexes for performance
- Complete audit trail of all operations

---

## 🚀 Getting Started

1. **First time?** Read: QUICK_REFERENCE.md (5 min)
2. **Want details?** Read: LANGGRAPH_HEALING_WORKFLOW.md (15 min)
3. **Need to analyze?** Read: SQL_METADATA_QUERIES.md (30 min)
4. **Deep dive?** Read all guides in order (2-4 hours)

---

## 📝 Version Info

- **System**: LangGraph RAG Agent with Intelligent Healing
- **Date**: November 2025
- **Status**: Production Ready ✅
- **Components**: 
  - LangGraph workflow orchestration ✅
  - Intelligent healing decision logic ✅
  - 5 SQLite metadata tables ✅
  - Complete documentation ✅
  - Test suite ✅

---

This index provides a complete roadmap to all documentation. Use it to navigate, find answers, and understand the system at any level of detail.

**Happy exploring! 🎉**
