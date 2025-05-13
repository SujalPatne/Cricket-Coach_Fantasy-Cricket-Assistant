"""
Cricket Data Adapter - Converts API data to application format

This module integrates multiple cricket data sources (CricAPI, Cricsheet, Cricbuzz)
and provides a unified interface for accessing cricket data.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import cricket_api_client as api
from cricket_data_reliable import PLAYER_DATA as FALLBACK_PLAYER_DATA
from cricket_data_reliable import MATCH_DATA as FALLBACK_MATCH_DATA
from cricket_data_reliable import LIVE_MATCH_DATA as FALLBACK_LIVE_MATCH_DATA
from config import (
    CRICKET_API_KEY,
    CRICSHEET_ENABLED,
    CRICBUZZ_ENABLED
)

# Import data sources if enabled
if CRICSHEET_ENABLED:
    import cricsheet_parser as cricsheet
    from cricsheet_parser import CRICSHEET_CACHE_DIR
else:
    # Define a fallback cache directory if Cricsheet is not enabled
    CRICSHEET_CACHE_DIR = os.path.join("cricsheet_data", "cache")
    # Ensure the directory exists
    os.makedirs(CRICSHEET_CACHE_DIR, exist_ok=True)

if CRICBUZZ_ENABLED:
    import cricbuzz_client as cricbuzz

# Set up logging
logger = logging.getLogger(__name__)

# Check if data sources are available
CRICKET_API_AVAILABLE = bool(CRICKET_API_KEY)

def normalize_player_name(player_name: str) -> str:
    """
    Normalize player name by handling common misspellings and variations

    Parameters:
    - player_name: Original player name

    Returns:
    - Normalized player name
    """
    # Handle empty or None input
    if not player_name:
        return ""

    # Remove any special format like "what are X - Statistics"
    import re
    special_format_match = re.search(r'what are (.*?) - statistics', player_name.lower())
    if special_format_match:
        player_name = special_format_match.group(1)
        logger.info(f"Extracted name from special format: {player_name}")

    # Common misspellings and variations with their canonical forms
    name_corrections = {
        "virat kolhi": "virat kohli",
        "kolhi": "kohli",
        "rohit": "rohit sharma",
        "dhoni": "ms dhoni",
        "ms": "ms dhoni",
        "williamson": "kane williamson",
        "kane": "kane williamson",
        "smith": "steve smith",
        "steve": "steve smith",
        "babar": "babar azam",
        "azam": "babar azam",
        "bumrah": "jasprit bumrah",
        "jasprit": "jasprit bumrah",
        "stokes": "ben stokes",
        "ben": "ben stokes",
        "rabada": "kagiso rabada",
        "kagiso": "kagiso rabada",
        "rashid": "rashid khan",
        "khan": "rashid khan"
    }

    # Canonical forms for full player names
    canonical_names = {
        "virat kohli": "Virat Kohli",
        "rohit sharma": "Rohit Sharma",
        "ms dhoni": "MS Dhoni",
        "kane williamson": "Kane Williamson",
        "steve smith": "Steve Smith",
        "babar azam": "Babar Azam",
        "jasprit bumrah": "Jasprit Bumrah",
        "ben stokes": "Ben Stokes",
        "kagiso rabada": "Kagiso Rabada",
        "rashid khan": "Rashid Khan"
    }

    # Clean up the name - remove extra spaces and make lowercase for comparison
    player_name = " ".join(player_name.split()).lower()

    # Check for exact matches in the canonical names dictionary
    if player_name in canonical_names:
        return canonical_names[player_name]

    # Check for exact matches in the corrections dictionary
    if player_name in name_corrections:
        corrected_name = name_corrections[player_name]
        # Check if the corrected name has a canonical form
        if corrected_name in canonical_names:
            logger.info(f"Corrected player name from '{player_name}' to canonical form '{canonical_names[corrected_name]}'")
            return canonical_names[corrected_name]
        logger.info(f"Corrected player name from '{player_name}' to '{corrected_name}'")
        return corrected_name

    # Check for partial matches
    for misspelling, correct in name_corrections.items():
        # If the misspelling is a substring of the player name and it's at least 4 characters long
        if misspelling in player_name and len(misspelling) >= 4:
            # Replace only the misspelled part
            corrected_name = player_name.replace(misspelling, correct)
            # Check if the corrected name has a canonical form
            if corrected_name in canonical_names:
                logger.info(f"Corrected player name from '{player_name}' to canonical form '{canonical_names[corrected_name]}'")
                return canonical_names[corrected_name]
            logger.info(f"Corrected player name from '{player_name}' to '{corrected_name}'")
            return corrected_name

    # If no corrections needed, capitalize each word and return
    return " ".join(word.capitalize() for word in player_name.split())

def get_player_stats(player_name: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get player statistics from available data sources

    Intelligently chooses between:
    1. Cricsheet (cached data for historical stats)
    2. Cricbuzz API (for real-time data)
    3. Fallback data (when neither is available)

    Parameters:
    - player_name: Name of the player
    - force_refresh: Force refresh of cached data

    Returns:
    - Player statistics in application format
    """
    # Normalize player name to handle misspellings
    corrected_name = normalize_player_name(player_name)

    logger.info(f"Getting stats for player: {corrected_name} (original: {player_name})")

    # Normalize player name for file operations
    normalized_name = corrected_name.lower().replace(" ", "_")
    cache_file = os.path.join(CRICSHEET_CACHE_DIR, f"player_{normalized_name}.json")

    # Check if we have cached data and it's not a forced refresh
    if os.path.exists(cache_file) and not force_refresh:
        try:
            # Check if cache is still valid (less than 24 hours old)
            mod_time = os.path.getmtime(cache_file)
            current_time = time.time()

            if (current_time - mod_time) < (24 * 60 * 60):  # 24 hours
                # Cache is still valid, load it
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    logger.info(f"Using cached data for {corrected_name}")

                    # If we have Cricbuzz API available, try to update real-time stats
                    if CRICKET_API_AVAILABLE:
                        try:
                            # Try to get current form from Cricbuzz
                            players = api.search_players(corrected_name)
                            if players:
                                player_id = players[0].get("id")
                                current_stats = api.get_player_stats(player_id)

                                if current_stats:
                                    # Update only the real-time fields
                                    logger.info(f"Updating real-time stats for {corrected_name} from Cricbuzz")

                                    # Convert to our format
                                    current_data = _convert_player_stats(current_stats, corrected_name)

                                    # Update only specific fields
                                    real_time_fields = ["recent_form", "recent_wickets", "current_form"]
                                    for field in real_time_fields:
                                        if field in current_data:
                                            cached_data[field] = current_data[field]

                                    # Update the cache with the new data
                                    with open(cache_file, 'w') as f:
                                        json.dump(cached_data, f, indent=2)
                        except Exception as e:
                            logger.warning(f"Could not update real-time stats: {str(e)}")

                    return cached_data
        except Exception as e:
            logger.error(f"Error loading cached player data: {str(e)}")

    # If we get here, we need to fetch fresh data
    logger.info(f"Fetching fresh data for {corrected_name}")

    # Strategy: Try Cricsheet first for historical data, then enhance with Cricbuzz for real-time data
    player_data = None

    # Step 1: Try Cricsheet for historical data
    if CRICSHEET_ENABLED:
        try:
            logger.info(f"Fetching historical data from Cricsheet for {corrected_name}")
            cricsheet_player = cricsheet.get_player_stats(corrected_name, force_refresh=force_refresh)

            if cricsheet_player and cricsheet_player.get("matches_played", 0) > 0:
                logger.info(f"Found player stats for {corrected_name} from Cricsheet")
                player_data = _convert_cricsheet_player_stats(cricsheet_player)
        except Exception as e:
            logger.error(f"Error getting player stats from Cricsheet: {str(e)}")

    # Step 2: Try to enhance with Cricbuzz data or use it as primary if Cricsheet failed
    if CRICKET_API_AVAILABLE:
        try:
            logger.info(f"Fetching real-time data from Cricbuzz for {corrected_name}")
            # Search for player by name
            players = api.search_players(corrected_name)

            if players:
                # Get the first matching player
                player_id = players[0].get("id")

                # Get detailed player stats
                cricbuzz_stats = api.get_player_stats(player_id)

                if cricbuzz_stats:
                    logger.info(f"Found player stats for {corrected_name} from Cricbuzz")
                    cricbuzz_data = _convert_player_stats(cricbuzz_stats, corrected_name)

                    if player_data:
                        # Enhance Cricsheet data with Cricbuzz real-time data
                        logger.info(f"Enhancing Cricsheet data with Cricbuzz data for {corrected_name}")

                        # Update real-time fields
                        real_time_fields = ["recent_form", "recent_wickets", "current_form"]
                        for field in real_time_fields:
                            if field in cricbuzz_data:
                                player_data[field] = cricbuzz_data[field]
                    else:
                        # Use Cricbuzz as primary data source
                        logger.info(f"Using Cricbuzz as primary data source for {corrected_name}")
                        player_data = cricbuzz_data
        except Exception as e:
            logger.error(f"Error getting player stats from Cricbuzz: {str(e)}")

    # Step 3: If both failed, use fallback data
    if not player_data:
        logger.warning(f"No stats found for player: {corrected_name}, using fallback data")
        player_data = _get_fallback_player_stats(corrected_name)

    # Save to cache
    if player_data:
        try:
            # Ensure cache directory exists
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

            # Add timestamp
            player_data["last_updated"] = datetime.now().isoformat()

            # Make sure the name in the data is the corrected one
            player_data["name"] = corrected_name

            # Add original name as a reference
            if player_name != corrected_name:
                player_data["original_query"] = player_name

            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(player_data, f, indent=2)
            logger.info(f"Cached player data for {corrected_name}")
        except Exception as e:
            logger.error(f"Error caching player data: {str(e)}")

    return player_data

