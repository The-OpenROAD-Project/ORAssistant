import json

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from pydantic import BaseModel
from langserve import add_routes

from src.chain import llm_chain_with_source

class UserInput(BaseModel):
    query: str;

app = FastAPI()

with open("src/source_list.json") as f:
    src_dict = json.loads(f.read())

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

@app.post("/chatApp")
async def get_response(userInput : UserInput) -> str:
    links = []
    user_question = userInput.query
    result = llm_chain_with_source.invoke(user_question)

    for i in result['context']:
        links.append(src_dict[i.metadata['source']])
    
    links = set(links)

    response = result['answer']
    response += "\nSources:"

    for i in links:
        response += "\n" + i

    return response

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
