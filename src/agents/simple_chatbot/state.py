from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ChatbotState(TypedDict):
    """
    State definition for the simple chatbot.
    Tracks conversation messages using LangGraph's add_messages reducer.
    """
    messages: Annotated[list[AnyMessage], add_messages]
