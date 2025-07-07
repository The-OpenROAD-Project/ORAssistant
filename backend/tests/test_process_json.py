import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.tools.process_json import parse_json, generate_knowledge_base


class TestProcessJSON:
    """Test suite for process_json utility functions."""

    def test_parse_json_basic(self):
        """Test basic JSON parsing with user and assistant messages."""
        json_object = {
            "messages": [
                {"user": "What is OpenROAD?"},
                {"assistant": "OpenROAD is an open-source RTL-to-GDSII tool."},
                {"user": "How do I install it?"},
                {"assistant": "You can install OpenROAD using Docker or building from source."}
            ]
        }
        
        result = parse_json(json_object)
        
        assert "Infer knowledge from this conversation" in result
        assert "User1: What is OpenROAD?" in result
        assert "User2: OpenROAD is an open-source RTL-to-GDSII tool." in result
        assert "User1: How do I install it?" in result
        assert "User2: You can install OpenROAD using Docker or building from source." in result

    def test_parse_json_user_only(self):
        """Test JSON parsing with only user messages."""
        json_object = {
            "messages": [
                {"user": "First question"},
                {"user": "Second question"}
            ]
        }
        
        result = parse_json(json_object)
        
        assert "Infer knowledge from this conversation" in result
        assert "User1: First question" in result
        assert "User1: Second question" in result
        assert "User2:" not in result

    def test_parse_json_assistant_only(self):
        """Test JSON parsing with only assistant messages."""
        json_object = {
            "messages": [
                {"assistant": "First response"},
                {"assistant": "Second response"}
            ]
        }
        
        result = parse_json(json_object)
        
        assert "Infer knowledge from this conversation" in result
        assert "User2: First response" in result
        assert "User2: Second response" in result
        assert "User1:" not in result

    def test_parse_json_empty_messages(self):
        """Test JSON parsing with empty messages list."""
        json_object = {"messages": []}
        
        result = parse_json(json_object)
        
        assert result == "Infer knowledge from this conversation and use it to answer the given question.\n\t"

    def test_parse_json_strips_whitespace(self):
        """Test that whitespace is stripped from messages."""
        json_object = {
            "messages": [
                {"user": "  Question with spaces  "},
                {"assistant": "\tAnswer with tabs\n"}
            ]
        }
        
        result = parse_json(json_object)
        
        assert "User1: Question with spaces" in result
        assert "User2: Answer with tabs" in result
        # Should not contain the extra whitespace
        assert "  Question with spaces  " not in result
        assert "\tAnswer with tabs\n" not in result

    def test_parse_json_mixed_message_types(self):
        """Test JSON parsing with various message types and some empty."""
        json_object = {
            "messages": [
                {"user": "Question 1"},
                {"other_key": "Should be ignored"},
                {"assistant": "Answer 1"},
                {"user": "Question 2"},
                {}  # Empty message
            ]
        }
        
        result = parse_json(json_object)
        
        assert "User1: Question 1" in result
        assert "User2: Answer 1" in result
        assert "User1: Question 2" in result
        assert "Should be ignored" not in result

    def test_generate_knowledge_base_single_file(self):
        """Test generating knowledge base from single file."""
        json_data = [
            {"messages": [{"user": "Question 1"}, {"assistant": "Answer 1"}]},
            {"messages": [{"user": "Question 2"}, {"assistant": "Answer 2"}]}
        ]
        
        # Create temporary file with JSON lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for item in json_data:
                json.dump(item, f)
                f.write('\n')
            temp_file = f.name
        
        try:
            result = generate_knowledge_base([temp_file])
            
            assert len(result) == 2
            assert all(doc.metadata["source"] == temp_file for doc in result)
            assert "User1: Question 1" in result[0].page_content
            assert "User2: Answer 1" in result[0].page_content
            assert "User1: Question 2" in result[1].page_content
            assert "User2: Answer 2" in result[1].page_content
        finally:
            Path(temp_file).unlink()

    def test_generate_knowledge_base_multiple_files(self):
        """Test generating knowledge base from multiple files."""
        json_data1 = [{"messages": [{"user": "File 1 question"}, {"assistant": "File 1 answer"}]}]
        json_data2 = [{"messages": [{"user": "File 2 question"}, {"assistant": "File 2 answer"}]}]
        
        temp_files = []
        try:
            # Create first file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for item in json_data1:
                    json.dump(item, f)
                    f.write('\n')
                temp_files.append(f.name)
            
            # Create second file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for item in json_data2:
                    json.dump(item, f)
                    f.write('\n')
                temp_files.append(f.name)
            
            result = generate_knowledge_base(temp_files)
            
            assert len(result) == 2
            sources = [doc.metadata["source"] for doc in result]
            assert temp_files[0] in sources
            assert temp_files[1] in sources
            
            # Check content
            contents = [doc.page_content for doc in result]
            assert any("File 1 question" in content for content in contents)
            assert any("File 2 question" in content for content in contents)
            
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()

    @patch('src.tools.process_json.logging')
    def test_generate_knowledge_base_file_not_found(self, mock_logging):
        """Test handling of file not found error."""
        result = generate_knowledge_base(["/nonexistent/file.jsonl"])
        
        assert result == []
        mock_logging.error.assert_called_once()
        assert "/nonexistent/file.jsonl not found" in str(mock_logging.error.call_args)

    @patch('src.tools.process_json.logging')
    def test_generate_knowledge_base_invalid_json(self, mock_logging):
        """Test handling of invalid JSON lines."""
        # Create file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"messages": [{"user": "valid question"}]}\n')
            f.write('invalid json line\n')
            f.write('{"messages": [{"user": "another valid question"}]}\n')
            temp_file = f.name
        
        try:
            result = generate_knowledge_base([temp_file])
            
            # Should have processed only the valid JSON lines
            # The function continues processing after invalid JSON
            mock_logging.error.assert_called()
            # Should have some valid documents processed
            assert len(result) >= 1
            
        finally:
            Path(temp_file).unlink()

    def test_generate_knowledge_base_empty_file(self):
        """Test handling of empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_file = f.name  # Empty file
        
        try:
            result = generate_knowledge_base([temp_file])
            assert result == []
        finally:
            Path(temp_file).unlink()

    @pytest.mark.unit
    def test_parse_json_with_complex_messages(self):
        """Test parsing JSON with complex message content."""
        json_object = {
            "messages": [
                {"user": "How do I configure OpenROAD for a 14nm process?"},
                {"assistant": "To configure OpenROAD for 14nm:\n1. Set PDK path\n2. Configure design rules\n3. Set library files"},
                {"user": "What about timing constraints?"},
                {"assistant": "Use SDC files:\n- create_clock\n- set_input_delay\n- set_output_delay"}
            ]
        }
        
        result = parse_json(json_object)
        
        assert "configure OpenROAD for a 14nm process" in result
        assert "Set PDK path" in result
        assert "timing constraints" in result
        assert "create_clock" in result

    @pytest.mark.integration
    def test_generate_knowledge_base_realistic_data(self):
        """Test with realistic conversation data."""
        realistic_data = [
            {
                "messages": [
                    {"user": "I'm getting a DRC violation in my OpenROAD flow. How can I debug this?"},
                    {"assistant": "DRC violations can be debugged by:\n1. Checking the DRC report\n2. Using the GUI to visualize violations\n3. Reviewing design rules"}
                ]
            },
            {
                "messages": [
                    {"user": "What's the difference between global placement and detailed placement?"},
                    {"assistant": "Global placement determines approximate locations, while detailed placement refines positions for legality and optimization."}
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for item in realistic_data:
                json.dump(item, f)
                f.write('\n')
            temp_file = f.name
        
        try:
            result = generate_knowledge_base([temp_file])
            
            assert len(result) == 2
            contents = " ".join(doc.page_content for doc in result)
            assert "DRC violation" in contents
            assert "global placement" in contents
            assert "detailed placement" in contents
            assert "Infer knowledge from this conversation" in result[0].page_content
            
        finally:
            Path(temp_file).unlink()

    @pytest.mark.unit
    def test_parse_json_preserves_conversation_structure(self):
        """Test that conversation structure is preserved in parsing."""
        json_object = {
            "messages": [
                {"user": "First question"},
                {"assistant": "First answer"},
                {"user": "Follow-up question"},
                {"assistant": "Follow-up answer"}
            ]
        }
        
        result = parse_json(json_object)
        
        # Check that the conversation flows properly
        lines = result.split('\n')
        user_lines = [line for line in lines if line.strip().startswith('User1:')]
        assistant_lines = [line for line in lines if line.strip().startswith('User2:')]
        
        assert len(user_lines) == 2
        assert len(assistant_lines) == 2
        assert "First question" in user_lines[0]
        assert "Follow-up question" in user_lines[1]
        assert "First answer" in assistant_lines[0]
        assert "Follow-up answer" in assistant_lines[1]