import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from config import GEMINI_API_KEY, OPENAI_API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIModel(Enum):
    """Enum for available AI models"""
    GEMINI = "gemini"
    OPENAI = "openai"
    RULE_BASED = "rule-based"

class AIManager:
    """Manager for AI model selection and query processing"""

    def __init__(self, default_model: AIModel = AIModel.GEMINI):
        """Initialize AI manager with default model"""
        self.default_model = default_model
        self.available_models = self._check_available_models()

        # If default model is not available, fall back to rule-based
        if self.default_model not in self.available_models:
            logger.warning(f"{self.default_model.value} not available, falling back to rule-based")
            self.default_model = AIModel.RULE_BASED

    def _check_available_models(self) -> List[AIModel]:
        """Check which AI models are available based on API keys"""
        available = [AIModel.RULE_BASED]  # Rule-based is always available

        # Check Gemini
        if GEMINI_API_KEY:
            try:
                # Import and test Gemini
                from gemini_assistant import GEMINI_AVAILABLE
                if GEMINI_AVAILABLE:
                    available.append(AIModel.GEMINI)
                    logger.info("Gemini AI is available")
                else:
                    logger.warning("Gemini API key found but initialization failed")
            except ImportError:
                logger.warning("Gemini module not found")
        else:
            logger.warning("No Gemini API key found in config")

        # Check OpenAI
        if OPENAI_API_KEY:
            try:
                # Import and test OpenAI
                from openai_assistant import OPENAI_AVAILABLE
                if OPENAI_AVAILABLE:
                    available.append(AIModel.OPENAI)
                    logger.info("OpenAI is available")
                else:
                    logger.warning("OpenAI API key found but initialization failed")
            except ImportError:
                logger.warning("OpenAI module not found")
        else:
            logger.warning("No OpenAI API key found in config")

        return available

    def process_query(self, query: str, model: Optional[AIModel] = None) -> Dict[str, Any]:
        """
        Process a query using the specified AI model

        Parameters:
        - query: User's question or request
        - model: AI model to use (defaults to self.default_model)

        Returns:
        - Dictionary with response and metadata
        """
        # Use default model if none specified
        if model is None:
            model = self.default_model

        # If model is not available, fall back to rule-based
        if model not in self.available_models:
            logger.warning(f"{model.value} not available, falling back to rule-based")
            model = AIModel.RULE_BASED

        # Process query with selected model
        response = ""
        try:
            logger.info(f"Processing query with model: {model.value}")

            if model == AIModel.GEMINI:
                logger.info("Using Gemini model")
                from gemini_assistant import process_cricket_query
                response = process_cricket_query(query)
                logger.info("Gemini response generated successfully")
            elif model == AIModel.OPENAI:
                logger.info("Using OpenAI model")
                from openai_assistant import process_cricket_query
                response = process_cricket_query(query)
                logger.info("OpenAI response generated successfully")
            else:  # Rule-based
                logger.info("Using rule-based model")
                from assistant import generate_response
                response = generate_response(query)
                logger.info("Rule-based response generated successfully")

            result = {
                "response": response,
                "model_used": model.value,
                "success": True
            }
            logger.info(f"Query processed successfully with {model.value}")
            return result

        except Exception as e:
            logger.error(f"Error processing query with {model.value}: {str(e)}")

            # Try fallback to rule-based if not already using it
            if model != AIModel.RULE_BASED:
                try:
                    from assistant import generate_response
                    response = generate_response(query)
                    return {
                        "response": response,
                        "model_used": AIModel.RULE_BASED.value,
                        "success": True,
                        "fallback": True,
                        "error": str(e)
                    }
                except Exception as fallback_error:
                    logger.error(f"Error with fallback response: {str(fallback_error)}")

            # If all else fails, return error message
            return {
                "response": f"I'm having trouble processing your request. Please try again later. Error: {str(e)}",
                "model_used": model.value,
                "success": False,
                "error": str(e)
            }

    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return [model.value for model in self.available_models]

    def set_default_model(self, model: AIModel) -> bool:
        """
        Set the default AI model

        Parameters:
        - model: AI model to set as default

        Returns:
        - True if successful, False if model not available
        """
        if model in self.available_models:
            self.default_model = model
            return True
        return False
