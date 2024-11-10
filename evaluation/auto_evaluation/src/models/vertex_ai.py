"""
Code is adapted from https://github.com/meteatamel/genai-beyond-basics/blob/main/samples/evaluation/deepeval/vertex_ai/google_vertex_ai_langchain.py
Custom DeepEvalLLM wrapper.
"""

import instructor

from typing import Any
from vertexai.generative_models import GenerativeModel, HarmBlockThreshold, HarmCategory  # type: ignore
from deepeval.models.base_model import DeepEvalBaseLLM
from pydantic import BaseModel


class Response(BaseModel):
    content: str


class GoogleVertexAILangChain(DeepEvalBaseLLM):
    """Class that implements Vertex AI via LangChain for DeepEval"""

    def __init__(self, model_name, *args, **kwargs):
        super().__init__(model_name, *args, **kwargs)

    def load_model(self, *args, **kwargs):
        # Initialize safety filters for Vertex AI model
        # This is important to ensure no evaluation responses are blocked
        safety_settings = {
            HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }

        return GenerativeModel(
            model_name=self.model_name,
            safety_settings=safety_settings,
        )

    def generate(self, prompt: str, schema: BaseModel) -> Any:
        instructor_client = instructor.from_vertexai(
            client=self.load_model(),
            mode=instructor.Mode.VERTEXAI_TOOLS,
        )
        resp = instructor_client.messages.create(  # type: ignore
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=schema,
        )
        return resp

    async def a_generate(self, prompt: str, schema: BaseModel) -> Any:
        instructor_client = instructor.from_vertexai(
            client=self.load_model(),
            mode=instructor.Mode.VERTEXAI_TOOLS,
            _async=True,
        )
        resp = await instructor_client.messages.create(  # type: ignore
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=schema,
        )
        return resp

    def get_model_name(self):
        return self.model_name


def main():
    model = GoogleVertexAILangChain(model_name="gemini-1.5-pro-002")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = model.generate(prompt, schema=Response)
    print(f"Response: {response}")


async def main_async():
    model = GoogleVertexAILangChain(model_name="gemini-1.5-pro-002")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = await model.a_generate(prompt, Response)
    print(f"Response: {response}")


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()
    # main()
    asyncio.run(main_async())
