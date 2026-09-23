"""
Custom DeepEvalLLM wrapper using Google Gemini API (google.genai).
"""

import asyncio
import os
from typing import Any, Optional, Type

from google import genai
from google.genai import errors, types
from deepeval.models.base_model import DeepEvalBaseLLM
from pydantic import BaseModel


class Response(BaseModel):
    content: str


class GoogleGeminiLangChain(DeepEvalBaseLLM):
    """Class that implements Google Gemini API for DeepEval"""

    MAX_GENERATE_ATTEMPTS = 8
    MAX_RETRY_DELAY_SECONDS = 30

    def __init__(self, model_name, *args, **kwargs):
        self._model_name = model_name
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        super().__init__(model_name, *args, **kwargs)

    def load_model(self, *args, **kwargs):
        return self.client.models

    def generate(self, prompt: str, schema: Optional[Type[BaseModel]] = None) -> Any:
        if schema is not None:
            response = self.client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return response.parsed
        else:
            response = self.client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            return response.text

    async def a_generate(
        self, prompt: str, schema: Optional[Type[BaseModel]] = None
    ) -> Any:
        config = None
        if schema is not None:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            )

        for attempt in range(self.MAX_GENERATE_ATTEMPTS):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                )
                break
            except errors.ServerError:
                if attempt == self.MAX_GENERATE_ATTEMPTS - 1:
                    raise
                delay = min(2**attempt, self.MAX_RETRY_DELAY_SECONDS)
                await asyncio.sleep(delay)

        if schema is not None:
            return response.parsed
        return response.text

    def get_model_name(self):
        return self._model_name or "model-not-specified"


def main():
    model = GoogleGeminiLangChain(model_name="gemini-3.1-pro-preview")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = model.generate(prompt, schema=Response)
    print(f"Response: {response}")


async def main_async():
    model = GoogleGeminiLangChain(model_name="gemini-3.1-pro-preview")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = await model.a_generate(prompt, schema=Response)
    print(f"Response: {response}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(main_async())
