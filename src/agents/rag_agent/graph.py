import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.agents.rag_agent.state import RAGState
from src.agents.rag_agent.nodes import retrieve, call_model

# Determine checkpoints DB path at the root of the workspace
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
CHECKPOINTS_DB_PATH = os.path.join(WORKSPACE_ROOT, "checkpoints.db")

import sqlite3

# Initialize SqliteSaver checkpointer for database-backed conversation session persistence
# We use a persistent connection with check_same_thread=False for thread safety in FastAPI
db_conn = sqlite3.connect(CHECKPOINTS_DB_PATH, check_same_thread=False)
memory = SqliteSaver(db_conn)

# Build the StateGraph workflow
workflow = StateGraph(RAGState)

# Add execution nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("call_model", call_model)

# Define sequential transitions
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "call_model")
workflow.add_edge("call_model", END)

# Compile the final graph execution engine with memory
rag_graph = workflow.compile(checkpointer=memory)
