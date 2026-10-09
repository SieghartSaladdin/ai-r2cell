from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class MainState(TypedDict):
    """
    State definition for the R2Cell main agent.
    
    Attributes:
        messages: A sequence of BaseMessage objects representing the conversation history.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]

