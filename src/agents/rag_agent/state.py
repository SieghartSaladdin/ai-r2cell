from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class RAGState(TypedDict):
    """
    State definition for the R2Cell RAG agent.
    
    Attributes:
        messages: A sequence of BaseMessage objects representing the conversation history.
        context: A string container to hold retrieved PDF document chunks.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
