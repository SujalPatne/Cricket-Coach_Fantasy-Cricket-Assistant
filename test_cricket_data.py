"""
Test script for cricket data sources
"""

import logging
import json
from typing import Dict, List, Any
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import data sources
try:
    import cricsheet_parser as cricsheet
    CRICSHEET_AVAILABLE = True
    logger.info("Cricsheet parser available")
except ImportError:
    CRICSHEET_AVAILABLE = False
    logger.warning("Cricsheet parser not available")

try:
    import cricbuzz_client as cricbuzz
    CRICBUZZ_AVAILABLE = True
    logger.info("Cricbuzz client available")
except ImportError:
    CRICBUZZ_AVAILABLE = False
    logger.warning("Cricbuzz client not available")

# Import data adapter
import cricket_data_adapter as adapter

def pretty_print(data: Any) -> None:
    """Pretty print data"""
    print(json.dumps(data, indent=2))

def test_cricsheet():
    """Test Cricsheet data source"""
    if not CRICSHEET_AVAILABLE:
        logger.error("Cricsheet parser not available, skipping test")
        return

    print("\n=== Testing Cricsheet Data Source ===\n")

    # Test getting available match types
    print("Available match types:")
    match_types = cricsheet.get_available_match_types()
    print(match_types)

    # Test getting recent matches
    print("\nRecent matches:")
    recent_matches = cricsheet.get_recent_matches(days=30, limit=3)
    pretty_print(recent_matches)

    # Test getting player stats
    print("\nPlayer stats for Virat Kohli:")
    player_stats = cricsheet.get_player_stats("Virat Kohli")
    pretty_print(player_stats)

def test_cricbuzz():
    """Test Cricbuzz data source"""
    if not CRICBUZZ_AVAILABLE:
        logger.error("Cricbuzz client not available, skipping test")
        return

    from config import CRICBUZZ_API_KEY
    if not CRICBUZZ_API_KEY:
        logger.error("Cricbuzz API key not set, skipping test")
        print("\n=== Cricbuzz API Key Not Set ===")
        print("Please set your RapidAPI key in the .env file:")
        print("CRICBUZZ_API_KEY=your_rapidapi_key_here")
        return

    print("\n=== Testing Cricbuzz Data Source ===\n")

    # Test getting live matches
    print("Live matches:")
    live_matches = cricbuzz.get_live_matches()
    pretty_print(live_matches[:2] if len(live_matches) > 2 else live_matches)

    # Test getting upcoming matches
    print("\nUpcoming matches:")
    upcoming_matches = cricbuzz.get_upcoming_matches()
    pretty_print(upcoming_matches[:2] if len(upcoming_matches) > 2 else upcoming_matches)

    # Test getting recent matches
    print("\nRecent matches:")
    recent_matches = cricbuzz.get_recent_matches()
    pretty_print(recent_matches[:2] if len(recent_matches) > 2 else recent_matches)

    # Test getting match score (if any live matches available)
    if live_matches:
        match_id = live_matches[0].get("matchId", "")
        if match_id:
            print(f"\nMatch score for match ID {match_id}:")
            match_score = cricbuzz.get_match_score(match_id)
            pretty_print(match_score)

    # Test searching for players
    print("\nSearch for player 'Virat Kohli':")
    players = cricbuzz.search_players("Virat Kohli")
    pretty_print(players)

    # Test getting player info (if any players found)
    if players:
        player_id = players[0].get("id", "")
        if player_id:
            print(f"\nPlayer info for player ID {player_id}:")
            player_info = cricbuzz.get_player_info(player_id)
            pretty_print(player_info)

def test_adapter():
    """Test cricket data adapter"""
    print("\n=== Testing Cricket Data Adapter ===\n")

    # Test getting live matches
    print("Live matches:")
    live_matches = adapter.get_live_cricket_matches()
    pretty_print(live_matches[:2] if len(live_matches) > 2 else live_matches)

    # Test getting upcoming matches
    print("\nUpcoming matches:")
    upcoming_matches = adapter.get_upcoming_matches()
    pretty_print(upcoming_matches[:2] if len(upcoming_matches) > 2 else upcoming_matches)

    # Test getting player stats
    print("\nPlayer stats for Virat Kohli:")
    player_stats = adapter.get_player_stats("Virat Kohli")
    pretty_print(player_stats)

    # Test getting player form
    print("\nPlayer form for Virat Kohli:")
    player_form = adapter.get_player_form("Virat Kohli")
    print(player_form)

    # Test getting recommended players
    print("\nRecommended batsmen:")
    recommended_batsmen = adapter.get_recommended_players(role="Batsman")
    pretty_print(recommended_batsmen[:2] if len(recommended_batsmen) > 2 else recommended_batsmen)

def main():
    """Main function"""
    # Create necessary directories
    os.makedirs("cricsheet_data", exist_ok=True)
    os.makedirs("cricsheet_data/cache", exist_ok=True)
    os.makedirs("cricbuzz_cache", exist_ok=True)

    # Uncomment tests as needed

    # Test Cricsheet (can be slow due to data downloads)
    # test_cricsheet()

    # Test Cricbuzz
    test_cricbuzz()

    # Test adapter (can be slow if it uses Cricsheet)
    # test_adapter()

if __name__ == "__main__":
    main()
