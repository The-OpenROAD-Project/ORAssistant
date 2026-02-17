"""
Custom DeepEvalLLM wrapper using Google Gemini API (google.genai).
"""

import os
from typing import Any, Optional, Type

from google import genai
from google.genai import types
from deepeval.models.base_model import DeepEvalBaseLLM
from pydantic import BaseModel


class Response(BaseModel):
    content: str


class GoogleGeminiLangChain(DeepEvalBaseLLM):
    """Class that implements Google Gemini API for DeepEval"""

    def __init__(self, model_name, *args, **kwargs):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        super().__init__(model_name, *args, **kwargs)

    def load_model(self, *args, **kwargs):
        return self.client.models

    def generate(self, prompt: str, schema: Optional[Type[BaseModel]] = None) -> Any:
        if schema is not None:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return response.parsed, 0
        else:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text, 0

    async def a_generate(
        self, prompt: str, schema: Optional[Type[BaseModel]] = None
    ) -> Any:
        if schema is not None:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return response.parsed, 0
        else:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text, 0

    def get_model_name(self):
        return self.model_name or "model-not-specified"


def main():
    model = GoogleGeminiLangChain(model_name="gemini-2.5-pro")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = model.generate(prompt, schema=Response)
    print(f"Response: {response}")


async def main_async():
    model = GoogleGeminiLangChain(model_name="gemini-2.5-pro")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = await model.a_generate(prompt, schema=Response)
    print(f"Response: {response}")


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main_async())
