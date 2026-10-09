import os
import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition

from src.agents.main_agent.state import MainState
from src.agents.main_agent.nodes import call_model
from src.tools.search import query_knowledge_base
from src.tools.booking import query_products, book_cod_appointment, get_bandung_gmaps_location

# Determine checkpoints DB path at the root of the workspace
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
CHECKPOINTS_DB_PATH = os.path.join(WORKSPACE_ROOT, "checkpoints.db")

# Initialize SqliteSaver checkpointer for database-backed conversation session persistence
# We use a persistent connection with check_same_thread=False for thread safety in FastAPI
db_conn = sqlite3.connect(CHECKPOINTS_DB_PATH, check_same_thread=False)
memory = SqliteSaver(db_conn)

# Build the StateGraph workflow
workflow = StateGraph(MainState)

# Add execution nodes
workflow.add_node("call_model", call_model)
# Standard prebuilt ToolNode automatically manages executing list of tools
workflow.add_node("tools", ToolNode([
    query_knowledge_base,
    query_products,
    book_cod_appointment,
    get_bandung_gmaps_location
]))

# Define transitions
workflow.add_edge(START, "call_model")
# Conditional routing: if LLM output requires tools, run tools node, otherwise end
workflow.add_conditional_edges("call_model", tools_condition)
# Loop back from tools node to call_model node for final response generation
workflow.add_edge("tools", "call_model")

# Compile the final graph execution engine with memory
main_graph = workflow.compile(checkpointer=memory)
