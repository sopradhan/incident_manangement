# LangGraph Agent - Interactive Chat CLI

## Direct Command-Line Invocation

Start interactive chat mode directly from command line with human feedback loop.

### Quick Start

```bash
# Default: concise mode (user-friendly)
python langgraph_chat_cli.py

# Verbose mode (full debug details for engineers)
python langgraph_chat_cli.py verbose

# Internal mode (system integration, structured data)
python langgraph_chat_cli.py internal

# Without conversation history display
python langgraph_chat_cli.py concise --no-history
```

### Response Modes

| Mode | Use Case | Guardrails | Output |
|------|----------|-----------|--------|
| **concise** | End users | Hallucination check + Security policy | User-friendly, concise answers |
| **internal** | System integration | Hallucination check only | Structured data, JSON-ready |
| **verbose** | Engineers | None (raw data) | Full debugging details, tool traces |

### Chat Workflow

1. **Initialize Agent** - Loads LangGraph agent and RAG models
2. **Get Question** - Prompts user: "Ask a question (or 'quit' to exit):"
3. **Process Query** - Searches knowledge base through RAG pipeline
4. **Display Answer** - Shows Q&A with clear formatting
5. **Collect Feedback** - Asks: "Satisfied? (yes/no/followup):"
   - **yes/y** - Mark as satisfied, ask next question
   - **no/n** - Retry with verbose mode for more details
   - **followup/f** - Accept current answer, ask follow-up question
6. **Continue or Quit** - Repeat until user types 'quit' or 'exit'
7. **Save Session** - Automatically saves chat history to `data/chat_history/`

### Session Storage

All chat sessions are automatically saved as JSON files:

```
data/chat_history/
├── chat_session_20251127_140000.json
├── chat_session_20251127_141530.json
└── chat_session_20251127_143045.json
```

Each session file contains:
- Timestamp
- Response mode used
- Total messages
- Full conversation history with Q&A pairs

### Example Usage

```bash
$ python langgraph_chat_cli.py concise

======================================================================
LANGGRAPH AGENT - INTERACTIVE CHAT MODE
Response Mode: CONCISE
======================================================================

Ask a question (or 'quit' to exit): What are the main incident causes?

[PROCESSING] Searching knowledge base...

Q: What are the main incident causes?
----------------------------------------------------------------------
A: Based on the knowledge base, the main incident causes include:
1. Configuration errors - improper system settings
2. Resource exhaustion - CPU, memory, or storage limits
3. Network connectivity issues - DNS or routing problems
...
----------------------------------------------------------------------

Satisfied? (yes/no/followup): yes
[OK] Great! Ask another question or type 'quit' to exit.

Ask a question (or 'quit' to exit): What remediation steps are recommended?

[PROCESSING] Searching knowledge base...
...

Ask a question (or 'quit' to exit): quit

======================================================================
SESSION SUMMARY
======================================================================
Total Questions: 2
Response Mode: concise

Conversation History:
  1. Q: What are the main incident causes?
     A: Based on the knowledge base, the main incident causes include...
  2. Q: What remediation steps are recommended?
     A: The recommended remediation steps include...

======================================================================

[OK] Session saved to: data/chat_history/chat_session_20251127_140000.json

[OK] Chat session completed
    Questions asked: 2
    Session saved to: data/chat_history/chat_session_20251127_140000.json
```

### Programmatic Usage (Python)

You can also invoke chat mode directly from Python:

```python
from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Start interactive chat
result = agent.invoke(
    operation="chat",
    response_mode="concise",  # or "internal", "verbose"
    show_history=True
)

# Access results
print(f"Messages: {result['message_count']}")
print(f"Session: {result['session_file']}")
print(f"History: {result['conversation_history']}")
```

### Features

✓ Interactive multi-turn conversation  
✓ Human feedback loop (satisfaction tracking)  
✓ Automatic retry with verbose mode if unsatisfied  
✓ Session persistence (JSON storage)  
✓ Response mode selection (concise/internal/verbose)  
✓ Guardrails integration per response mode  
✓ Tool tracing in verbose mode  
✓ Clean CLI formatting and progress indicators  

### Troubleshooting

**Q: No answers being returned?**
- Ensure knowledge base is ingested: `python test_agent_quick.py`
- Check database path in data_sources.json

**Q: Chat freezing or stuck?**
- Press `Ctrl+C` to interrupt
- Check logs in `logs/` directory

**Q: Want to see more verbose output?**
- Use `python langgraph_chat_cli.py verbose`
- This shows all retrieval and tool traces

