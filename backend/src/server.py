from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from pydantic import BaseModel

from .ensemble_chain import llm_chain_with_source


class UserInput(BaseModel):
    query: str
    listSources: bool = False
    listContext: bool = False


app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


@app.post("/chatApp")
async def get_response(userInput: UserInput) -> dict:
    user_question = userInput.query
    result = llm_chain_with_source.invoke(user_question)

    links = []
    context = []
    for i in result["context"]:
        links.append(i.metadata["url"])
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
