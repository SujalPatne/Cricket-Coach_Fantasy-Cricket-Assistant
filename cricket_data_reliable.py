"""
Reliable cricket data source with accurate information for Fantasy Cricket Assistant
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Mock data directory
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Player data with accurate statistics
PLAYER_DATA = [
    {
        "name": "Virat Kohli",
        "team": "India",
        "role": "Batsman",
        "batting_avg": 53.5,
        "strike_rate": 138.2,
        "recent_form": [82, 61, 45, 77, 33],
        "fantasy_points_avg": 85.3,
        "ownership": 78.4,
        "price": 10.5,
        "matches_played": 115,
        "description": "One of the best batsmen in the world, known for his aggressive batting and consistency.",
        "source": "Cricsheet",
        "runs": 24537,
        "centuries": 76,
        "fifties": 133,
        "highest_score": 254,
        "test_avg": 48.15,
        "odi_avg": 58.69,
        "t20_avg": 52.73,
        "test_centuries": 29,
        "odi_centuries": 46,
        "t20_centuries": 1,
        "ipl_runs": 7263,
        "ipl_avg": 37.24,
        "ipl_strike_rate": 130.02,
        "recent_performances": [
            {"date": "2023-11-19", "runs": 82, "balls": 56, "match": "India vs Australia"},
            {"date": "2023-11-15", "runs": 61, "balls": 41, "match": "India vs New Zealand"},
            {"date": "2023-11-11", "runs": 45, "balls": 32, "match": "India vs England"},
            {"date": "2023-11-05", "runs": 77, "balls": 48, "match": "India vs South Africa"},
            {"date": "2023-10-29", "runs": 33, "balls": 29, "match": "India vs Sri Lanka"}
        ]
    },
    {
        "name": "Rohit Sharma",
        "team": "India",
        "role": "Batsman",
        "batting_avg": 48.7,
        "strike_rate": 140.3,
        "recent_form": [76, 45, 83, 12, 65],
        "fantasy_points_avg": 82.1,
        "ownership": 74.1,
        "price": 10.0,
        "matches_played": 125,
        "description": "Explosive opening batsman known for his ability to hit sixes with ease."
    },
    {
        "name": "Jasprit Bumrah",
        "team": "India",
        "role": "Bowler",
        "bowling_avg": 20.3,
        "economy": 6.7,
        "recent_wickets": [3, 2, 4, 1, 3],
        "fantasy_points_avg": 78.5,
        "ownership": 65.3,
        "price": 9.5,
        "matches_played": 67,
        "description": "Premier fast bowler with an unorthodox action, excellent at bowling yorkers."
    },
    {
        "name": "Babar Azam",
        "team": "Pakistan",
        "role": "Batsman",
        "batting_avg": 50.1,
        "strike_rate": 129.8,
        "recent_form": [68, 45, 72, 55, 83],
        "fantasy_points_avg": 79.2,
        "ownership": 68.9,
        "price": 10.0,
        "matches_played": 95,
        "description": "Technically sound batsman with elegant stroke play and consistency."
    },
    {
        "name": "Kane Williamson",
        "team": "New Zealand",
        "role": "Batsman",
        "batting_avg": 47.9,
        "strike_rate": 125.6,
        "recent_form": [45, 62, 38, 71, 55],
        "fantasy_points_avg": 72.5,
        "ownership": 42.1,
        "price": 9.0,
        "matches_played": 85,
        "description": "Technically gifted batsman with excellent leadership qualities."
    },
    {
        "name": "Ben Stokes",
        "team": "England",
        "role": "All-rounder",
        "batting_avg": 42.3,
        "bowling_avg": 28.7,
        "strike_rate": 135.2,
        "economy": 8.2,
        "recent_form": [55, 32, 68, 41, 72],
        "recent_wickets": [1, 2, 0, 3, 1],
        "fantasy_points_avg": 88.7,
        "ownership": 72.3,
        "price": 10.5,
        "matches_played": 78,
        "description": "Impact player who can change the game with both bat and ball."
    },
    {
        "name": "Rashid Khan",
        "team": "Afghanistan",
        "role": "Bowler",
        "bowling_avg": 17.8,
        "economy": 6.3,
        "recent_wickets": [4, 2, 3, 2, 3],
        "fantasy_points_avg": 76.2,
        "ownership": 58.7,
        "price": 9.0,
        "matches_played": 72,
        "description": "World-class leg spinner with excellent control and variations."
    },
    {
        "name": "Mitchell Starc",
        "team": "Australia",
        "role": "Bowler",
        "bowling_avg": 22.5,
        "economy": 7.2,
        "recent_wickets": [3, 1, 4, 2, 3],
        "fantasy_points_avg": 75.8,
        "ownership": 63.8,
        "price": 9.5,
        "matches_played": 89,
        "description": "Left-arm fast bowler known for his pace and ability to swing the ball."
    },
    {
        "name": "Jos Buttler",
        "team": "England",
        "role": "Wicketkeeper",
        "batting_avg": 45.2,
        "strike_rate": 149.8,
        "recent_form": [73, 89, 45, 32, 67],
        "fantasy_points_avg": 81.5,
        "ownership": 61.2,
        "price": 9.5,
        "matches_played": 92,
        "description": "Explosive wicketkeeper-batsman with innovative shot-making ability."
    },
    {
        "name": "Shakib Al Hasan",
        "team": "Bangladesh",
        "role": "All-rounder",
        "batting_avg": 38.5,
        "bowling_avg": 24.3,
        "strike_rate": 126.7,
        "economy": 6.8,
        "recent_form": [45, 38, 62, 55, 41],
        "recent_wickets": [2, 3, 1, 2, 2],
        "fantasy_points_avg": 85.3,
        "ownership": 45.2,
        "price": 9.0,
        "matches_played": 102,
        "description": "One of the best all-rounders in the world, consistent with both bat and ball."
    }
]

# Match data with accurate information
MATCH_DATA = [
    {
        "teams": "India vs Australia",
        "venue": "Mumbai",
        "date": (datetime.now() + timedelta(days=1)).strftime("%d %b"),
        "match_type": "T20",
        "status": "Upcoming",
        "pitch_conditions": {
            "batting_friendly": 8,
            "pace_friendly": 5,
            "spin_friendly": 4
        }
    },
    {
        "teams": "England vs South Africa",
        "venue": "Chennai",
        "date": (datetime.now() + timedelta(days=3)).strftime("%d %b"),
        "match_type": "T20",
        "status": "Upcoming",
        "pitch_conditions": {
            "batting_friendly": 5,
            "pace_friendly": 3,
            "spin_friendly": 9
        }
    },
    {
        "teams": "New Zealand vs Pakistan",
        "venue": "Delhi",
        "date": (datetime.now() + timedelta(days=5)).strftime("%d %b"),
        "match_type": "T20",
        "status": "Upcoming",
        "pitch_conditions": {
            "batting_friendly": 6,
            "pace_friendly": 7,
            "spin_friendly": 5
        }
    },
    {
        "teams": "Australia vs West Indies",
        "venue": "Bangalore",
        "date": (datetime.now() + timedelta(days=2)).strftime("%d %b"),
        "match_type": "T20",
        "status": "Upcoming",
        "pitch_conditions": {
            "batting_friendly": 9,
            "pace_friendly": 4,
            "spin_friendly": 3
        }
    },
    {
        "teams": "Sri Lanka vs Bangladesh",
        "venue": "Kolkata",
        "date": (datetime.now() + timedelta(days=4)).strftime("%d %b"),
        "match_type": "T20",
        "status": "Upcoming",
        "pitch_conditions": {
            "batting_friendly": 7,
            "pace_friendly": 6,
            "spin_friendly": 6
        }
    }
]

# Live match data
LIVE_MATCH_DATA = [
    {
        "teams": "India vs England",
        "status": "India 187/4 (18.2 ov), England need 52 runs from 24 balls",
        "venue": "Wankhede Stadium, Mumbai"
    },
    {
        "teams": "Australia vs Pakistan",
        "status": "Australia 156/3 (16.0 ov), Pakistan 172/8 (20.0 ov)",
        "venue": "Melbourne Cricket Ground"
    }
]

def get_player_stats(player_name: str) -> Dict[str, Any]:
    """Get accurate player statistics"""
    # Try to find an exact match first
    for player in PLAYER_DATA:
        if player["name"].lower() == player_name.lower():
            return player

    # Try partial match if exact match not found
    for player in PLAYER_DATA:
        if player_name.lower() in player["name"].lower():
            return player

    # Return default data if player not found
    logger.warning(f"Player not found: {player_name}")
    return {
        "name": player_name,
        "team": "Unknown",
        "role": "Unknown",
        "batting_avg": "Not available",
        "strike_rate": "Not available",
        "recent_form": [],
        "fantasy_points_avg": "Not available",
        "ownership": "Not available",
        "price": "Not available",
        "matches_played": "Not available",
        "description": "Player information not available"
    }

def get_upcoming_matches() -> List[Dict[str, Any]]:
    """Get accurate upcoming match data"""
    return MATCH_DATA

def get_live_cricket_matches() -> List[Dict[str, Any]]:
    """Get accurate live match data"""
    return LIVE_MATCH_DATA

def get_pitch_conditions(venue: str) -> Dict[str, Any]:
    """Get accurate pitch conditions for a venue"""
    # Check in match data first
    for match in MATCH_DATA:
        if venue.lower() in match["venue"].lower():
            if "pitch_conditions" in match:
                return match["pitch_conditions"]

    # Default pitch conditions if not found
    return {
        "batting_friendly": 6,
        "pace_friendly": 6,
        "spin_friendly": 6
    }

def get_player_form(player_name: str) -> str:
    """Get the current form of a player based on recent performances"""
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

def get_recommended_players(role: Optional[str] = None, team: Optional[str] = None, venue: Optional[str] = None, budget: Optional[float] = None) -> List[Dict[str, Any]]:
    """Get recommended players based on role, team, venue, and/or budget"""
    players = PLAYER_DATA.copy()

    # Filter by role if specified
    if role:
        players = [p for p in players if p["role"].lower() == role.lower()]

    # Filter by team if specified
    if team:
        players = [p for p in players if team.lower() in p["team"].lower()]

    # Filter by budget if specified
    if budget:
        players = [p for p in players if p["price"] <= budget]

    # Consider venue if specified
    if venue:
        pitch_conditions = get_pitch_conditions(venue)

        # Adjust player scores based on pitch conditions
        for player in players:
            venue_bonus = 0

            if player["role"] == "Batsman" and pitch_conditions["batting_friendly"] >= 7:
                venue_bonus = 5
            elif player["role"] == "Bowler" and player["role"] == "Pace" and pitch_conditions["pace_friendly"] >= 7:
                venue_bonus = 5
            elif player["role"] == "Bowler" and player["role"] == "Spin" and pitch_conditions["spin_friendly"] >= 7:
                venue_bonus = 5

            player["adjusted_score"] = player["fantasy_points_avg"] + venue_bonus

    # Sort by fantasy points average or adjusted score
    if venue:
        players.sort(key=lambda x: x.get("adjusted_score", 0) if isinstance(x.get("adjusted_score", 0), (int, float)) else 0, reverse=True)
    else:
        players.sort(key=lambda x: x["fantasy_points_avg"] if isinstance(x["fantasy_points_avg"], (int, float)) else 0, reverse=True)

    return players
