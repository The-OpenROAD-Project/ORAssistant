import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from ..models.response_model import SuggestedQuestionInput, SuggestedQuestions
from ...prompts.prompt_templates import suggested_questions_prompt_template
from openai import OpenAI

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set")

model = "gemini-2.0-flash"
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GOOGLE_API_KEY,
)

router = APIRouter(prefix="/helpers", tags=["helpers"])


# Main Router
@router.post("/suggestedQuestions")
async def get_suggested_questions(
    suggested_question_input: SuggestedQuestionInput,
) -> SuggestedQuestions:
    full_prompt = suggested_questions_prompt_template.format(
        latest_question=suggested_question_input.latest_question,
        assistant_answer=suggested_question_input.assistant_answer,
    )

    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt},
            ],
            response_format=SuggestedQuestions,
        )
        response_data = response.choices[0].message.parsed
        if not response_data or not SuggestedQuestions.model_validate(response_data):
            raise ValueError(
                f"Invalid response format from the model, got {response_data}"
            )
        return SuggestedQuestions.model_validate(response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to get suggested questions: " + str(e)
        )
