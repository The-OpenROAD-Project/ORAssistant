from .retriever_agent import RetrieverAgent

from typing import TypedDict, Annotated, Union, Optional, Any
from langchain_core.messages import AnyMessage

from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages

from ..chains.base_chain import BaseChain
from ..prompts.answer_prompts import (
    summarise_prompt_template,
    tool_calling_prompt_template,
)

from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain.tools.render import render_text_description
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate

import os
import logging

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: Annotated[list[str], add_messages]
    tools: list[str]
    sources: Annotated[list[str], add_messages]
    urls: Annotated[list[str], add_messages]
    chat_history: str


class ToolNode:
    def __init__(self, tool_fn: Any) -> None:
        self.tool_fn = tool_fn

    def get_node(self, state: AgentState) -> dict[str, list[str]]:
        query = state['messages'][-1].content
        if query is None:
            raise ValueError('Query is None')

        response, sources, urls = self.tool_fn(query)

        if response != []:
            response = (
                [item for sublist in response for item in sublist]
                if isinstance(response[0], list)
                else response
            )
        if sources != []:
            sources = (
                [item for sublist in sources for item in sublist]
                if isinstance(sources[0], list)
                else sources
            )
        if urls != []:
            urls = (
                [item for sublist in urls for item in sublist]
                if isinstance(urls[0], list)
                else urls
            )
        return {'context': response, 'sources': sources, 'urls': urls}


class RetrieverGraph:
    def __init__(
        self,
        llm_model: Union[ChatGoogleGenerativeAI, ChatVertexAI, ChatOllama],
        embeddings_config: dict[str, str],
        reranking_model_name: str,
        inbuit_tool_calling: bool,
        use_cuda: bool = False,
    ):
        self.llm = llm_model
        self.retriever_agent: RetrieverAgent = RetrieverAgent()
        self.retriever_agent.initialize(
            embeddings_config=embeddings_config,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
        )

        self.retriever_tools = [
            self.retriever_agent.retrieve_cmds,
            self.retriever_agent.retrieve_install,
            self.retriever_agent.retrieve_general,
            self.retriever_agent.retrieve_opensta,
            self.retriever_agent.retrieve_errinfo,
            self.retriever_agent.retrieve_yosys_rtdocs,
        ]
        self.inbuit_tool_calling = inbuit_tool_calling

        self.tool_descriptions = ''
        for retriever_tool in self.retriever_tools:
            text_desc = render_text_description([retriever_tool])  # type: ignore
            text_desc.replace('(query: str) -> Tuple[str, list[str], list[str]]', ' ')
            self.tool_descriptions += text_desc + '\n\n'

        self.graph: Optional[CompiledGraph] = None
        self.llm_chain = BaseChain(
            llm_model=self.llm,
            prompt_template_str=summarise_prompt_template,
        ).get_llm_chain()

    def agent(self, state: AgentState) -> dict[str, list[str]]:
        messages = state['messages'][-1].content

        if self.llm is None:
            return {'tools': []}

        if self.inbuit_tool_calling:
            model = self.llm.bind_tools([
                self.retriever_agent.retrieve_cmds,
                self.retriever_agent.retrieve_install,
                self.retriever_agent.retrieve_general,
                self.retriever_agent.retrieve_opensta,
                self.retriever_agent.retrieve_errinfo,
                self.retriever_agent.retrieve_yosys_rtdocs,
            ])  # type: ignore
            response = model.invoke(messages)

            if response is None or response.tool_calls is None:  # type: ignore
                return {'tools': []}

            return {'tools': response.tool_calls}  # type: ignore
        else:
            tool_choice_chain = (
                ChatPromptTemplate.from_template(tool_calling_prompt_template)
                | self.llm
                | JsonOutputParser()
            )
            response = tool_choice_chain.invoke({
                'question': messages,
                'tool_descriptions': self.retriever_tools,
                'chat_history': state['chat_history'],
            })

            if response is None:
                logging.warn(
                    'Tool selection response not found. Returning empty tool list.'
                )
                return {'tools': []}

            if 'tool_names' in response:
                tool_calls = response.get('tool_names', [])
            else:
                logging.warn('Tool selection failed. Returning empty tool list.')

            if 'rephrased_question' in response:
                state['messages'][-1].content = response['rephrased_question']
            else:
                logging.warn('Rephrased question not found in response.')

            return {'tools': tool_calls}

    def generate(self, state: AgentState) -> dict[str, list[AnyMessage]]:
        query = state['messages'][-1].content
        context = state['context'][-1]

        ans = self.llm_chain.invoke({'context': context, 'question': query})

        if ans is not None:
            return {'messages': [ans]}

        return {'messages': []}

    def route(self, state: AgentState) -> list[str]:
        tools = state['tools']

        if tools == []:
            return ['retrieve_general']

        if self.inbuit_tool_calling:
            tool_names = [tool['name'] for tool in tools if 'name' in tool]  # type: ignore
            return tool_names
        else:
            return tools

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
