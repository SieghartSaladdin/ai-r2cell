import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import ChatbotState
from .nodes import call_model

# 1. Define the workflow structure using ChatbotState schema
workflow = StateGraph(ChatbotState)

# 2. Add the execution nodes
workflow.add_node("chatbot", call_model)

# 3. Add edges (Start -> chatbot -> End)
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)

# 4. Initialize SQLite checkpointer for database session persistence
# We use check_same_thread=False to make it safe for multi-threaded APIs like FastAPI
db_conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(db_conn)

# 5. Compile the final graph execution engine
chatbot_graph = workflow.compile(checkpointer=memory)
