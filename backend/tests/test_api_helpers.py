import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from src.api.models.response_model import SuggestedQuestionInput


class TestApiHelpers:
    """Test suite for API helper functions."""

    @patch("src.api.routers.helpers.client")
    @patch("src.api.routers.helpers.SuggestedQuestions.model_validate")
    async def test_get_suggested_questions_success(self, mock_validate, mock_client):
        """Test successful suggested questions generation."""
        from src.api.routers.helpers import get_suggested_questions

        # Mock the OpenAI client response
        mock_response = Mock()
        mock_parsed = Mock()
        mock_response.choices = [Mock(message=Mock(parsed=mock_parsed))]
        mock_client.beta.chat.completions.parse.return_value = mock_response

        # Mock validation
        mock_validate.return_value = mock_parsed

        # Create test input
        input_data = SuggestedQuestionInput(
            latest_question="How to use OpenROAD?",
            assistant_answer="OpenROAD is a tool for...",
        )

        result = await get_suggested_questions(input_data)

        assert result == mock_parsed
        mock_client.beta.chat.completions.parse.assert_called_once()

    @patch("src.api.routers.helpers.client")
    async def test_get_suggested_questions_client_error(self, mock_client):
        """Test suggested questions generation with client error."""
        from src.api.routers.helpers import get_suggested_questions

        # Mock client to raise an exception
        mock_client.beta.chat.completions.parse.side_effect = Exception("API Error")

        input_data = SuggestedQuestionInput(
            latest_question="Test question", assistant_answer="Test answer"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_suggested_questions(input_data)

        assert exc_info.value.status_code == 500
        assert "Failed to get suggested questions" in str(exc_info.value.detail)

    @patch("src.api.routers.helpers.client")
    @patch("src.api.routers.helpers.SuggestedQuestions.model_validate")
    async def test_get_suggested_questions_invalid_response(
        self, mock_validate, mock_client
    ):
        """Test suggested questions generation with invalid response."""
        from src.api.routers.helpers import get_suggested_questions

        # Mock the OpenAI client response with None parsed content
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(parsed=None))]
        mock_client.beta.chat.completions.parse.return_value = mock_response

        input_data = SuggestedQuestionInput(
            latest_question="Test question", assistant_answer="Test answer"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_suggested_questions(input_data)

        assert exc_info.value.status_code == 500

    def test_constants_defined(self):
        """Test that constants are properly defined."""
        from src.api.routers.helpers import model

        assert model == "gemini-2.0-flash"
        # GOOGLE_API_KEY should be set or raise error during module import

    def test_router_configuration(self):
        """Test that router is properly configured."""
        from src.api.routers.helpers import router

        assert router.prefix == "/helpers"
        assert "helpers" in router.tags
