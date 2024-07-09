from .retriever_agent import RetrieverAgent

from typing import TypedDict, Annotated, Union, Optional
from langchain_core.messages import AnyMessage

from langgraph.graph import START, StateGraph, END
from langgraph.graph.message import add_messages

from ..chains.base_chain import BaseChain
from ..prompts.answer_prompts import summarise_prompt_template


from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: Annotated[list[str], add_messages]
    tools: list[str]
    sources: list[str]


class ToolNode:
    def __init__(self, tool_fn):
        self.tool_fn = tool_fn

    def get_node(self, state):
        query = state["messages"][-1].content
        response, sources = self.tool_fn(query)
        return {"context": [response], "sources": sources}


class RetrieverGraph:
    def __init__(
        self,
        llm_model: Optional[Union[ChatGoogleGenerativeAI, ChatVertexAI]] = None,
    ):
        self.llm = llm_model
        self.retriever_agent: RetrieverAgent = RetrieverAgent()
        self.graph: Optional[StateGraph] = None
        load_dotenv()

    def agent(self, state: AgentState):
        print("--CALL AGENT--")
        messages = state["messages"][-1].content
        model = self.llm.bind_tools([
            self.retriever_agent.retrieve_cmds,
            self.retriever_agent.retrieve_install,
            self.retriever_agent.retrieve_general,
        ])
        response = model.invoke(messages)
        return {"tools": response.tool_calls}

    def generate(self, state: AgentState):
        print("--GENERATE--")
        query = state["messages"][-1].content
        context = state["context"][-1].content
        llm_chain = BaseChain(
            llm_model=self.llm,
            prompt_template_str=summarise_prompt_template,
        ).get_llm_chain()

        ans = llm_chain.invoke({"context": context, "question": query})
        return {"messages": [ans]}

    def route(self, state: AgentState):
        print("--ROUTE--")
        tools = state["tools"]
        tool_names = []
        if tools == []:
            return ["retrieve_general"]
        for tool in tools:
            tool_names.append(tool["name"])
        return tool_names

    def initialize(self):
        workflow = StateGraph(AgentState)

        commands = ToolNode(self.retriever_agent.retrieve_cmds)
        install = ToolNode(self.retriever_agent.retrieve_install)
        general = ToolNode(self.retriever_agent.retrieve_general)

        workflow.add_node("agent", self.agent)
        workflow.add_node("generate", self.generate)

        workflow.add_node("retrieve_cmds", commands.get_node)
        workflow.add_node("retrieve_install", install.get_node)
        workflow.add_node("retrieve_general", general.get_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self.route,
            ["retrieve_cmds", "retrieve_install", "retrieve_general"],
        )

        workflow.add_edge("retrieve_cmds", "generate")
        workflow.add_edge("retrieve_install", "generate")
        workflow.add_edge("retrieve_general", "generate")

        workflow.add_edge("generate", END)

        self.graph = workflow.compile()

        return