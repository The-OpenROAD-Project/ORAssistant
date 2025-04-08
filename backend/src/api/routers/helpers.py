import os
from typing import Any
from fastapi import APIRouter,HTTPException
from dotenv import load_dotenv
from typing import Union
from ..models.response_model import SuggestedQuestions, SuggestedQuestionInput
import requests
from ..prompts.prompt_templates import suggested_questions_prompt_template

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

GEMINI_ROUTE = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

router = APIRouter(prefix="/helpers", tags=["helpers"])

# Main Router
@router.post("/suggestedQuestions",response_model=SuggestedQuestions)
async def get_suggested_questions(
    suggested_question_input: SuggestedQuestionInput
) -> SuggestedQuestions:
    
    full_prompt = f"{suggested_questions_prompt_template}\n\nUser Question: {suggested_question_input.latest_question}\n\nAssistant Answer: {suggested_question_input.assistant_answer}"
    body = {
    "contents": [
        {
            "parts": [
                { "text": full_prompt }
            ]
        }
        ]
    }

    try:
        response = requests.post(GEMINI_ROUTE, json=body,headers={"Content-Type": "application/json"})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get suggested questions: "+str(e))
