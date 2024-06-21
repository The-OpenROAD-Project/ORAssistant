from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate

from langchain_core.output_parsers import StrOutputParser

from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional


class BaseChain:
    def __init__(
        self,
        llm_model: Optional[ChatGoogleGenerativeAI],
        prompt_template_str: Optional[str],
    ):
        self.llm_model = llm_model
        self.prompt_template = ChatPromptTemplate.from_template(prompt_template_str)

        self.llm_chain = None

    def create_llm_chain(self) -> None:
        self.llm_chain = self.prompt_template | self.llm_model | StrOutputParser()
        return

    def get_llm_chain(self) -> ChatGoogleGenerativeAI:
        if self.llm_chain is None:
            self.create_llm_chain()
        return self.llm_chain


if __name__ == "__main__":
    load_dotenv()
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=1)
    prompt_template_str = """
    Give a detailed answer to this question: 
    {question}
    """

    basechain = BaseChain(llm_model=llm, prompt_template_str=prompt_template_str)

    basechain = basechain.get_llm_chain()

    while True:
        user_question = input("\n\nAsk a question: ")
        result = basechain.invoke(user_question)
        print(result)
