from fastapi import APIRouter, Request, Response
import httpx
import os

router = APIRouter(prefix="/ui", tags=["ui"])

BACKEND_ENDPOINT = os.getenv('BACKEND_ENDPOINT')
BACKEND_ENDPOINT_HELPERS = os.getenv('BACKEND_ENDPOINT_HELPERS')


@router.post("/chat")
async def proxy_chat(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        resp = await client.post(BACKEND_ENDPOINT, json=data)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get('content-type')
    )


@router.post("/suggestedQuestions")
async def suggested_questions(request: Request):
    data = await request.json()
    # Transform camelCase to snake_case for the backend
    transformed_data = {
        "latest_question": data.get("latestQuestion", ""),
        "assistant_answer": data.get("assistantAnswer", "")
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(BACKEND_ENDPOINT_HELPERS, json=transformed_data)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get('content-type')
    )
