"""
Test script for the Fantasy Cricket Chatbot with integrated data sources
"""

import logging
from assistant import generate_response

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_query(query):
    """Test a query and print the response"""
    print(f"\n=== Query: '{query}' ===\n")
    response = generate_response(query)
    print(response)
    print("\n" + "="*50 + "\n")

def main():
    """Main function to test the chatbot"""
    # Test greeting
    test_query("Hello")
    
    # Test live matches query
    test_query("Show me live matches")
    
    # Test upcoming matches query
    test_query("What are the upcoming matches?")
    
    # Test recent matches query
    test_query("Show me recent match results")
    
    # Test player stats query
    test_query("Show me stats for Virat Kohli")
    
    # Test player form query
    test_query("How is Rohit Sharma playing?")
    
    # Test pitch report query
    test_query("What are the pitch conditions in Mumbai?")
    
    # Test captain picks query
    test_query("Who should I pick as captain?")
    
    # Test player comparison query
    test_query("Compare Rohit Sharma and Virat Kohli")
    
    # Test match details query (this will likely fail without a valid match ID)
    test_query("Show me match details for 12345")
    
    # Test recommendation query
    test_query("Recommend some batsmen for today's match")
    
    # Test fantasy rules query
    test_query("Explain fantasy cricket scoring")

if __name__ == "__main__":
    main()
