from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument
from langchain_community.document_loaders import DirectoryLoader

from src.tools.recursive_chunk import recursive_chunking

md_seperators = [
    "\n#{1,6} ",
    "```\n",
    "\n\\*\\*\\*+\n",
    "\n---+\n",
    "\n___+\n",
    "\n\n",
    "\n",
    " ",
    "",
]

def chunk_markdown(embeddings_model_name: str , files_path: str):
    loader = DirectoryLoader(files_path, glob="**/*.md" ,show_progress=True)
    documents = loader.load()

    documents_knowledge_base = [
        LangchainDocument(page_content=doc.page_content, metadata=doc.metadata)
        for doc in (documents)
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50, 
        add_start_index=True, 
        strip_whitespace=True,  
        separators=md_seperators,
    )

    docs_processed = []
    for doc in documents_knowledge_base:
        docs_processed += text_splitter.split_documents([doc])


    docs_processed = recursive_chunking(
        256,
        documents_knowledge_base,
        tokenizer_name=embeddings_model_name,
    )

    return docs_processed