def _convert_player_stats(api_stats: Dict[str, Any], player_name: str) -> Dict[str, Any]:
    """Convert API player stats to application format"""
    # Extract basic info
    name = api_stats.get("name", player_name)
    country = api_stats.get("country", "Unknown")

    # Determine player role
    role = "Unknown"
    if api_stats.get("isKeeper"):
        role = "Wicketkeeper"
    elif api_stats.get("isBowler") and api_stats.get("isBatsman"):
        role = "All-rounder"
    elif api_stats.get("isBowler"):
        role = "Bowler"
    elif api_stats.get("isBatsman"):
        role = "Batsman"

    # Extract batting stats
    batting_stats = api_stats.get("battingStats", {})
    batting_avg = float(batting_stats.get("avg", 0)) if batting_stats.get("avg") else 0
    strike_rate = float(batting_stats.get("strikeRate", 0)) if batting_stats.get("strikeRate") else 0
    matches_played = int(batting_stats.get("matches", 0)) if batting_stats.get("matches") else 0

    # Extract bowling stats
    bowling_stats = api_stats.get("bowlingStats", {})
    bowling_avg = float(bowling_stats.get("avg", 0)) if bowling_stats.get("avg") else 0
    economy = float(bowling_stats.get("economy", 0)) if bowling_stats.get("economy") else 0

    # Create recent form data (mock data as API doesn't provide this)
    recent_form = []
    if role in ["Batsman", "All-rounder", "Wicketkeeper"]:
        # Generate mock recent form based on batting average
        import random
        base = batting_avg * 0.8
        variance = batting_avg * 0.4
        recent_form = [max(0, int(base + random.uniform(-variance, variance))) for _ in range(5)]

    # Create recent wickets data (mock data as API doesn't provide this)
    recent_wickets = []
    if role in ["Bowler", "All-rounder"]:
        # Generate mock recent wickets
        import random
        base = 2 if bowling_avg > 0 and bowling_avg < 30 else 1
        recent_wickets = [max(0, int(base + random.uniform(-1, 1))) for _ in range(5)]

    # Calculate fantasy points average (mock calculation)
    fantasy_points_avg = 0
    if role == "Batsman":
        fantasy_points_avg = batting_avg * 1.5
    elif role == "Bowler":
        fantasy_points_avg = (30 / bowling_avg) * 30 if bowling_avg > 0 else 30
    elif role == "All-rounder":
        batting_points = batting_avg * 1.2
        bowling_points = (30 / bowling_avg) * 25 if bowling_avg > 0 else 25
        fantasy_points_avg = batting_points + bowling_points
    elif role == "Wicketkeeper":
        fantasy_points_avg = batting_avg * 1.6

    # Mock ownership and price data
    ownership = min(90, max(10, fantasy_points_avg * 0.8))
    price = min(11, max(5, fantasy_points_avg / 10))

    return {
        "name": name,
        "team": country,
        "role": role,
        "batting_avg": batting_avg,
        "bowling_avg": bowling_avg,
        "strike_rate": strike_rate,
        "economy": economy,
        "recent_form": recent_form,
        "recent_wickets": recent_wickets,
        "fantasy_points_avg": fantasy_points_avg,
        "ownership": ownership,
        "price": price,
        "matches_played": matches_played
    }

