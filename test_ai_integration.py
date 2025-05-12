"""
Test script for the Fantasy Cricket Chatbot AI integration
"""

import logging
from openai_assistant import enrich_query_with_context
from gemini_assistant import enrich_query_with_context as gemini_enrich_query_with_context

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_openai_context_enrichment(query):
    """Test OpenAI context enrichment"""
    print(f"\n=== OpenAI Context Enrichment for: '{query}' ===\n")
    context = enrich_query_with_context(query)
    print(context if context else "No context added")
    print("\n" + "="*50 + "\n")

def test_gemini_context_enrichment(query):
    """Test Gemini context enrichment"""
    print(f"\n=== Gemini Context Enrichment for: '{query}' ===\n")
    context = gemini_enrich_query_with_context(query)
    print(context if context else "No context added")
    print("\n" + "="*50 + "\n")

def main():
    """Main function to test the AI integration"""
    # Test greeting (should not add context)
    test_openai_context_enrichment("Hello")
    test_gemini_context_enrichment("Hello")
    
    # Test live matches query
    test_openai_context_enrichment("Show me live matches")
    test_gemini_context_enrichment("Show me live matches")

if __name__ == "__main__":
    main()
