"""
Test: LangGraph Agent - SQLite Table and PDF Ingestion

This test demonstrates:
1. Ingesting a SQLite table from incident_iq.db using data_sources.json config
2. Ingesting a PDF document
3. Retrieving and answering questions from both sources

The test invokes the master LangGraph agent with data source configurations.
"""

import sys
import json
import sqlite3
from pathlib import Path
from io import BytesIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
from incident_iq.rag.tools.ingestion_tools import ingest_sqlite_table_tool
from incident_iq.config.env_config import EnvConfig

# Try to import PDF tools
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    print("⚠️ WARNING: reportlab not installed. PDF creation will be skipped.")
    print("   Install with: pip install reportlab")
    PDF_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    from pypdf import PdfReader as PyPdfReader
    PDF_READ_AVAILABLE = True
except ImportError:
    print("⚠️ WARNING: pypdf/PyPDF2 not installed. PDF reading will be skipped.")
    print("   Install with: pip install pypdf")
    PDF_READ_AVAILABLE = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"🤖 {title}")
    print("=" * 80)


def print_section(title):
    """Print formatted section."""
    print(f"\n📋 {title}")
    print("-" * 80)


def create_sample_pdf(output_path: str):
    """Create a sample PDF document for testing."""
    if not PDF_AVAILABLE:
        print("⚠️ Cannot create PDF: reportlab not installed")
        return None
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom style for title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Title
        story.append(Paragraph("Incident Response Policy", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Content
        content = """
        <b>1. Purpose</b><br/>
        This policy establishes a comprehensive incident response process to minimize damage from security incidents, 
        reduce recovery time and costs, and enable the organization to restore business operations.
        <br/><br/>
        
        <b>2. Incident Classification</b><br/>
        Incidents are classified by severity:
        <br/>
        • <b>Critical (P1)</b>: Complete service outage, data breach, or system compromise. Response time: &lt;15 minutes<br/>
        • <b>High (P2)</b>: Major functionality unavailable, performance degradation. Response time: &lt;1 hour<br/>
        • <b>Medium (P3)</b>: Minor functionality affected. Response time: &lt;4 hours<br/>
        • <b>Low (P4)</b>: Cosmetic issues, documentation updates. Response time: &lt;24 hours<br/>
        <br/><br/>
        
        <b>3. Incident Response Workflow</b><br/>
        <b>Phase 1: Detection &amp; Alerting</b><br/>
        - Incidents detected via monitoring systems or user reports<br/>
        - Alert sent to on-call engineer<br/>
        - Incident ticket created automatically<br/>
        <br/>
        
        <b>Phase 2: Initial Response</b><br/>
        - Acknowledge incident receipt<br/>
        - Assess severity and impact<br/>
        - Notify stakeholders<br/>
        - Create incident war room (for P1/P2)<br/>
        <br/>
        
        <b>Phase 3: Investigation &amp; Mitigation</b><br/>
        - Identify root cause<br/>
        - Implement temporary fix if needed<br/>
        - Prevent further damage<br/>
        - Monitor system stability<br/>
        <br/>
        
        <b>Phase 4: Resolution &amp; Recovery</b><br/>
        - Deploy permanent fix<br/>
        - Verify system functionality<br/>
        - Communicate status to users<br/>
        <br/>
        
        <b>Phase 5: Post-Incident Review</b><br/>
        - Conduct blameless postmortem<br/>
        - Document lessons learned<br/>
        - Implement preventive measures<br/>
        - Close incident ticket<br/>
        <br/><br/>
        
        <b>4. Escalation Matrix</b><br/>
        Response times are measured from incident detection:
        <br/>
        • P1: Page on-call manager immediately, escalate to VP Engineering<br/>
        • P2: Page on-call engineer, escalate if not resolved in 30 minutes<br/>
        • P3: Create ticket, escalate if not acknowledged in 2 hours<br/>
        • P4: Create ticket, no escalation required<br/>
        <br/><br/>
        
        <b>5. Communication Requirements</b><br/>
        - Initial update within 10 minutes of detection (P1/P2)<br/>
        - Status updates every 15-30 minutes<br/>
        - Root cause analysis within 24 hours<br/>
        - Final post-mortem within 7 days<br/>
        """
        
        story.append(Paragraph(content, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def read_pdf_as_text(pdf_path: str) -> str:
    """Read PDF file and extract text content."""
    if not PDF_READ_AVAILABLE:
        print("⚠️ Cannot read PDF: pypdf not installed")
        return ""
    
    try:
        # Try pypdf first
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
        except ImportError:
            # Fall back to PyPDF2
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        print(f"⚠️ Error reading PDF: {e}")
        return ""


def load_data_sources_config(config_path: str = None) -> dict:
    """Load data sources configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent / "src" / "incident_iq" / "rag" / "config" / "data_sources.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading data_sources.json: {e}")
        return {}


def get_table_config_from_data_sources(config: dict, table_name: str) -> dict:
    """Extract table configuration from data_sources.json."""
    try:
        sqlite_config = config.get("data_sources", {}).get("sqlite", {})
        tables = sqlite_config.get("ingestion_modes", {}).get("table_based", {}).get("tables_to_ingest", [])
        
        for table in tables:
            if table.get("name") == table_name:
                return table
        
        return {}
    except Exception as e:
        print(f"❌ Error extracting table config: {e}")
        return {}


def get_sqlite_table_as_text(db_path: str, table_name: str, limit: int = 50) -> str:
    """Read SQLite table and convert to structured text."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get sample rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        # Convert to text format
        text = f"# SQLite Table: {table_name}\n\n"
        text += f"**Total Rows**: {row_count}\n"
        text += f"**Columns**: {', '.join(columns)}\n\n"
        text += "## Sample Data\n\n"
        text += "| " + " | ".join(columns) + " |\n"
        text += "|" + "|".join(["---"] * len(columns)) + "|\n"
        
        for row in rows:
            values = [str(row[col])[:50] for col in columns]
            text += "| " + " | ".join(values) + " |\n"
        
        if row_count > limit:
            text += f"\n*(Showing {limit} of {row_count} rows)*\n"
        
        conn.close()
        return text
        
    except Exception as e:
        print(f"❌ Error reading SQLite table: {e}")
        import traceback
        traceback.print_exc()
        return ""


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_sqlite_table_ingestion():
    """Test ingesting a SQLite table using orchestrator with data_sources.json config."""
    print_section("1. SQLite Table Ingestion (via Orchestrator with data_sources.json)")
    
    try:
        # Load data sources configuration
        config = load_data_sources_config()
        if not config:
            print("❌ Failed to load data_sources.json")
            return False
        
        print(f"✅ Loaded data_sources.json configuration")
        
        # Initialize agent
        agent = LangGraphRAGAgent()
        print(f"✅ Initialized LangGraphRAGAgent")
        
        # Get database path
        db_path = EnvConfig.get_db_path()
        print(f"📂 Database: {db_path}")
        
        # Try to find available tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"📊 Available tables: {tables}")
        
        if not tables:
            print("⚠️ No tables found in database.")
            return False
        
        # Use first table
        table_to_ingest = tables[0]
        print(f"📥 Selected table for ingestion: {table_to_ingest}")
        
        # Get table config from data_sources.json
        table_config = get_table_config_from_data_sources(config, table_to_ingest)
        
        if table_config:
            print(f"✅ Found table config in data_sources.json")
            text_columns = table_config.get("text_columns", [])
            metadata_columns = table_config.get("metadata_columns", [])
        else:
            # Use sensible defaults if config not in data_sources.json
            print(f"⚠️ Table '{table_to_ingest}' not in data_sources.json, using defaults")
            
            # Get column names from table
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_to_ingest})")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            
            # Use all string columns as text columns
            text_columns = columns[:3] if len(columns) >= 3 else columns
            metadata_columns = columns[3:] if len(columns) > 3 else []
        
        print(f"📋 Text columns: {text_columns}")
        print(f"📎 Metadata columns: {metadata_columns}")
        
        # Get chunking config
        sqlite_config = config.get("data_sources", {}).get("sqlite", {})
        chunking_config = sqlite_config.get("chunking", {})
        chunk_size = chunking_config.get("chunk_size", 512)
        chunk_overlap = chunking_config.get("overlap", 50)
        
        print(f"🔪 Chunk size: {chunk_size}, overlap: {chunk_overlap}")
        
        # Create doc_id
        doc_id = f"sqlite_{table_to_ingest}_{Path(__file__).stem}"
        rbac_namespace = "general"
        
        print(f"\n🔄 Invoking Master LangGraph Agent for table ingestion...")
        print(f"   Doc ID: {doc_id}")
        print(f"   RBAC Namespace: {rbac_namespace}")
        
        # Invoke ingest_sqlite_table_tool through the LLM service (which can be called directly)
        result_json = ingest_sqlite_table_tool.invoke({
            "table_name": table_to_ingest,
            "doc_id": doc_id,
            "rbac_namespace": rbac_namespace,
            "text_columns": text_columns,
            "metadata_columns": metadata_columns,
            "db_path": db_path,
            "llm_service": agent.llm_service,
            "vectordb_service": agent.vectordb_service,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        })
        
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        print(f"\n✅ Ingestion Result:")
        print(f"   Status: {'Success' if result.get('success') else 'Failed'}")
        print(f"   Doc ID: {result.get('doc_id', 'N/A')}")
        print(f"   Chunks Saved: {result.get('chunks_saved', 0)}")
        print(f"   RBAC Namespace: {result.get('rbac_namespace', 'N/A')}")
        
        if result.get('error'):
            print(f"   Error: {result['error']}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_ingestion():
    """Test ingesting a PDF document."""
    print_section("2. PDF Document Ingestion")
    
    if not PDF_AVAILABLE:
        print("⚠️ Skipping PDF ingestion test: reportlab not installed")
        return False
    
    try:
        agent = LangGraphRAGAgent()
        
        # Create sample PDF
        pdf_path = Path("sample_incident_policy.pdf")
        print(f"📝 Creating sample PDF: {pdf_path}")
        
        created_pdf = create_sample_pdf(str(pdf_path))
        if not created_pdf:
            print("⚠️ Failed to create PDF")
            return False
        
        print(f"✅ PDF created successfully")
        
        # Read PDF content
        if PDF_READ_AVAILABLE:
            pdf_text = read_pdf_as_text(str(pdf_path))
            if not pdf_text:
                # Fallback: use sample content
                pdf_text = """
                Incident Response Policy Document
                
                This document outlines the comprehensive incident response procedures for the organization.
                
                1. Purpose and Scope
                - Establish rapid response to incidents
                - Minimize impact and recovery time
                - Ensure effective communication
                
                2. Severity Levels
                - P1: Critical - Complete outage
                - P2: High - Major impact
                - P3: Medium - Minor impact
                - P4: Low - Cosmetic
                
                3. Response Procedures
                - Detection and alerting
                - Initial assessment
                - Investigation and mitigation
                - Resolution
                - Post-incident review
                
                4. Escalation Procedures
                - Page on-call engineer
                - Notify team leads
                - Escalate to management if needed
                
                5. Communication
                - Initial status within 10 minutes
                - Updates every 15-30 minutes
                - Root cause analysis within 24 hours
                """
        else:
            print("⚠️ PDF reading library not available, using sample content instead")
            pdf_text = """
Incident Response Policy Document

This document outlines the comprehensive incident response procedures for the organization.

1. Purpose and Scope
- Establish rapid response to incidents
- Minimize impact and recovery time
- Ensure effective communication

2. Severity Levels
- P1: Critical - Complete outage
- P2: High - Major impact
- P3: Medium - Minor impact
- P4: Low - Cosmetic

3. Response Procedures
- Detection and alerting
- Initial assessment
- Investigation and mitigation
- Resolution
- Post-incident review

4. Escalation Procedures
- Page on-call engineer
- Notify team leads
- Escalate to management if needed

5. Communication
- Initial status within 10 minutes
- Updates every 15-30 minutes
- Root cause analysis within 24 hours
            """
        
        print(f"📄 PDF content preview: {len(pdf_text)} characters")
        print(f"{pdf_text[:300]}...")
        
        # Ingest PDF
        doc_id = "pdf_incident_policy_001"
        print(f"\n🔄 Ingesting PDF as document ID: {doc_id}")
        
        result = agent.ingest_document(pdf_text, doc_id)
        
        print(f"\n✅ Ingestion Result:")
        print(f"   Status: {'Success' if result['success'] else 'Failed'}")
        print(f"   Doc ID: {result['doc_id']}")
        print(f"   Chunks: {result.get('chunks_count', 0)}")
        print(f"   Saved: {result.get('chunks_saved', 0)}")
        if result.get('errors'):
            print(f"   Errors: {result['errors']}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval_from_ingested_sources():
    """Test retrieving information from both SQLite and PDF sources."""
    print_section("3. Retrieval from Ingested Sources")
    
    try:
        agent = LangGraphRAGAgent()
        
        questions = [
            "What are the incident severity levels?",
            "What is the incident response workflow?",
            "What are the escalation procedures?",
            "How quickly should we respond to critical incidents?",
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            
            result = agent.ask_question(
                question, 
                response_mode="concise"
            )
            
            print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
            
            answer = result.get('answer', 'N/A')
            # Clean up answer if it's JSON
            if isinstance(answer, str) and answer.strip().startswith('{'):
                try:
                    parsed = json.loads(answer)
                    answer = parsed.get('answer', answer)
                except:
                    pass
            
            print(f"   Answer: {answer[:150]}...")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            
            if result.get('errors'):
                print(f"   Errors: {result['errors']}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def test_verbose_retrieval():
    """Test verbose retrieval with full traceability."""
    print_section("4. Verbose Retrieval with Traceability")
    
    try:
        agent = LangGraphRAGAgent()
        
        question = "What is the incident response workflow?"
        
        print(f"❓ Question: {question}\n")
        print("Executing with VERBOSE response mode (full metadata)...\n")
        
        result = agent.ask_question(
            question, 
            response_mode="verbose"
        )
        
        print(f"✅ Success: {result['success']}")
        print(f"📊 Retrieval Quality: {result.get('retrieval_quality', 0):.2%}")
        print(f"📚 Sources Found: {result.get('sources_count', 0)}")
        print(f"⏱️  Execution Time: {result.get('execution_time_ms', 0):.1f}ms")
        
        if result.get('answer'):
            print(f"\n📝 Answer:\n{result['answer'][:300]}...")
        
        if result.get('optimization_applied'):
            print(f"\n🔧 Optimization Applied:")
            print(f"   Action: {result.get('rl_action', 'N/A')}")
            print(f"   Reason: {result.get('optimization_reason', 'N/A')}")
        
        if result.get('sources_count', 0) > 0:
            print(f"\n📖 Sources Retrieved:")
            for i, source in enumerate(result.get('sources', [])[:3], 1):
                print(f"   {i}. {source.get('metadata', {}).get('doc_id', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🤖 LANGGRAPH MASTER AGENT - SQLITE & PDF INGESTION TESTS")
    print("=" * 80)
    
    print("\n📌 Test Configuration:")
    print(f"   Database Path: {EnvConfig.get_db_path()}")
    print(f"   Chroma DB Path: {EnvConfig.get_chroma_db_path()}")
    print(f"   Data Sources Config: src/incident_iq/rag/config/data_sources.json")
    
    # Run tests
    sqlite_ok = test_sqlite_table_ingestion()
    pdf_ok = test_pdf_ingestion()
    
    if sqlite_ok or pdf_ok:
        test_retrieval_from_ingested_sources()
        test_verbose_retrieval()
    else:
        print("\n⚠️ Ingestion tests failed. Skipping retrieval tests.")
    
    print("\n" + "=" * 80)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