def _get_fallback_player_stats(player_name: str) -> Dict[str, Any]:
    """Get player statistics from fallback data"""
    player_name_lower = player_name.lower()

    # Try to find an exact match first
    for player in FALLBACK_PLAYER_DATA:
        if player["name"].lower() == player_name_lower:
            return player

    # Try partial match if exact match not found
    for player in FALLBACK_PLAYER_DATA:
        if player_name_lower in player["name"].lower():
            return player

    # Try fuzzy matching - check if any part of the player name matches
    player_parts = player_name_lower.split()
    for player in FALLBACK_PLAYER_DATA:
        player_name_parts = player["name"].lower().split()
        # Check if any part of the name matches
        for part in player_parts:
            if part in player_name_parts and len(part) >= 4:  # Only consider parts with at least 4 characters
                logger.info(f"Fuzzy match found for {player_name}: {player['name']}")
                return player

    # Try to match common misspellings
    common_misspellings = {
        "kohli": "virat kohli",
        "kolhi": "virat kohli",
        "sharma": "rohit sharma",
        "dhoni": "ms dhoni",
        "williamson": "kane williamson",
        "smith": "steve smith",
        "azam": "babar azam",
        "bumrah": "jasprit bumrah",
        "stokes": "ben stokes",
        "rabada": "kagiso rabada",
        "khan": "rashid khan"
    }

    # Check if any part of the player name is a known misspelling
    for part in player_parts:
        if part in common_misspellings:
            correct_name = common_misspellings[part]
            logger.info(f"Misspelling match found for {player_name}: {correct_name}")
            # Look for the correct name in the fallback data
            for player in FALLBACK_PLAYER_DATA:
                if player["name"].lower() == correct_name:
                    return player

    # Return default data if player not found
    logger.warning(f"Player not found in fallback data: {player_name}")
    return {
        "name": player_name,
        "team": "Unknown",
        "role": "Unknown",
        "batting_avg": 0,
        "strike_rate": 0,
        "recent_form": [],
        "fantasy_points_avg": 0,
        "ownership": 0,
        "price": 0,
        "matches_played": 0
    }

def get_live_cricket_matches() -> List[Dict[str, Any]]:
    """
    Get live cricket matches from available data sources

    Priority order:
    1. Cricbuzz (most real-time)
    2. CricAPI
    3. Fallback data
    """
    matches = []

    # Try Cricbuzz first (most real-time)
    if CRICBUZZ_ENABLED:
        try:
            cricbuzz_matches = cricbuzz.get_live_matches()
            if cricbuzz_matches:
                logger.info(f"Found {len(cricbuzz_matches)} live matches from Cricbuzz")
                return [_convert_cricbuzz_match(match, is_live=True) for match in cricbuzz_matches]
        except Exception as e:
            logger.error(f"Error getting live matches from Cricbuzz: {str(e)}")

    # Try CricAPI next
    if CRICKET_API_AVAILABLE:
        try:
            api_matches = api.get_current_matches()
            if api_matches:
                logger.info(f"Found {len(api_matches)} live matches from CricAPI")
                return [_convert_match_data(match, is_live=True) for match in api_matches]
        except Exception as e:
            logger.error(f"Error getting live matches from CricAPI: {str(e)}")

    # If no matches found, use fallback data
    logger.warning("No live matches found from any source, using fallback data")
    return FALLBACK_LIVE_MATCH_DATA

