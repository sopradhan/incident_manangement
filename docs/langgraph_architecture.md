# RAG Master Agent LangGraph Architecture

## Overview
The RAG Master Agent uses LangGraph to coordinate document ingestion and retrieval operations through a sophisticated state management system with TodoList middleware integration.

## Graph Structure

### Nodes
- **Input Processing**: Analyzes incoming requests
- **TodoList Middleware**: Manages task tracking (write_todos/read_todos)
- **Decision Engine**: Master agent analysis and subagent selection
- **Subagent Delegation**: Routes to ingestion or retrieval subagents
- **Result Aggregation**: Combines subagent results
- **Output Processing**: Formats final response

### State Management
- **Conversation State**: Maintains dialogue history and context
- **TodoList State**: Tracks task progression and coordination
- **Metrics State**: Performance and operation tracking
- **Error State**: Error handling and recovery information

### Middleware Integration
- **TodoListMiddleware**: Automatically provided by deepagents
- **Tools Available**: write_todos, read_todos
- **State Persistence**: Managed by LangGraph state system
- **Coordination**: Master-subagent task tracking

### Subagent Architecture
- **Ingestion SubAgent**: Document processing, chunking, embedding, storage
- **Retrieval SubAgent**: Vector search, ranking, answer synthesis
- **Parent Communication**: Results reported back to master agent
- **Independent Execution**: Each subagent has its own processing pipeline

## Workflow Process

1. **Request Input** -> Master agent receives operation request
2. **TodoList Init** -> write_todos creates tracking tasks
3. **Analysis Phase** -> Master analyzes and decides on subagent
4. **Delegation** -> Routes to appropriate subagent(s)
5. **Execution** -> Subagent processes the request
6. **Aggregation** -> Master combines and validates results
7. **TodoList Update** -> Marks tasks as completed
8. **Response** -> Returns structured result with metrics

## Key Benefits
- **Trackable Workflows**: TodoList provides visibility into coordination
- **State Persistence**: LangGraph maintains context across invocations
- **Error Recovery**: Built-in retry and error handling mechanisms
- **Scalable Architecture**: Easy to add new subagents and capabilities
- **Performance Monitoring**: Comprehensive metrics and timing data
