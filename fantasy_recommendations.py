"""
Fantasy Cricket Recommendations Module

This module provides functions for generating fantasy cricket recommendations
based on player statistics, match conditions, and other relevant factors.
"""

import logging
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Import cricket data functions
from cricket_data_adapter import (
    get_player_stats,
    get_live_cricket_matches,
    get_upcoming_matches,
    get_pitch_conditions
)

# Set up logging
logger = logging.getLogger(__name__)

# Cache for recommendations to avoid redundant calculations
RECOMMENDATIONS_CACHE = {
    'differential_picks': {'data': None, 'timestamp': 0},
    'captain_picks': {'data': None, 'timestamp': 0},
    'player_comparisons': {}
}

# Cache expiration (in seconds)
CACHE_EXPIRY = {
    'differential_picks': 3600,  # 1 hour
    'captain_picks': 3600,  # 1 hour
    'player_comparisons': 3600  # 1 hour
}

def get_differential_picks(match_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get differential player picks for fantasy cricket

    Parameters:
    - match_id: Optional match ID to get picks for a specific match

    Returns:
    - List of player recommendations with reasoning
    """
    # Check cache first
    if RECOMMENDATIONS_CACHE['differential_picks']['data'] is not None:
        if (time.time() - RECOMMENDATIONS_CACHE['differential_picks']['timestamp']) < CACHE_EXPIRY['differential_picks']:
            logger.info("Using cached differential picks")
            return RECOMMENDATIONS_CACHE['differential_picks']['data']

    logger.info("Generating fresh differential picks")

    # Get live or upcoming matches
    matches = get_live_cricket_matches()
    if not matches:
        matches = get_upcoming_matches()

    if not matches:
        logger.warning("No matches found for differential picks")
        return []

    # Filter by match_id if provided
    if match_id:
        matches = [match for match in matches if match.get('id') == match_id]
        if not matches:
            logger.warning(f"Match with ID {match_id} not found")
            return []

    # Get the first match (or the specified match)
    match = matches[0]

    # Extract teams
    teams = match.get('teams', '').split(' vs ')
    if len(teams) != 2:
        logger.warning(f"Could not extract teams from match: {match.get('teams')}")
        return []

    team1, team2 = teams

    # Get venue for pitch conditions
    venue = match.get('venue')
    pitch_conditions = get_pitch_conditions(venue) if venue else None

    # Generate differential picks based on match conditions and player stats
    differential_picks = []

    # Get players from both teams
    team1_players = _get_team_players(team1)
    team2_players = _get_team_players(team2)

    # Analyze players for differential picks
    all_players = team1_players + team2_players

    for player in all_players:
        # Skip highly owned players (not differential)
        if player.get('ownership', 0) > 50:
            continue

        # Calculate differential score based on form, matchup, and pitch conditions
        differential_score = _calculate_differential_score(player, pitch_conditions, match)

        if differential_score > 7:
            player['differential_score'] = differential_score
            player['reasoning'] = _generate_differential_reasoning(player, pitch_conditions, match)
            differential_picks.append(player)

    # Sort by differential score
    differential_picks.sort(key=lambda x: x.get('differential_score', 0), reverse=True)

    # Limit to top 5
    differential_picks = differential_picks[:5]

    # Update cache
    RECOMMENDATIONS_CACHE['differential_picks'] = {
        'data': differential_picks,
        'timestamp': time.time()
    }

    return differential_picks

def compare_players(player1_name: str, player2_name: str) -> Dict[str, Any]:
    """
    Compare two players for fantasy cricket

    Parameters:
    - player1_name: Name of first player
    - player2_name: Name of second player

    Returns:
    - Comparison results with recommendation
    """
    # Create cache key
    cache_key = f"{player1_name.lower()}_{player2_name.lower()}"

    # Check cache first
    if cache_key in RECOMMENDATIONS_CACHE['player_comparisons']:
        if (time.time() - RECOMMENDATIONS_CACHE['player_comparisons'][cache_key]['timestamp']) < CACHE_EXPIRY['player_comparisons']:
            logger.info(f"Using cached comparison for {player1_name} vs {player2_name}")
            return RECOMMENDATIONS_CACHE['player_comparisons'][cache_key]['data']

    logger.info(f"Generating fresh comparison for {player1_name} vs {player2_name}")

    # Get player stats
    player1 = get_player_stats(player1_name)
    player2 = get_player_stats(player2_name)

    if not player1 or not player2:
        logger.warning(f"Could not get stats for one or both players: {player1_name}, {player2_name}")
        return {
            'error': 'Could not get stats for one or both players',
            'recommendation': 'Insufficient data for comparison'
        }

    # Get live or upcoming matches
    matches = get_live_cricket_matches()
    if not matches:
        matches = get_upcoming_matches()

    # Get venue for pitch conditions
    venue = matches[0].get('venue') if matches else None
    pitch_conditions = get_pitch_conditions(venue) if venue else None

    # Compare players
    comparison = {
        'player1': {
            'name': player1_name,
            'stats': _extract_key_stats(player1),
            'score': _calculate_player_score(player1, pitch_conditions)
        },
        'player2': {
            'name': player2_name,
            'stats': _extract_key_stats(player2),
            'score': _calculate_player_score(player2, pitch_conditions)
        }
    }

    # Generate recommendation
    if comparison['player1']['score'] > comparison['player2']['score']:
        comparison['recommendation'] = f"Pick {player1_name} over {player2_name}"
        comparison['reasoning'] = _generate_comparison_reasoning(player1, player2, pitch_conditions)
    else:
        comparison['recommendation'] = f"Pick {player2_name} over {player1_name}"
        comparison['reasoning'] = _generate_comparison_reasoning(player2, player1, pitch_conditions)

    # Update cache
    RECOMMENDATIONS_CACHE['player_comparisons'][cache_key] = {
        'data': comparison,
        'timestamp': time.time()
    }

    return comparison

def get_captain_picks() -> List[Dict[str, Any]]:
    """
    Get captain and vice-captain recommendations for fantasy cricket

    Returns:
    - List of player recommendations for captain/vice-captain
    """
    # Check cache first
    if RECOMMENDATIONS_CACHE['captain_picks']['data'] is not None:
        if (time.time() - RECOMMENDATIONS_CACHE['captain_picks']['timestamp']) < CACHE_EXPIRY['captain_picks']:
            logger.info("Using cached captain picks")
            return RECOMMENDATIONS_CACHE['captain_picks']['data']

    logger.info("Generating fresh captain picks")

    # Get live or upcoming matches
    matches = get_live_cricket_matches()
    if not matches:
        matches = get_upcoming_matches()

    if not matches:
        logger.warning("No matches found for captain picks")
        return []

    # Get the first match
    match = matches[0]

    # Extract teams
    teams = match.get('teams', '').split(' vs ')
    if len(teams) != 2:
        logger.warning(f"Could not extract teams from match: {match.get('teams')}")
        return []

    team1, team2 = teams

    # Get venue for pitch conditions
    venue = match.get('venue')
    pitch_conditions = get_pitch_conditions(venue) if venue else None

    # Get players from both teams
    team1_players = _get_team_players(team1)
    team2_players = _get_team_players(team2)

    # Analyze players for captain picks
    all_players = team1_players + team2_players

    # Calculate captain scores
    for player in all_players:
        player['captain_score'] = _calculate_captain_score(player, pitch_conditions, match)

    # Sort by captain score
    all_players.sort(key=lambda x: x.get('captain_score', 0), reverse=True)

    # Get top 3 for captain and next 3 for vice-captain
    captain_picks = []

    for i, player in enumerate(all_players[:6]):
        pick = {
            'name': player.get('name'),
            'role': player.get('role', 'Unknown'),
            'team': player.get('team', 'Unknown'),
            'captain_score': player.get('captain_score', 0),
            'recommendation': 'Captain' if i < 3 else 'Vice-Captain',
            'reasoning': _generate_captain_reasoning(player, pitch_conditions, match)
        }
        captain_picks.append(pick)

    # Update cache
    RECOMMENDATIONS_CACHE['captain_picks'] = {
        'data': captain_picks,
        'timestamp': time.time()
    }

    return captain_picks

# Helper functions
def _get_team_players(team_name: str) -> List[Dict[str, Any]]:
    """Get players for a specific team"""
    # This is a simplified implementation
    # In a real system, you'd query a database or API for the team's players

    # Common players for major teams
    team_players = {
        'India': ['Virat Kohli', 'Rohit Sharma', 'Jasprit Bumrah', 'KL Rahul', 'Hardik Pandya', 'Ravindra Jadeja'],
        'Australia': ['Steve Smith', 'David Warner', 'Pat Cummins', 'Mitchell Starc', 'Glenn Maxwell'],
        'England': ['Joe Root', 'Ben Stokes', 'Jofra Archer', 'Jos Buttler', 'Eoin Morgan'],
        'New Zealand': ['Kane Williamson', 'Trent Boult', 'Ross Taylor', 'Tim Southee', 'Martin Guptill'],
        'Pakistan': ['Babar Azam', 'Shaheen Afridi', 'Mohammad Rizwan', 'Shadab Khan', 'Fakhar Zaman'],
        'South Africa': ['Quinton de Kock', 'Kagiso Rabada', 'Anrich Nortje', 'David Miller', 'Aiden Markram'],
        'West Indies': ['Kieron Pollard', 'Nicholas Pooran', 'Jason Holder', 'Shimron Hetmyer', 'Andre Russell'],
        'Sri Lanka': ['Wanindu Hasaranga', 'Dushmantha Chameera', 'Charith Asalanka', 'Pathum Nissanka'],
        'Bangladesh': ['Shakib Al Hasan', 'Mushfiqur Rahim', 'Mustafizur Rahman', 'Mahmudullah'],
        'Afghanistan': ['Rashid Khan', 'Mohammad Nabi', 'Mujeeb Ur Rahman', 'Rahmanullah Gurbaz']
    }

    # Handle IPL teams
    ipl_teams = {
        'Mumbai Indians': ['Rohit Sharma', 'Jasprit Bumrah', 'Suryakumar Yadav', 'Ishan Kishan', 'Hardik Pandya'],
        'Chennai Super Kings': ['MS Dhoni', 'Ravindra Jadeja', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Moeen Ali'],
        'Royal Challengers Bangalore': ['Virat Kohli', 'Glenn Maxwell', 'Faf du Plessis', 'Mohammed Siraj'],
        'Kolkata Knight Riders': ['Shreyas Iyer', 'Andre Russell', 'Sunil Narine', 'Venkatesh Iyer'],
        'Delhi Capitals': ['Rishabh Pant', 'Axar Patel', 'Prithvi Shaw', 'Anrich Nortje', 'David Warner'],
        'Punjab Kings': ['KL Rahul', 'Mayank Agarwal', 'Arshdeep Singh', 'Kagiso Rabada'],
        'Rajasthan Royals': ['Sanju Samson', 'Jos Buttler', 'Yuzvendra Chahal', 'Trent Boult'],
        'Sunrisers Hyderabad': ['Kane Williamson', 'Bhuvneshwar Kumar', 'T Natarajan', 'Nicholas Pooran']
    }

    # Combine both dictionaries
    all_teams = {**team_players, **ipl_teams}

    # Find the closest team name match
    team_key = None
    for key in all_teams.keys():
        if team_name.lower() in key.lower() or key.lower() in team_name.lower():
            team_key = key
            break

    if not team_key:
        logger.warning(f"No players found for team: {team_name}")
        return []

    # Get player stats for each player
    players = []
    for player_name in all_teams[team_key]:
        player_stats = get_player_stats(player_name)
        if player_stats:
            players.append(player_stats)

    return players

def _calculate_differential_score(player: Dict[str, Any], pitch_conditions: Optional[Dict[str, Any]], match: Dict[str, Any]) -> float:
    """Calculate a differential score for a player"""
    score = 5.0  # Base score

    # Factor in player form
    if 'recent_form' in player:
        recent_form = player['recent_form']
        avg_score = sum(recent_form) / len(recent_form) if recent_form else 0

        if avg_score > 50:
            score += 2.0
        elif avg_score > 30:
            score += 1.0
        elif avg_score < 15:
            score -= 1.0

    # Factor in player role
    role = player.get('role', '').lower()
    if 'all-rounder' in role:
        score += 1.5  # All-rounders have more ways to score points
    elif 'bowler' in role and pitch_conditions and pitch_conditions.get('bowler_friendly', False):
        score += 1.0  # Bowlers do better on bowler-friendly pitches
    elif 'batsman' in role and pitch_conditions and pitch_conditions.get('batsman_friendly', False):
        score += 1.0  # Batsmen do better on batsman-friendly pitches

    # Factor in ownership
    ownership = player.get('ownership', 50)
    if ownership < 10:
        score += 2.0  # Very low ownership is great for differential
    elif ownership < 25:
        score += 1.0  # Low ownership is good for differential

    # Factor in price
    price = player.get('price', 9.0)
    if price < 7.0:
        score += 1.0  # Budget picks are good differentials

    # Factor in matchup
    teams = match.get('teams', '').split(' vs ')
    if len(teams) == 2:
        player_team = player.get('team', '')
        opponent = teams[0] if teams[1] == player_team else teams[1]

        # This would be more sophisticated in a real system
        # For now, just add a random factor
        matchup_factor = random.uniform(-0.5, 1.5)
        score += matchup_factor

    # Add some randomness to avoid identical scores
    score += random.uniform(-0.2, 0.2)

    return round(score, 1)

def _calculate_player_score(player: Dict[str, Any], pitch_conditions: Optional[Dict[str, Any]]) -> float:
    """Calculate a player score for comparison"""
    score = 5.0  # Base score

    # Factor in player form
    if 'recent_form' in player:
        recent_form = player['recent_form']
        avg_score = sum(recent_form) / len(recent_form) if recent_form else 0

        if avg_score > 50:
            score += 3.0
        elif avg_score > 30:
            score += 1.5
        elif avg_score < 15:
            score -= 1.0

    # Factor in player role
    role = player.get('role', '').lower()
    if 'all-rounder' in role:
        score += 1.0  # All-rounders have more ways to score points
    elif 'bowler' in role and pitch_conditions and pitch_conditions.get('bowler_friendly', False):
        score += 1.5  # Bowlers do better on bowler-friendly pitches
    elif 'batsman' in role and pitch_conditions and pitch_conditions.get('batsman_friendly', False):
        score += 1.5  # Batsmen do better on batsman-friendly pitches

    # Factor in fantasy points average
    fantasy_points_avg = player.get('fantasy_points_avg', 0)
    if fantasy_points_avg > 80:
        score += 2.0
    elif fantasy_points_avg > 60:
        score += 1.0

    # Add some randomness to avoid identical scores
    score += random.uniform(-0.1, 0.1)

    return round(score, 1)

def _calculate_captain_score(player: Dict[str, Any], pitch_conditions: Optional[Dict[str, Any]], match: Dict[str, Any]) -> float:
    """Calculate a captain score for a player"""
    score = 5.0  # Base score

    # Factor in player form
    if 'recent_form' in player:
        recent_form = player['recent_form']
        avg_score = sum(recent_form) / len(recent_form) if recent_form else 0

        if avg_score > 50:
            score += 3.0
        elif avg_score > 30:
            score += 1.5
        elif avg_score < 15:
            score -= 2.0  # Poor form is a big negative for captain

    # Factor in player role
    role = player.get('role', '').lower()
    if 'all-rounder' in role:
        score += 1.5  # All-rounders have more ways to score points
    elif 'bowler' in role and pitch_conditions and pitch_conditions.get('bowler_friendly', False):
        score += 1.0  # Bowlers do better on bowler-friendly pitches
    elif 'batsman' in role and pitch_conditions and pitch_conditions.get('batsman_friendly', False):
        score += 1.0  # Batsmen do better on batsman-friendly pitches

    # Factor in fantasy points average
    fantasy_points_avg = player.get('fantasy_points_avg', 0)
    if fantasy_points_avg > 80:
        score += 2.5  # High fantasy points are crucial for captain
    elif fantasy_points_avg > 60:
        score += 1.5

    # Factor in consistency
    if 'recent_form' in player:
        recent_form = player['recent_form']
        if recent_form:
            # Calculate standard deviation
            mean = sum(recent_form) / len(recent_form)
            variance = sum((x - mean) ** 2 for x in recent_form) / len(recent_form)
            std_dev = variance ** 0.5

            # Lower standard deviation means more consistent
            if std_dev < 10:
                score += 1.5  # Very consistent
            elif std_dev < 20:
                score += 0.5  # Somewhat consistent

    # Add some randomness to avoid identical scores
    score += random.uniform(-0.2, 0.2)

    return round(score, 1)

def _extract_key_stats(player: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key stats for player comparison"""
    key_stats = {}

    # Extract the most important stats
    important_stats = [
        "batting_avg", "strike_rate", "bowling_avg", "economy",
        "recent_form", "recent_wickets", "fantasy_points_avg"
    ]

    for stat in important_stats:
        if stat in player:
            key_stats[stat] = player[stat]

    # Add role and team
    if 'role' in player:
        key_stats['role'] = player['role']

    if 'team' in player:
        key_stats['team'] = player['team']

    return key_stats

def _generate_differential_reasoning(player: Dict[str, Any], pitch_conditions: Optional[Dict[str, Any]], match: Dict[str, Any]) -> str:
    """Generate reasoning for differential pick"""
    name = player.get('name', 'This player')
    role = player.get('role', 'player')
    team = player.get('team', 'their team')

    reasons = []

    # Low ownership reason
    ownership = player.get('ownership', 50)
    if ownership < 10:
        reasons.append(f"has very low ownership ({ownership}%)")
    elif ownership < 25:
        reasons.append(f"has low ownership ({ownership}%)")

    # Form reason
    if 'recent_form' in player:
        recent_form = player['recent_form']
        avg_score = sum(recent_form) / len(recent_form) if recent_form else 0

        if avg_score > 40:
            reasons.append(f"is in good form (avg: {avg_score:.1f})")
        elif avg_score > 25:
            reasons.append(f"has shown decent form recently")

    # Price reason
    price = player.get('price', 9.0)
    if price < 7.0:
        reasons.append(f"is budget-friendly at {price} credits")

    # Pitch condition reason
    if pitch_conditions:
        if 'bowler' in role.lower() and pitch_conditions.get('bowler_friendly', False):
            reasons.append("will benefit from bowler-friendly conditions")
        elif 'batsman' in role.lower() and pitch_conditions.get('batsman_friendly', False):
            reasons.append("will benefit from batting-friendly conditions")

    # Combine reasons
    if reasons:
        reasoning = f"{name} is a good differential pick because they {' and '.join(reasons)}"
    else:
        reasoning = f"{name} could be a good differential pick for this match"

    return reasoning

def _generate_comparison_reasoning(better_player: Dict[str, Any], worse_player: Dict[str, Any], pitch_conditions: Optional[Dict[str, Any]]) -> str:
    """Generate reasoning for player comparison"""
    better_name = better_player.get('name', 'Player 1')
    worse_name = worse_player.get('name', 'Player 2')

    reasons = []

    # Form comparison
    if 'recent_form' in better_player and 'recent_form' in worse_player:
        better_form = better_player['recent_form']
        worse_form = worse_player['recent_form']

        better_avg = sum(better_form) / len(better_form) if better_form else 0
        worse_avg = sum(worse_form) / len(worse_form) if worse_form else 0

        if better_avg > worse_avg:
            reasons.append(f"better current form (avg: {better_avg:.1f} vs {worse_avg:.1f})")

    # Fantasy points comparison
    if 'fantasy_points_avg' in better_player and 'fantasy_points_avg' in worse_player:
        better_points = better_player['fantasy_points_avg']
        worse_points = worse_player['fantasy_points_avg']

        if better_points > worse_points:
            reasons.append(f"higher fantasy points average ({better_points} vs {worse_points})")

    # Role advantage
    better_role = better_player.get('role', '').lower()

    if pitch_conditions:
        if 'bowler' in better_role and pitch_conditions.get('bowler_friendly', False):
            reasons.append("better suited to the bowler-friendly conditions")
        elif 'batsman' in better_role and pitch_conditions.get('batsman_friendly', False):
            reasons.append("better suited to the batting-friendly conditions")

    # Combine reasons
    if reasons:
        reasoning = f"Pick {better_name} over {worse_name} because of {' and '.join(reasons)}"
    else:
        reasoning = f"{better_name} is slightly favored over {worse_name} for this match"

    return reasoning

def _generate_captain_reasoning(player: Dict[str, Any], pitch_conditions: Optional[Dict[str, Any]], match: Dict[str, Any]) -> str:
    """Generate reasoning for captain pick"""
    name = player.get('name', 'This player')
    role = player.get('role', 'player')

    reasons = []

    # Form reason
    if 'recent_form' in player:
        recent_form = player['recent_form']
        avg_score = sum(recent_form) / len(recent_form) if recent_form else 0

        if avg_score > 50:
            reasons.append(f"excellent current form (avg: {avg_score:.1f})")
        elif avg_score > 35:
            reasons.append(f"good current form (avg: {avg_score:.1f})")

    # Fantasy points reason
    fantasy_points_avg = player.get('fantasy_points_avg', 0)
    if fantasy_points_avg > 80:
        reasons.append(f"high fantasy points average ({fantasy_points_avg})")
    elif fantasy_points_avg > 60:
        reasons.append(f"good fantasy points average ({fantasy_points_avg})")

    # Role reason
    if 'all-rounder' in role.lower():
        reasons.append("all-rounder capabilities (can score points with both bat and ball)")

    # Pitch condition reason
    if pitch_conditions:
        if 'bowler' in role.lower() and pitch_conditions.get('bowler_friendly', False):
            reasons.append("favorable bowling conditions")
        elif 'batsman' in role.lower() and pitch_conditions.get('batsman_friendly', False):
            reasons.append("favorable batting conditions")

    # Combine reasons
    if reasons:
        reasoning = f"{name} is a good captain choice because of {' and '.join(reasons)}"
    else:
        reasoning = f"{name} could be a good captain choice for this match"

    return reasoning