def get_upcoming_matches() -> List[Dict[str, Any]]:
    """
    Get upcoming cricket matches from available data sources

    Priority order:
    1. Cricbuzz (most real-time)
    2. Cricsheet (most detailed)
    3. CricAPI
    4. Fallback data
    """
    # Try Cricbuzz first (most real-time)
    if CRICBUZZ_ENABLED:
        try:
            cricbuzz_matches = cricbuzz.get_upcoming_matches()
            if cricbuzz_matches:
                logger.info(f"Found {len(cricbuzz_matches)} upcoming matches from Cricbuzz")
                return [_convert_cricbuzz_match(match, is_live=False) for match in cricbuzz_matches]
        except Exception as e:
            logger.error(f"Error getting upcoming matches from Cricbuzz: {str(e)}")

    # Try Cricsheet next (most detailed)
    if CRICSHEET_ENABLED:
        try:
            # Get matches from the next 30 days
            cricsheet_matches = cricsheet.get_matches(date_from=datetime.now().strftime("%Y-%m-%d"))
            if cricsheet_matches:
                logger.info(f"Found {len(cricsheet_matches)} upcoming matches from Cricsheet")
                return [_convert_cricsheet_match(match) for match in cricsheet_matches]
        except Exception as e:
            logger.error(f"Error getting upcoming matches from Cricsheet: {str(e)}")

    # Try CricAPI next
    if CRICKET_API_AVAILABLE:
        try:
            api_matches = api.get_upcoming_matches()
            if api_matches:
                logger.info(f"Found {len(api_matches)} upcoming matches from CricAPI")
                return [_convert_match_data(match, is_live=False) for match in api_matches]
        except Exception as e:
            logger.error(f"Error getting upcoming matches from CricAPI: {str(e)}")

    # If no matches found, use fallback data
    logger.warning("No upcoming matches found from any source, using fallback data")
    return FALLBACK_MATCH_DATA

def _convert_match_data(api_match: Dict[str, Any], is_live: bool) -> Dict[str, Any]:
    """Convert API match data to application format"""
    # Extract teams
    teams = api_match.get("teams", [])
    team_names = [team.get("name", "Unknown") for team in teams]

    if len(team_names) < 2:
        team_names = api_match.get("name", "Unknown vs Unknown").split(" vs ")

    # Format teams string
    teams_str = " vs ".join(team_names[:2]) if len(team_names) >= 2 else "Unknown vs Unknown"

    # Extract venue
    venue = api_match.get("venue", "Unknown")

    # Extract date
    date_str = api_match.get("date", "")
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        date = date_obj.strftime("%d %b")
    except:
        date = date_str

    # Extract match type
    match_type = api_match.get("matchType", "Unknown")
    if match_type.lower() == "t20":
        match_type = "T20"
    elif match_type.lower() == "odi":
        match_type = "ODI"
    elif match_type.lower() == "test":
        match_type = "Test"

    # Extract status
    status = "Live" if is_live else "Upcoming"

    # Extract score if live match
    if is_live:
        score = api_match.get("score", [])
        score_str = ""

        if score and len(score) > 0:
            team1_score = score[0].get("r", 0)
            team1_wickets = score[0].get("w", 0)
            team1_overs = score[0].get("o", 0)

            score_str = f"{team_names[0]} {team1_score}/{team1_wickets} ({team1_overs} ov)"

            if len(score) > 1:
                team2_score = score[1].get("r", 0)
                team2_wickets = score[1].get("w", 0)
                team2_overs = score[1].get("o", 0)

                score_str += f", {team_names[1]} {team2_score}/{team2_wickets} ({team2_overs} ov)"

        status = score_str if score_str else "Live"

    # Create mock pitch conditions
    import random
    pitch_conditions = {
        "batting_friendly": random.randint(4, 8),
        "pace_friendly": random.randint(4, 8),
        "spin_friendly": random.randint(4, 8)
    }

    return {
        "teams": teams_str,
        "venue": venue,
        "date": date,
        "match_type": match_type,
        "status": status,
        "pitch_conditions": pitch_conditions
    }

