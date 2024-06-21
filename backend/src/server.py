from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from pydantic import BaseModel

from .chains.hybrid_retriever_chain import HybridRetrieverChain

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

class UserInput(BaseModel):
    query: str
    listSources: bool = False
    listContext: bool = False


app = FastAPI()

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)
prompt_template_str = """
    Use the following context:

    {context}

    -------------------------------------------------------------------------------------------------
    Your task is to act as a knowledgeable assistant for users seeking information and guidance about the OpenROAD project. Avoid speculating or inventing information beyond the scope of the provided data.
    Note that OR refers to OpenROAD and ORFS refers to OpenROAD-Flow-Scripts

    Give a detailed answer to this question: 
    {question}

    """

retriever = HybridRetrieverChain(
    llm_model=llm,
    prompt_template_str=prompt_template_str,
    embeddings_model_name="BAAI/bge-large-en-v1.5",
    reranking_model_name="BAAI/bge-reranker-base",
    contextual_rerank=True,
    use_cuda=True,
    docs_path=["./data/markdown/ORFS_docs", "./data/markdown/OR_docs"],
    manpages_path=["./data/markdown/manpages"],
)

retriever_chain = retriever.get_llm_chain()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


@app.post("/chatApp")
async def get_response(userInput: UserInput) -> dict:
    user_question = userInput.query
    result = retriever_chain.invoke(user_question)

    links = []
    context = []
    for i in result["context"]:
        if "url" in i.metadata:
            links.append(i.metadata["url"])
        elif "source" in i.metadata:
            links.append(i.metadata["source"])
        context.append(i.page_content)

    links = set(links)

    if userInput.listSources and userInput.listContext:
        response = {
            "response": result["answer"],
            "sources": (links),
            "context": (context),
        }
    elif userInput.listSources:
        response = {"response": result["answer"], "sources": (links)}
    elif userInput.listContext:
        response = {"response": result["answer"], "context": (context)}
    else:
        response = {"response": result["answer"]}

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
