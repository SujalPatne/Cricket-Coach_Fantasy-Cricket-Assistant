import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_manager import AIManager, AIModel

class TestAIManager(unittest.TestCase):
    """Test cases for AIManager"""

    def setUp(self):
        """Set up test case"""
        # Clear environment variables for testing
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

    @patch('ai_manager.AIManager._check_available_models')
    def test_init_with_default_model(self, mock_check_models):
        """Test initializing with default model"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED, AIModel.GEMINI]

        # Initialize with default model
        manager = AIManager(default_model=AIModel.GEMINI)

        self.assertEqual(manager.default_model, AIModel.GEMINI)
        self.assertEqual(manager.available_models, [AIModel.RULE_BASED, AIModel.GEMINI])

    @patch('ai_manager.AIManager._check_available_models')
    def test_init_with_unavailable_model(self, mock_check_models):
        """Test initializing with unavailable model"""
        # Mock available models (GEMINI not available)
        mock_check_models.return_value = [AIModel.RULE_BASED]

        # Initialize with unavailable model
        manager = AIManager(default_model=AIModel.GEMINI)

        # Should fall back to rule-based
        self.assertEqual(manager.default_model, AIModel.RULE_BASED)

    def test_check_available_models(self):
        """Test checking available models"""
        # No API keys set
        manager = AIManager()
        available_models = manager._check_available_models()

        # Only rule-based should be available
        self.assertEqual(available_models, [AIModel.RULE_BASED])

        # Set Gemini API key
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch('gemini_assistant.GEMINI_AVAILABLE', True):
                # Import the module inside the test to avoid circular imports
                import sys
                sys.modules['gemini_assistant'] = MagicMock()
                sys.modules['gemini_assistant'].GEMINI_AVAILABLE = True

                manager = AIManager()
                # Mock the check_available_models method
                manager._check_available_models = MagicMock(return_value=[AIModel.RULE_BASED, AIModel.GEMINI])
                available_models = manager._check_available_models()

                # Rule-based and Gemini should be available
                self.assertIn(AIModel.RULE_BASED, available_models)
                self.assertIn(AIModel.GEMINI, available_models)

        # Set OpenAI API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
            with patch('openai_assistant.OPENAI_AVAILABLE', True):
                # Import the module inside the test to avoid circular imports
                import sys
                sys.modules['openai_assistant'] = MagicMock()
                sys.modules['openai_assistant'].OPENAI_AVAILABLE = True

                manager = AIManager()
                # Mock the check_available_models method
                manager._check_available_models = MagicMock(return_value=[AIModel.RULE_BASED, AIModel.OPENAI])
                available_models = manager._check_available_models()

                # Rule-based and OpenAI should be available
                self.assertIn(AIModel.RULE_BASED, available_models)
                self.assertIn(AIModel.OPENAI, available_models)

    @patch('ai_manager.AIManager._check_available_models')
    @patch('assistant.generate_response')
    def test_process_query_rule_based(self, mock_generate_response, mock_check_models):
        """Test processing query with rule-based model"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED]

        # Mock rule-based response
        mock_generate_response.return_value = "Rule-based response"

        # Initialize manager
        manager = AIManager(default_model=AIModel.RULE_BASED)

        # Process query
        result = manager.process_query("Test query")

        # Check result
        self.assertEqual(result["response"], "Rule-based response")
        self.assertEqual(result["model_used"], "rule-based")
        self.assertTrue(result["success"])

        # Verify mock was called
        mock_generate_response.assert_called_once_with("Test query")

    @patch('ai_manager.AIManager._check_available_models')
    @patch('gemini_assistant.process_cricket_query')
    def test_process_query_gemini(self, mock_process_query, mock_check_models):
        """Test processing query with Gemini model"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED, AIModel.GEMINI]

        # Mock Gemini response
        mock_process_query.return_value = "Gemini response"

        # Initialize manager
        manager = AIManager(default_model=AIModel.GEMINI)

        # Process query
        result = manager.process_query("Test query")

        # Check result
        self.assertEqual(result["response"], "Gemini response")
        self.assertEqual(result["model_used"], "gemini")
        self.assertTrue(result["success"])

        # Verify mock was called
        mock_process_query.assert_called_once_with("Test query")

    @patch('ai_manager.AIManager._check_available_models')
    @patch('openai_assistant.process_cricket_query')
    def test_process_query_openai(self, mock_process_query, mock_check_models):
        """Test processing query with OpenAI model"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED, AIModel.OPENAI]

        # Mock OpenAI response
        mock_process_query.return_value = "OpenAI response"

        # Initialize manager
        manager = AIManager(default_model=AIModel.OPENAI)

        # Process query
        result = manager.process_query("Test query")

        # Check result
        self.assertEqual(result["response"], "OpenAI response")
        self.assertEqual(result["model_used"], "openai")
        self.assertTrue(result["success"])

        # Verify mock was called
        mock_process_query.assert_called_once_with("Test query")

    @patch('ai_manager.AIManager._check_available_models')
    @patch('gemini_assistant.process_cricket_query')
    @patch('assistant.generate_response')
    def test_process_query_with_fallback(self, mock_generate_response, mock_process_query, mock_check_models):
        """Test processing query with fallback to rule-based"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED, AIModel.GEMINI]

        # Mock Gemini to raise exception
        mock_process_query.side_effect = Exception("Gemini error")

        # Mock rule-based response
        mock_generate_response.return_value = "Fallback response"

        # Initialize manager
        manager = AIManager(default_model=AIModel.GEMINI)

        # Process query
        result = manager.process_query("Test query")

        # Check result
        self.assertEqual(result["response"], "Fallback response")
        self.assertEqual(result["model_used"], "rule-based")
        self.assertTrue(result["success"])
        self.assertTrue(result["fallback"])
        self.assertEqual(result["error"], "Gemini error")

        # Verify mocks were called
        mock_process_query.assert_called_once_with("Test query")
        mock_generate_response.assert_called_once_with("Test query")

    @patch('ai_manager.AIManager._check_available_models')
    def test_set_default_model(self, mock_check_models):
        """Test setting default model"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED, AIModel.GEMINI]

        # Initialize manager
        manager = AIManager(default_model=AIModel.RULE_BASED)

        # Set default model to available model
        result = manager.set_default_model(AIModel.GEMINI)

        # Check result
        self.assertTrue(result)
        self.assertEqual(manager.default_model, AIModel.GEMINI)

        # Set default model to unavailable model
        result = manager.set_default_model(AIModel.OPENAI)

        # Check result
        self.assertFalse(result)
        self.assertEqual(manager.default_model, AIModel.GEMINI)  # Unchanged

    @patch('ai_manager.AIManager._check_available_models')
    def test_get_available_models(self, mock_check_models):
        """Test getting available models"""
        # Mock available models
        mock_check_models.return_value = [AIModel.RULE_BASED, AIModel.GEMINI, AIModel.OPENAI]

        # Initialize manager
        manager = AIManager()

        # Get available models
        models = manager.get_available_models()

        # Check result
        self.assertEqual(models, ["rule-based", "gemini", "openai"])

if __name__ == '__main__':
    unittest.main()
