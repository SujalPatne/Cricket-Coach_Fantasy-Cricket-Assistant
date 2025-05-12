"""
Simple test script for the Fantasy Cricket Chatbot with integrated data sources
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
    
    # Test player stats query
    test_query("Show me stats for Virat Kohli")

if __name__ == "__main__":
    main()