def get_recent_matches() -> List[Dict[str, Any]]:
    """
    Get recent cricket matches from available data sources

    Priority order:
    1. Cricbuzz (most real-time)
    2. Cricsheet (most detailed)
    3. CricAPI
    4. Fallback data
    """
    # Try Cricbuzz first (most real-time)
    if CRICBUZZ_ENABLED:
        try:
            cricbuzz_matches = cricbuzz.get_recent_matches()
            if cricbuzz_matches:
                logger.info(f"Found {len(cricbuzz_matches)} recent matches from Cricbuzz")
                return [_convert_cricbuzz_match(match, is_live=False) for match in cricbuzz_matches]
        except Exception as e:
            logger.error(f"Error getting recent matches from Cricbuzz: {str(e)}")

    # Try Cricsheet next (most detailed)
    if CRICSHEET_ENABLED:
        try:
            # Get matches from the last 30 days
            from datetime import datetime, timedelta
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")

            cricsheet_matches = cricsheet.get_matches(date_from=date_from, date_to=date_to)
            if cricsheet_matches:
                logger.info(f"Found {len(cricsheet_matches)} recent matches from Cricsheet")
                return [_convert_cricsheet_match(match) for match in cricsheet_matches]
        except Exception as e:
            logger.error(f"Error getting recent matches from Cricsheet: {str(e)}")

    # Try CricAPI next
    if CRICKET_API_AVAILABLE:
        try:
            # CricAPI doesn't have a specific endpoint for recent matches
            # We'll use the upcoming matches endpoint and filter for matches that have already started
            api_matches = api.get_upcoming_matches()
            if api_matches:
                # Filter for matches that have already started
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                recent_matches = [match for match in api_matches if match.get("date", "") <= today]

                if recent_matches:
                    logger.info(f"Found {len(recent_matches)} recent matches from CricAPI")
                    return [_convert_match_data(match, is_live=False) for match in recent_matches]
        except Exception as e:
            logger.error(f"Error getting recent matches from CricAPI: {str(e)}")

    # If no matches found, use fallback data
    logger.warning("No recent matches found from any source, using fallback data")
    return FALLBACK_MATCH_DATA

def get_pitch_conditions(venue: str) -> Dict[str, Any]:
    """Get pitch conditions for a venue"""
    # This is mostly mock data as the API doesn't provide detailed pitch conditions
    import random

    # Check if we have any matches at this venue
    matches = get_upcoming_matches() + get_live_cricket_matches() + get_recent_matches()
    venue_matches = [m for m in matches if venue.lower() in m.get("venue", "").lower()]

    if venue_matches:
        # Use the pitch conditions from the first match at this venue
        return venue_matches[0].get("pitch_conditions", {})

    # Generate random pitch conditions if no matches found
    return {
        "batting_friendly": random.randint(4, 8),
        "pace_friendly": random.randint(4, 8),
        "spin_friendly": random.randint(4, 8)
    }

def _convert_cricbuzz_match(cricbuzz_match: Dict[str, Any], is_live: bool = False) -> Dict[str, Any]:
    """
    Convert Cricbuzz match data to application format

    Parameters:
    - cricbuzz_match: Match data from Cricbuzz API via RapidAPI
    - is_live: Whether this is a live match

    Returns:
    - Match data in application format
    """
    # Extract match info
    match_info = cricbuzz_match.get("matchInfo", cricbuzz_match)

    # Extract teams
    team1 = match_info.get("team1", {}).get("teamName", "Unknown")
    team2 = match_info.get("team2", {}).get("teamName", "Unknown")
    teams_str = f"{team1} vs {team2}"

    # Extract venue
    venue = match_info.get("venueInfo", {}).get("ground", "Unknown")
    city = match_info.get("venueInfo", {}).get("city", "")
    if city and city not in venue:
        venue = f"{venue}, {city}"

    # Extract date
    match_date = match_info.get("startDate", 0)
    date = "Unknown"
    if match_date:
        try:
            # Convert milliseconds timestamp to datetime
            date_obj = datetime.fromtimestamp(match_date / 1000)
            date = date_obj.strftime("%Y-%m-%d")
        except:
            pass

    # Extract match type
    match_format = match_info.get("matchFormat", "Unknown")
    match_type = match_format.upper()

    # Extract status
    status = match_info.get("status", "Upcoming")
    if is_live:
        status = "Live: " + status

    # Create mock pitch conditions based on venue
    import random
    pitch_conditions = {
        "batting_friendly": random.randint(4, 8),
        "pace_friendly": random.randint(4, 8),
        "spin_friendly": random.randint(4, 8)
    }

    return {
        "teams": teams_str,
        "venue": venue,
        "date": date,
        "match_type": match_type,
        "status": status,
        "pitch_conditions": pitch_conditions,
        "source": "Cricbuzz",
        "match_id": str(match_info.get("matchId", ""))
    }

