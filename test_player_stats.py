"""
Test script to verify player statistics functionality
"""

import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the necessary functions
from cricket_data_adapter import get_player_stats
from gemini_assistant import extract_player_name, get_formatted_player_stats

def test_player_extraction():
    """Test the player name extraction function"""
    test_queries = [
        "What are Virat Kohli's batting statistics?",
        "Show me stats for Rohit Sharma",
        "Tell me about Jasprit Bumrah's bowling performance",
        "MS Dhoni's career statistics",
        "Kane Williamson form",
        "How is Babar Azam performing?",
        "Ben Stokes recent matches",
        "Steve Smith batting average"
    ]
    
    print("\n=== Testing Player Name Extraction ===")
    for query in test_queries:
        player_name = extract_player_name(query)
        print(f"Query: '{query}' -> Extracted: '{player_name}'")
    
    print("\n")

def test_player_stats_retrieval():
    """Test the player statistics retrieval function"""
    test_players = [
        "Virat Kohli",
        "Rohit Sharma",
        "Jasprit Bumrah",
        "MS Dhoni",
        "Kane Williamson"
    ]
    
    print("\n=== Testing Player Stats Retrieval ===")
    for player in test_players:
        print(f"\nRetrieving stats for {player}...")
        
        # Check if we have cached data
        normalized_name = player.lower().replace(" ", "_")
        cache_file = os.path.join("cricsheet_data/cache", f"player_{normalized_name}.json")
        
        if os.path.exists(cache_file):
            cache_age = datetime.fromtimestamp(os.path.getmtime(cache_file))
            print(f"Found cached data from {cache_age}")
        
        # Get stats (force refresh for first player to test download)
        force_refresh = (player == test_players[0])
        stats = get_player_stats(player, force_refresh=force_refresh)
        
        # Print key stats
        print(f"  Team: {stats.get('team', 'Unknown')}")
        print(f"  Role: {stats.get('role', 'Unknown')}")
        print(f"  Source: {stats.get('source', 'Unknown')}")
        
        if 'batting_avg' in stats:
            print(f"  Batting Average: {stats.get('batting_avg', 'N/A')}")
        
        if 'recent_form' in stats:
            print(f"  Recent Form: {stats.get('recent_form', [])}")
        
        if 'last_updated' in stats:
            print(f"  Last Updated: {stats.get('last_updated', 'Unknown')}")
    
    print("\n")

def test_formatted_output():
    """Test the formatted output function"""
    test_players = [
        "Virat Kohli",
        "Jasprit Bumrah"
    ]
    
    print("\n=== Testing Formatted Output ===")
    for player in test_players:
        print(f"\nFormatted stats for {player}:")
        formatted_stats = get_formatted_player_stats(player)
        print(formatted_stats)
    
    print("\n")

def main():
    """Main test function"""
    print("=== Cricket Player Stats Test ===")
    
    # Ensure cache directory exists
    os.makedirs("cricsheet_data/cache", exist_ok=True)
    
    # Run tests
    test_player_extraction()
    test_player_stats_retrieval()
    test_formatted_output()
    
    print("=== Tests Complete ===")

if __name__ == "__main__":
    main()
