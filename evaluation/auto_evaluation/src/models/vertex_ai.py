"""
Code is adapted from https://github.com/meteatamel/genai-beyond-basics/blob/main/samples/evaluation/deepeval/vertex_ai/google_vertex_ai_langchain.py
Custom DeepEvalLLM wrapper.
"""

from typing import Any

from langchain_google_vertexai import ChatVertexAI, HarmBlockThreshold, HarmCategory
from deepeval.models.base_model import DeepEvalBaseLLM


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

        return ChatVertexAI(
            model_name=self.model_name,
            safety_settings=safety_settings,
        )

    def generate(self, prompt: str) -> Any:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> Any:
        response = await self.model.ainvoke(prompt)
        return response.content

    def get_model_name(self):
        return self.model_name


def main():
    model = GoogleVertexAILangChain(model_name="gemini-1.5-pro-002")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = model.generate(prompt)
    print(f"Response: {response}")


async def main_async():
    model = GoogleVertexAILangChain(model_name="gemini-1.5-pro-002")
    prompt = "Write me a joke"
    print(f"Prompt: {prompt}")
    response = await model.a_generate(prompt)
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
    # asyncio.run(main_async())