def _convert_cricsheet_match(cricsheet_match: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Cricsheet match data to application format

    Parameters:
    - cricsheet_match: Match data from Cricsheet

    Returns:
    - Match data in application format
    """
    # Extract teams
    teams = cricsheet_match.get("teams", [])
    teams_str = " vs ".join(teams) if teams else "Unknown vs Unknown"

    # Extract venue
    venue = cricsheet_match.get("venue", "Unknown")
    city = cricsheet_match.get("city", "")
    if city and city not in venue:
        venue = f"{venue}, {city}"

    # Extract date
    date = cricsheet_match.get("date", "Unknown")

    # Extract match type
    match_type = cricsheet_match.get("match_type", "Unknown").upper()

    # Create mock pitch conditions based on venue
    import random
    pitch_conditions = {
        "batting_friendly": random.randint(4, 8),
        "pace_friendly": random.randint(4, 8),
        "spin_friendly": random.randint(4, 8)
    }

    return {
        "teams": teams_str,
        "venue": venue,
        "date": date,
        "match_type": match_type,
        "status": "Upcoming",
        "pitch_conditions": pitch_conditions,
        "source": "Cricsheet",
        "match_id": cricsheet_match.get("id", "")
    }

def get_player_form(player_name: str) -> str:
    """
    Get the current form of a player based on recent performances

    Parameters:
    - player_name: Name of the player

    Returns:
    - Form rating (excellent, good, average, poor, unknown)
    """
    # Try to get player stats from Cricsheet first (most detailed)
    if CRICSHEET_ENABLED:
        try:
            cricsheet_player = cricsheet.get_player_stats(player_name)
            if cricsheet_player and cricsheet_player.get("recent_performances"):
                # Analyze recent performances
                return _analyze_player_form(cricsheet_player)
        except Exception as e:
            logger.error(f"Error getting player form from Cricsheet: {str(e)}")

    # Fall back to regular player stats
    player = get_player_stats(player_name)

    if not player or 'recent_form' not in player or not player['recent_form']:
        return "unknown"

    # For batsmen and all-rounders, check recent_form
    if player['role'] in ['Batsman', 'All-rounder', 'Wicketkeeper'] and 'recent_form' in player:
        recent_scores = player['recent_form']
        avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0

        if avg_score > 50:
            return "excellent"
        elif avg_score > 35:
            return "good"
        elif avg_score > 20:
            return "average"
        else:
            return "poor"

    # For bowlers and all-rounders, check recent_wickets
    if player['role'] in ['Bowler', 'All-rounder'] and 'recent_wickets' in player:
        recent_wickets = player['recent_wickets']
        avg_wickets = sum(recent_wickets) / len(recent_wickets) if recent_wickets else 0

        if avg_wickets > 2.5:
            return "excellent"
        elif avg_wickets > 1.5:
            return "good"
        elif avg_wickets > 1:
            return "average"
        else:
            return "poor"

    return "unknown"

def _convert_cricsheet_player_stats(cricsheet_player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Cricsheet player stats to application format

    Parameters:
    - cricsheet_player: Player data from Cricsheet

    Returns:
    - Player statistics in application format
    """
    # Extract basic info
    name = cricsheet_player.get("name", "Unknown")
    matches_played = cricsheet_player.get("matches_played", 0)

    # Determine player role based on stats
    role = "Unknown"
    if "wickets" in cricsheet_player and cricsheet_player.get("wickets", 0) > 0:
        if "runs" in cricsheet_player and cricsheet_player.get("runs", 0) > 0:
            role = "All-rounder"
        else:
            role = "Bowler"
    elif "runs" in cricsheet_player and cricsheet_player.get("runs", 0) > 0:
        role = "Batsman"

    # Extract batting stats
    batting_avg = 0
    if "runs" in cricsheet_player and "innings" in cricsheet_player and cricsheet_player.get("innings", 0) > 0:
        not_outs = cricsheet_player.get("not_outs", 0)
        innings = cricsheet_player.get("innings", 0)
        runs = cricsheet_player.get("runs", 0)

        # Calculate batting average (runs / (innings - not outs))
        if innings > not_outs:
            batting_avg = runs / (innings - not_outs)

    # Extract bowling stats
    bowling_avg = 0
    economy = 0
    if "wickets" in cricsheet_player and cricsheet_player.get("wickets", 0) > 0:
        wickets = cricsheet_player.get("wickets", 0)
        runs_conceded = cricsheet_player.get("runs_conceded", 0)
        balls_bowled = cricsheet_player.get("balls_bowled", 0)

        # Calculate bowling average (runs conceded / wickets)
        if wickets > 0:
            bowling_avg = runs_conceded / wickets

        # Calculate economy rate (runs conceded / (balls bowled / 6))
        if balls_bowled > 0:
            economy = (runs_conceded / (balls_bowled / 6))

    # Extract recent form
    recent_form = []
    recent_wickets = []

    # Process recent performances
    recent_performances = cricsheet_player.get("recent_performances", [])
    for perf in recent_performances:
        if "runs" in perf:
            recent_form.append(perf.get("runs", 0))
        if "wickets" in perf:
            recent_wickets.append(perf.get("wickets", 0))

    # Ensure we have at least 5 entries in recent form/wickets
    while len(recent_form) < 5:
        recent_form.append(0)

    while len(recent_wickets) < 5:
        recent_wickets.append(0)

    # Calculate fantasy points average (mock calculation)
    fantasy_points_avg = 0
    if role == "Batsman":
        fantasy_points_avg = batting_avg * 1.5
    elif role == "Bowler":
        fantasy_points_avg = (30 / bowling_avg) * 30 if bowling_avg > 0 else 30
    elif role == "All-rounder":
        batting_points = batting_avg * 1.2
        bowling_points = (30 / bowling_avg) * 25 if bowling_avg > 0 else 25
        fantasy_points_avg = batting_points + bowling_points

    # Mock ownership and price data
    ownership = min(90, max(10, fantasy_points_avg * 0.8))
    price = min(11, max(5, fantasy_points_avg / 10))

    return {
        "name": name,
        "team": cricsheet_player.get("team", "Unknown"),
        "role": role,
        "batting_avg": batting_avg,
        "bowling_avg": bowling_avg,
        "strike_rate": cricsheet_player.get("strike_rate", 0),
        "economy": economy,
        "recent_form": recent_form[:5],  # Limit to 5 most recent
        "recent_wickets": recent_wickets[:5],  # Limit to 5 most recent
        "fantasy_points_avg": fantasy_points_avg,
        "ownership": ownership,
        "price": price,
        "matches_played": matches_played,
        "source": "Cricsheet"
    }

def get_match_details(match_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific match

    Parameters:
    - match_id: ID of the match

    Returns:
    - Match details in application format
    """
    # Try Cricbuzz first (most real-time)
    if CRICBUZZ_ENABLED:
        try:
            cricbuzz_match = cricbuzz.get_match_score(match_id)
            if cricbuzz_match:
                logger.info(f"Found match details for {match_id} from Cricbuzz")

                # Convert to application format
                match_info = cricbuzz_match.get("matchInfo", {})
                match_score = cricbuzz_match.get("matchScore", {})

                # Extract teams
                team1 = match_info.get("team1", {}).get("teamName", "Unknown")
                team2 = match_info.get("team2", {}).get("teamName", "Unknown")
                teams_str = f"{team1} vs {team2}"

                # Extract venue
                venue = match_info.get("venueInfo", {}).get("ground", "Unknown")
                city = match_info.get("venueInfo", {}).get("city", "")
                if city and city not in venue:
                    venue = f"{venue}, {city}"

                # Extract date
                match_date = match_info.get("startDate", 0)
                date = "Unknown"
                if match_date:
                    try:
                        # Convert milliseconds timestamp to datetime
                        date_obj = datetime.fromtimestamp(match_date / 1000)
                        date = date_obj.strftime("%Y-%m-%d")
                    except:
                        pass

                # Extract match type
                match_format = match_info.get("matchFormat", "Unknown")
                match_type = match_format.upper()

                # Extract status
                status = match_info.get("status", "Unknown")

                # Extract scores
                scores = []
                team1_score = match_score.get("team1Score", {})
                team2_score = match_score.get("team2Score", {})

                for innings_key, innings_data in team1_score.items():
                    innings_num = innings_data.get("inningsId", 0)
                    runs = innings_data.get("runs", 0)
                    wickets = innings_data.get("wickets", 0)
                    overs = innings_data.get("overs", 0)
                    declared = innings_data.get("isDeclared", False)

                    score_str = f"{team1} {runs}/{wickets}"
                    if overs:
                        score_str += f" ({overs} ov)"
                    if declared:
                        score_str += " (d)"

                    scores.append({
                        "team": team1,
                        "innings": innings_num,
                        "runs": runs,
                        "wickets": wickets,
                        "overs": overs,
                        "declared": declared,
                        "score_str": score_str
                    })

                for innings_key, innings_data in team2_score.items():
                    innings_num = innings_data.get("inningsId", 0)
                    runs = innings_data.get("runs", 0)
                    wickets = innings_data.get("wickets", 0)
                    overs = innings_data.get("overs", 0)
                    declared = innings_data.get("isDeclared", False)
                    follow_on = innings_data.get("isFollowOn", False)

                    score_str = f"{team2} {runs}/{wickets}"
                    if overs:
                        score_str += f" ({overs} ov)"
                    if declared:
                        score_str += " (d)"
                    if follow_on:
                        score_str += " (f/o)"

                    scores.append({
                        "team": team2,
                        "innings": innings_num,
                        "runs": runs,
                        "wickets": wickets,
                        "overs": overs,
                        "declared": declared,
                        "follow_on": follow_on,
                        "score_str": score_str
                    })

                # Sort scores by innings number
                scores.sort(key=lambda x: x.get("innings", 0))

                # Create mock pitch conditions
                import random
                pitch_conditions = {
                    "batting_friendly": random.randint(4, 8),
                    "pace_friendly": random.randint(4, 8),
                    "spin_friendly": random.randint(4, 8)
                }

                return {
                    "match_id": match_id,
                    "teams": teams_str,
                    "venue": venue,
                    "date": date,
                    "match_type": match_type,
                    "status": status,
                    "scores": scores,
                    "pitch_conditions": pitch_conditions,
                    "source": "Cricbuzz"
                }
        except Exception as e:
            logger.error(f"Error getting match details from Cricbuzz: {str(e)}")

    # Try Cricsheet next (most detailed)
    if CRICSHEET_ENABLED:
        try:
            # Determine match type from match ID format
            match_type = None
            if match_id.startswith("t20"):
                match_type = "t20"
            elif match_id.startswith("odi"):
                match_type = "odi"
            elif match_id.startswith("test"):
                match_type = "test"

            if match_type:
                cricsheet_match = cricsheet.download_match_data(match_type, match_id)
                if cricsheet_match:
                    logger.info(f"Found match details for {match_id} from Cricsheet")

                    # Convert to application format
                    match_info = cricsheet_match.get("info", {})

                    # Extract teams
                    teams = match_info.get("teams", [])
                    teams_str = " vs ".join(teams) if teams else "Unknown vs Unknown"

                    # Extract venue
                    venue = match_info.get("venue", "Unknown")
                    city = match_info.get("city", "")
                    if city and city not in venue:
                        venue = f"{venue}, {city}"

                    # Extract date
                    dates = match_info.get("dates", [])
                    date = dates[0] if dates else "Unknown"

                    # Extract match type
                    match_format = match_type.upper()

                    # Extract status
                    outcome = match_info.get("outcome", {})
                    if "winner" in outcome:
                        winner = outcome.get("winner", "")
                        by_runs = outcome.get("by", {}).get("runs", 0)
                        by_wickets = outcome.get("by", {}).get("wickets", 0)

                        if by_runs:
                            status = f"{winner} won by {by_runs} runs"
                        elif by_wickets:
                            status = f"{winner} won by {by_wickets} wickets"
                        else:
                            status = f"{winner} won"
                    elif "result" in outcome:
                        status = outcome.get("result", "Unknown")
                    else:
                        status = "Unknown"

                    # Extract innings data
                    innings = cricsheet_match.get("innings", [])
                    scores = []

                    for i, inning in enumerate(innings):
                        team = inning.get("team", "Unknown")
                        overs = len(inning.get("overs", []))
                        runs = 0
                        wickets = 0

                        # Calculate runs and wickets
                        for over in inning.get("overs", []):
                            for delivery in over.get("deliveries", []):
                                runs += delivery.get("runs", {}).get("total", 0)
                                if "wicket" in delivery:
                                    wickets += 1

                        score_str = f"{team} {runs}/{wickets}"
                        if overs:
                            score_str += f" ({overs} ov)"

                        scores.append({
                            "team": team,
                            "innings": i + 1,
                            "runs": runs,
                            "wickets": wickets,
                            "overs": overs,
                            "score_str": score_str
                        })

                    # Create mock pitch conditions
                    import random
                    pitch_conditions = {
                        "batting_friendly": random.randint(4, 8),
                        "pace_friendly": random.randint(4, 8),
                        "spin_friendly": random.randint(4, 8)
                    }

                    return {
                        "match_id": match_id,
                        "teams": teams_str,
                        "venue": venue,
                        "date": date,
                        "match_type": match_format,
                        "status": status,
                        "scores": scores,
                        "pitch_conditions": pitch_conditions,
                        "source": "Cricsheet"
                    }
        except Exception as e:
            logger.error(f"Error getting match details from Cricsheet: {str(e)}")

    # If no match details found, return a default response
    logger.warning(f"No match details found for match ID: {match_id}")
    return {
        "match_id": match_id,
        "teams": "Unknown vs Unknown",
        "venue": "Unknown",
        "date": "Unknown",
        "match_type": "Unknown",
        "status": "Unknown",
        "scores": [],
        "error": "Match details not found"
    }

def _analyze_player_form(player_data: Dict[str, Any]) -> str:
    """
    Analyze player form based on detailed performance data

    Parameters:
    - player_data: Detailed player data

    Returns:
    - Form rating (excellent, good, average, poor, unknown)
    """
    # Check if we have recent performances data
    recent_performances = player_data.get("recent_performances", [])

    if not recent_performances:
        logger.warning("No recent performances data available for form analysis")
        return "unknown"

    # Determine player role based on stats
    role = "Unknown"
    if "wickets" in player_data and player_data.get("wickets", 0) > 0:
        if "runs" in player_data and player_data.get("runs", 0) > 0:
            role = "All-rounder"
        else:
            role = "Bowler"
    elif "runs" in player_data and player_data.get("runs", 0) > 0:
        role = "Batsman"

    # For batsmen, analyze recent runs
    if role in ["Batsman", "All-rounder"]:
        # Extract runs from recent performances
        recent_runs = []
        for perf in recent_performances:
            if "runs" in perf:
                recent_runs.append(perf.get("runs", 0))

        if recent_runs:
            avg_runs = sum(recent_runs) / len(recent_runs)

            # Analyze batting form
            if avg_runs > 50:
                return "excellent"
            elif avg_runs > 35:
                return "good"
            elif avg_runs > 20:
                return "average"
            else:
                return "poor"

    # For bowlers, analyze recent wickets
    if role in ["Bowler", "All-rounder"]:
        # Extract wickets from recent performances
        recent_wickets = []
        for perf in recent_performances:
            if "wickets" in perf:
                recent_wickets.append(perf.get("wickets", 0))

        if recent_wickets:
            avg_wickets = sum(recent_wickets) / len(recent_wickets)

            # Analyze bowling form
            if avg_wickets > 2.5:
                return "excellent"
            elif avg_wickets > 1.5:
                return "good"
            elif avg_wickets > 1:
                return "average"
            else:
                return "poor"

    # If we couldn't determine form from recent performances
    logger.warning("Could not determine form from recent performances")
    return "unknown"

def get_recommended_players(role: Optional[str] = None, team: Optional[str] = None, venue: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get recommended players based on role, team, and venue"""
    # This is a simplified implementation
    # In a real application, you would use more sophisticated algorithms

    # Get all players (this is a mock implementation)
    all_players = []

    # Add some known players from our fallback data
    for player in FALLBACK_PLAYER_DATA:
        all_players.append(player)

    # Filter by role if specified
    if role:
        all_players = [p for p in all_players if p.get("role", "").lower() == role.lower()]

    # Filter by team if specified
    if team:
        all_players = [p for p in all_players if team.lower() in p.get("team", "").lower()]

    # Consider venue if specified
    if venue:
        pitch_conditions = get_pitch_conditions(venue)

        # Adjust player scores based on pitch conditions
        for player in all_players:
            venue_bonus = 0

            if player.get("role") == "Batsman" and pitch_conditions.get("batting_friendly", 5) >= 7:
                venue_bonus = 5
            elif player.get("role") == "Bowler" and pitch_conditions.get("pace_friendly", 5) >= 7:
                venue_bonus = 5
            elif player.get("role") == "Bowler" and pitch_conditions.get("spin_friendly", 5) >= 7:
                venue_bonus = 5

            player["adjusted_score"] = player.get("fantasy_points_avg", 0) + venue_bonus

    # Sort by fantasy points average or adjusted score
    if venue:
        all_players.sort(key=lambda x: x.get("adjusted_score", 0), reverse=True)
    else:
        all_players.sort(key=lambda x: x.get("fantasy_points_avg", 0), reverse=True)

    return all_players
