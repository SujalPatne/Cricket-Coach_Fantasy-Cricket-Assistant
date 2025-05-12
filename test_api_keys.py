"""
Test script to verify API keys are working correctly
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def test_gemini_api():
    """Test if Gemini API key is working"""
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not found in environment variables")
        return False
    
    try:
        import google.generativeai as genai
        
        # Configure the API
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Create a GenerationConfig object
        generation_config = genai.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=1024,
        )
        
        # Initialize the Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
        
        # Test with a simple query
        response = model.generate_content("Hello, who are you?")
        
        logger.info("Gemini API test successful")
        logger.info(f"Response: {response.text[:100]}...")
        return True
    
    except Exception as e:
        logger.error(f"Error testing Gemini API: {str(e)}")
        return False

def test_openai_api():
    """Test if OpenAI API key is working"""
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables")
        return False
    
    try:
        from openai import OpenAI
        
        # Initialize the client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Test with a simple query
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, who are you?"}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        logger.info("OpenAI API test successful")
        logger.info(f"Response: {response.choices[0].message.content[:100]}...")
        return True
    
    except Exception as e:
        logger.error(f"Error testing OpenAI API: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing API keys...")
    
    # Test Gemini API
    logger.info("Testing Gemini API...")
    gemini_success = test_gemini_api()
    
    # Test OpenAI API
    logger.info("Testing OpenAI API...")
    openai_success = test_openai_api()
    
    # Summary
    logger.info("API Test Results:")
    logger.info(f"Gemini API: {'SUCCESS' if gemini_success else 'FAILED'}")
    logger.info(f"OpenAI API: {'SUCCESS' if openai_success else 'FAILED'}")
    
    if not gemini_success and not openai_success:
        logger.error("Both API tests failed. Please check your API keys.")
        sys.exit(1)
    
    logger.info("API test completed.")
