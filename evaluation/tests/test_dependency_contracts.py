"""Regression tests for external APIs used by the evaluation package."""

import unittest
from unittest.mock import patch

from deepeval import evaluate

from auto_evaluation.src.models.gemini import GoogleGeminiLangChain


class DependencyContractsTest(unittest.TestCase):
    """Keep the dependency APIs that the evaluation code expects."""

    def test_deepeval_evaluate_is_callable(self) -> None:
        self.assertTrue(callable(evaluate))

    @patch("auto_evaluation.src.models.gemini.genai.Client")
    def test_gemini_model_keeps_its_name(self, _client: object) -> None:
        model = GoogleGeminiLangChain(model_name="gemini-test")

        self.assertEqual(model.get_model_name(), "gemini-test")


if __name__ == "__main__":
    unittest.main()
