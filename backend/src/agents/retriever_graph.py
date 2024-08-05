from .retriever_agent import RetrieverAgent

from typing import TypedDict, Annotated, Union, Optional, Any
from langchain_core.messages import AnyMessage

from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph
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
    urls: list[str]


class ToolNode:
    def __init__(self, tool_fn: Any) -> None:
        self.tool_fn = tool_fn

    def get_node(self, state: AgentState) -> dict[str, list[str]]:
        query = state['messages'][-1].content
        if query is None:
            raise ValueError('Query is None')
        response, sources, urls = self.tool_fn(query)
        return {'context': [response], 'sources': sources, 'urls': urls}


class RetrieverGraph:
    def __init__(
        self,
        llm_model: Union[ChatGoogleGenerativeAI, ChatVertexAI],
        embeddings_config: dict[str, str],
        reranking_model_name: str,
        use_cuda: bool = False,
    ):
        self.llm = llm_model
        self.retriever_agent: RetrieverAgent = RetrieverAgent()
        self.retriever_agent.initialize(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
        )
        self.graph: Optional[CompiledGraph] = None

    def agent(self, state: AgentState) -> dict[str, list[str]]:
        messages = state['messages'][-1].content

        if self.llm is None:
            return {'tools': []}

        model = self.llm.bind_tools([
            self.retriever_agent.retrieve_cmds,
            self.retriever_agent.retrieve_install,
            self.retriever_agent.retrieve_general,
            self.retriever_agent.retrieve_opensta,
            self.retriever_agent.retrieve_errinfo,
            self.retriever_agent.retrieve_yosys_rtdocs,
        ])

        response = model.invoke(messages)

        if response is None or response.tool_calls is None:  # type: ignore
            return {'tools': []}

        return {'tools': response.tool_calls}  # type: ignore

    def generate(self, state: AgentState) -> dict[str, list[AnyMessage]]:
        query = state['messages'][-1].content
        context = state['context'][-1]
        llm_chain = BaseChain(
            llm_model=self.llm,
            prompt_template_str=summarise_prompt_template,
        ).get_llm_chain()

        ans = llm_chain.invoke({'context': context, 'question': query})

        if ans is not None:
            return {'messages': [ans]}

        return {'messages': []}

    def route(self, state: AgentState) -> list[str]:
        tools = state['tools']

        if tools == []:
            return ['retrieve_general']

        tool_names = [tool['name'] for tool in tools if 'name' in tool]  # type: ignore

        return tool_names

    def initialize(self) -> None:
        workflow = StateGraph(AgentState)

        commands = ToolNode(self.retriever_agent.retrieve_cmds)
        install = ToolNode(self.retriever_agent.retrieve_install)
        general = ToolNode(self.retriever_agent.retrieve_general)
        opensta = ToolNode(self.retriever_agent.retrieve_opensta)
        errinfo = ToolNode(self.retriever_agent.retrieve_errinfo)
        yosys_rtdocs = ToolNode(self.retriever_agent.retrieve_yosys_rtdocs)

        workflow.add_node('agent', self.agent)
        workflow.add_node('generate', self.generate)

        workflow.add_node('retrieve_cmds', commands.get_node)
        workflow.add_node('retrieve_install', install.get_node)
        workflow.add_node('retrieve_general', general.get_node)
        workflow.add_node('retrieve_opensta', opensta.get_node)
        workflow.add_node('retrieve_errinfo', errinfo.get_node)
        workflow.add_node('retrieve_yosys_rtdocs', yosys_rtdocs.get_node)

        workflow.add_edge(START, 'agent')
        workflow.add_conditional_edges(
            'agent',
            self.route,  # type: ignore
            [
                'retrieve_cmds',
                'retrieve_install',
                'retrieve_general',
                'retrieve_opensta',
                'retrieve_errinfo',
                'retrieve_yosys_rtdocs',
            ],
        )

        workflow.add_edge('retrieve_cmds', 'generate')
        workflow.add_edge('retrieve_install', 'generate')
        workflow.add_edge('retrieve_general', 'generate')
        workflow.add_edge('retrieve_opensta', 'generate')
        workflow.add_edge('retrieve_errinfo', 'generate')
        workflow.add_edge('retrieve_yosys_rtdocs', 'generate')

        workflow.add_edge('generate', END)

        self.graph = workflow.compile()

        return
