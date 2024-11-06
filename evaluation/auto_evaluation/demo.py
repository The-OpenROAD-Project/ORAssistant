import os

from dotenv import load_dotenv
from src.vertex_ai import GoogleVertexAILangChain
from src.metrics.accuracy import make_correctness_metric
from deepeval.test_case import LLMTestCase

cur_dir = os.path.dirname(__file__)
root_dir = os.path.join(cur_dir, "../../")
load_dotenv(os.path.join(root_dir, ".env"))

if __name__ == "__main__":
    model = GoogleVertexAILangChain(model_name="gemini-1.5-pro-002")
    cm = make_correctness_metric(model)
    test_case = LLMTestCase(
        input="The dog chased the cat up the tree, who ran up the tree?",
        actual_output="It depends, some might consider the cat, while others might argue the dog.",
        expected_output="The cat.",
    )

    cm.measure(test_case)
    print(cm.score)
    print(cm.reason)
