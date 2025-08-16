from typing import TypedDict, Annotated, Union, Optional
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: Annotated[list[AnyMessage], add_messages]
    tools: list[str]
    sources: Annotated[list[str], add_messages]
    urls: Annotated[list[str], add_messages]
    chat_history: str
    agent_type: list[str]
