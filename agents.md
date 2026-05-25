# Agent Development Guidelines (agents.md)

Welcome, Agent. This repository operates under strict modular, graph-centric architectural principles. You are required to read, understand, and enforce these guidelines for every action, file modification, and design task you undertake in this workspace.

---

## 1. Core Architectural Principles

To maximize debugging efficiency, maintainability, and scalability, all development must adhere to the following pillars:

### A. Agent-Based Structure
All workflows, state machines, and specialized agent reasoning loops must be isolated within their own subdirectories under the `/src/agents/` prefix.
* **Standard Pattern**: `/src/agents/<agent_name>/`
* **Example**: `/src/agents/rag_agent/` or `/src/agents/customer_service_seller/`
* **Rule**: Keep agent-specific business logic, internal validation, and workflow states contained inside their respective agent directory.

### B. Separation of Graph Concerns
Inside each individual agent module (e.g., `/src/agents/rag_agent/`), you must strictly separate logic into the following dedicated files:
1. **`state.py`**: Defines the `GraphState` schemas (using `TypedDict`, `Pydantic`, or Python typing classes) and custom reducers (like `add_messages`).
2. **`nodes.py`**: Contains the execution node functions that perform computations, query tools, or call LLMs. Nodes should consume the state, perform a single task, and return updated state attributes.
3. **`graph.py`**: Handles building the `StateGraph` builder, defining all nodes, connecting them with entry points, edges, and conditional routing, and compiling the final graph (with checkpointers or memory).
4. **`prompts.py`**: Stores all system prompts, instruction templates, few-shot examples, and agent persona configurations. No raw prompt strings should be inline in `nodes.py`.

### C. Core Infrastructure Isolation
Shared, global infrastructure that is not specific to a single agent must be kept in the `/src/core/` directory. This includes:
* **LLM Initializers**: Global LLM configuration and client setups (e.g., Ollama, OpenAI, Anthropic).
* **Vector Databases**: Core database setups, embeddings, and vector store providers (e.g., ChromaDB, Pgvector).
* **Memory & Persistence**: Shared LangGraph checkpointers, database connections, and session managers.

### D. Reusable Tools
* All custom tools bound to LLMs using LangChain's `@tool` decorator must reside in the `/src/tools/` directory.
* **Rule**: Keep tools generic, reusable, and self-contained with thorough type definitions and clear docstrings so they can be easily shared across multiple agents.

### E. API / Interface Layer
* The entry point layer (e.g., FastAPI, Twilio Webhook, or CLI interfaces) in `/src/main.py` or `/src/api/` must contain zero agent logic or routing logic.
* **Rule**: The API layer simply imports the compiled graph from the `agents` directory, initializes the thread/session, invokes or streams from the compiled graph, and returns the response.

---

## 2. Standardized Directory Layout

All work in this repository should construct files according to the layout below:

```plaintext
ai-r2cell/
├── .env                  # Shared environment keys
├── langgraph.json        # LangGraph CLI config
├── agents.md             # This guidelines file
├── pyproject.toml        # Poetry/uv/Pip dependencies
│
└── src/
    ├── core/             # Shared core infrastructure
    │   ├── __init__.py
    │   ├── llm.py        # Ollama/OpenAI initializations
    │   ├── database.py   # DB clients and connection pools
    │   └── vectorstore.py# ChromaDB client & embeddings
    │
    ├── tools/            # Shared reusable tools for agents
    │   ├── __init__.py
    │   ├── search.py     # Search tools
    │   └── crm.py        # CRM tools
    │
    ├── agents/           # Specialized agent modules
    │   ├── __init__.py
    │   └── rag_agent/    # RAG agent module
    │       ├── __init__.py
    │       ├── state.py  # GraphState definition
    │       ├── nodes.py  # Node functions
    │       ├── graph.py  # StateGraph compilation & edges
    │       └── prompts.py# System prompts & templates
    │
    └── main.py           # FastAPI server & route handlers (invokes compiled agents)
```

---

## 3. Predictive Error Evasion (PEE) & Verification

Whenever you modify any agent graph, verify your changes against the following safety guidelines:

* **No Infinite Loops**: Always define a maximum recursion limit in your graph invocations and monitor state cycles.
* **Schema Safety**: Do not modify state schemas (`state.py`) without checking all corresponding nodes to ensure they unpack and return correct keys.
* **Asynchronous Integrity**: Keep heavy API calls inside tools or nodes thread-safe and non-blocking.
* **Clean Fallbacks**: Ensure every node catching an exception logs it to the state so that subsequent nodes can gracefully handle the failure instead of raising unhandled exceptions.
