from ..chains.hybrid_retriever_chain import HybridRetrieverChain

from langchain_core.tools import tool
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever

from typing import Tuple, Optional, Union


class RetrieverAgent:
    def __init__(self) -> None:
        pass

    install_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]
    cmds_retriever: Optional[Union[EnsembleRetriever, ContextualCompressionRetriever]]
    general_retriever: Optional[
        Union[EnsembleRetriever, ContextualCompressionRetriever]
    ]

    def initialize(
        self,
        embeddings_model_name: str,
        reranking_model_name: str,
        use_cuda: bool = False,
    ) -> None:
        install_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=[
                './data/markdown/ORFS_docs/installation',
                './data/markdown/OR_docs/installation',
            ],
            contextual_rerank=True,
            search_k=10,
        )
        install_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.install_retriever = install_retriever_chain.retriever

        cmds_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=['./data/markdown/OR_docs/tools'],
            manpages_path=['./data/markdown/manpages'],
            contextual_rerank=True,
            search_k=10,
        )
        cmds_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.cmds_retriever = cmds_retriever_chain.retriever

        general_retriever_chain = HybridRetrieverChain(
            embeddings_model_name=embeddings_model_name,
            reranking_model_name=reranking_model_name,
            use_cuda=use_cuda,
            docs_path=[
                './data/markdown/ORFS_docs',
                './data/markdown/OR_docs',
            ],
            manpages_path=['./data/markdown/manpages'],
            contextual_rerank=True,
            search_k=10,
        )
        general_retriever_chain.create_hybrid_retriever()
        RetrieverAgent.general_retriever = general_retriever_chain.retriever

    @staticmethod
    @tool
    def retrieve_general(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve any general information related to OpenROAD and OpenROAD-flow-scripts
        """
        if RetrieverAgent.general_retriever is not None:
            docs = RetrieverAgent.general_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs

    @staticmethod
    @tool
    def retrieve_cmds(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve information related to the commands and tools in OpenROAD and OpenROAD-flow-scripts
        """
        if RetrieverAgent.cmds_retriever is not None:
            docs = RetrieverAgent.cmds_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs

    @staticmethod
    @tool
    def retrieve_install(query: str) -> Tuple[str, list[str]]:
        """
        Retrieve information related to the installation of OpenROAD and OpenROAD-flow-scripts
        """
        if RetrieverAgent.install_retriever is not None:
            docs = RetrieverAgent.install_retriever.invoke(input=query)

        doc_text = ''
        doc_srcs = []
        for doc in docs:
            doc_text += f'\n\n- - - - - - - - - - - - - - - \n\n{doc.page_content}'
            if 'url' in doc.metadata:
                doc_srcs.append(doc.metadata['url'])
            elif 'source' in doc.metadata:
                doc_srcs.append(doc.metadata['source'])

        return doc_text, doc_srcs
