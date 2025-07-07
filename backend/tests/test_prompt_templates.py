from src.prompts.prompt_templates import suggested_questions_prompt_template


class TestPromptTemplates:
    """Test suite for prompt template constants."""

    def test_suggested_questions_prompt_template_exists(self):
        """Test that suggested questions prompt template is defined."""
        assert suggested_questions_prompt_template is not None
        assert isinstance(suggested_questions_prompt_template, str)
        assert len(suggested_questions_prompt_template) > 0

    def test_suggested_questions_prompt_template_has_placeholders(self):
        """Test that prompt template contains expected placeholders."""
        template = suggested_questions_prompt_template

        # Should contain placeholders for formatting
        assert "{latest_question}" in template
        assert "{assistant_answer}" in template

    def test_suggested_questions_prompt_template_formatting(self):
        """Test that prompt template can be formatted correctly."""
        template = suggested_questions_prompt_template

        formatted = template.format(
            latest_question="What is OpenROAD?",
            assistant_answer="OpenROAD is an open-source tool for ASIC design.",
        )

        # Should contain the formatted values
        assert "What is OpenROAD?" in formatted
        assert "OpenROAD is an open-source tool for ASIC design." in formatted

        # Should not contain unformatted placeholders
        assert "{latest_question}" not in formatted
        assert "{assistant_answer}" not in formatted

    def test_suggested_questions_prompt_template_content(self):
        """Test that prompt template contains expected content."""
        template = suggested_questions_prompt_template

        # Should contain instructions about generating questions
        assert "question" in template.lower()
        assert "suggest" in template.lower() or "generate" in template.lower()

    def test_suggested_questions_prompt_template_is_string(self):
        """Test that prompt template is properly typed as string."""
        assert isinstance(suggested_questions_prompt_template, str)
        assert suggested_questions_prompt_template != ""
        assert suggested_questions_prompt_template is not None
