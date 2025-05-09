import pandas as pd
import random

# Mock cricket player data with realistic stats
PLAYER_DATA = [
    {
        "name": "Virat Kohli",
        "role": "Batsman",
        "team": "India",
        "batting_avg": 53.5,
        "strike_rate": 92.7,
        "recent_form": [45, 82, 67, 18, 112],
        "fantasy_points_avg": 87.5,
        "ownership": 78.4,
        "price": 10.5,
        "matches_played": 254,
    },
    {
        "name": "Jasprit Bumrah",
        "role": "Bowler",
        "team": "India",
        "bowling_avg": 22.3,
        "economy": 4.5,
        "recent_wickets": [2, 3, 1, 4, 2],
        "fantasy_points_avg": 78.2,
        "ownership": 65.3,
        "price": 9.5,
        "matches_played": 128,
    },
    {
        "name": "Kane Williamson",
        "role": "Batsman",
        "team": "New Zealand",
        "batting_avg": 47.8,
        "strike_rate": 81.2,
        "recent_form": [32, 56, 88, 45, 21],
        "fantasy_points_avg": 72.6,
        "ownership": 42.1,
        "price": 9.0,
        "matches_played": 157,
    },
    {
        "name": "Rashid Khan",
        "role": "Bowler",
        "team": "Afghanistan",
        "bowling_avg": 18.7,
        "economy": 4.2,
        "recent_wickets": [3, 2, 4, 1, 3],
        "fantasy_points_avg": 82.4,
        "ownership": 58.7,
        "price": 9.0,
        "matches_played": 83,
    },
    {
        "name": "Jos Buttler",
        "role": "Wicketkeeper",
        "team": "England",
        "batting_avg": 40.2,
        "strike_rate": 119.5,
        "recent_form": [67, 39, 88, 102, 14],
        "fantasy_points_avg": 76.8,
        "ownership": 61.2,
        "price": 9.5,
        "matches_played": 157,
    },
    {
        "name": "Babar Azam",
        "role": "Batsman",
        "team": "Pakistan",
        "batting_avg": 56.8,
        "strike_rate": 89.1,
        "recent_form": [103, 56, 72, 33, 91],
        "fantasy_points_avg": 85.3,
        "ownership": 68.9,
        "price": 10.0,
        "matches_played": 92,
    },
    {
        "name": "Ben Stokes",
        "role": "All-rounder",
        "team": "England",
        "batting_avg": 38.7,
        "bowling_avg": 32.1,
        "recent_form": [45, 23, 58, 11, 67],
        "recent_wickets": [1, 2, 0, 3, 1],
        "fantasy_points_avg": 88.7,
        "ownership": 72.3,
        "price": 10.5,
        "matches_played": 105,
    },
    {
        "name": "Trent Boult",
        "role": "Bowler",
        "team": "New Zealand",
        "bowling_avg": 24.5,
        "economy": 4.8,
        "recent_wickets": [2, 3, 1, 3, 2],
        "fantasy_points_avg": 71.2,
        "ownership": 48.7,
        "price": 8.5,
        "matches_played": 98,
    },
    {
        "name": "Quinton de Kock",
        "role": "Wicketkeeper",
        "team": "South Africa",
        "batting_avg": 44.7,
        "strike_rate": 95.3,
        "recent_form": [67, 38, 102, 15, 54],
        "fantasy_points_avg": 74.5,
        "ownership": 52.6,
        "price": 9.0,
        "matches_played": 132,
    },
    {
        "name": "Shakib Al Hasan",
        "role": "All-rounder",
        "team": "Bangladesh",
        "batting_avg": 37.5,
        "bowling_avg": 29.4,
        "recent_form": [56, 32, 41, 78, 22],
        "recent_wickets": [2, 1, 3, 0, 2],
        "fantasy_points_avg": 79.8,
        "ownership": 45.2,
        "price": 9.0,
        "matches_played": 228,
    },
    {
        "name": "Rohit Sharma",
        "role": "Batsman",
        "team": "India",
        "batting_avg": 48.9,
        "strike_rate": 88.9,
        "recent_form": [122, 42, 65, 18, 83],
        "fantasy_points_avg": 82.7,
        "ownership": 74.1,
        "price": 10.0,
        "matches_played": 231,
    },
    {
        "name": "Mitchell Starc",
        "role": "Bowler",
        "team": "Australia",
        "bowling_avg": 22.5,
        "economy": 5.1,
        "recent_wickets": [5, 2, 3, 1, 4],
        "fantasy_points_avg": 80.3,
        "ownership": 63.8,
        "price": 9.5,
        "matches_played": 105,
    },
    {
        "name": "David Warner",
        "role": "Batsman",
        "team": "Australia",
        "batting_avg": 45.2,
        "strike_rate": 96.7,
        "recent_form": [85, 24, 103, 56, 12],
        "fantasy_points_avg": 78.9,
        "ownership": 59.2,
        "price": 9.5,
        "matches_played": 138,
    },
    {
        "name": "Kagiso Rabada",
        "role": "Bowler",
        "team": "South Africa",
        "bowling_avg": 23.7,
        "economy": 4.9,
        "recent_wickets": [3, 2, 4, 2, 1],
        "fantasy_points_avg": 75.6,
        "ownership": 51.3,
        "price": 9.0,
        "matches_played": 89,
    },
    {
        "name": "Hardik Pandya",
        "role": "All-rounder",
        "team": "India",
        "batting_avg": 33.2,
        "bowling_avg": 35.6,
        "recent_form": [35, 68, 42, 15, 56],
        "recent_wickets": [1, 2, 0, 3, 1],
        "fantasy_points_avg": 76.3,
        "ownership": 62.5,
        "price": 9.0,
        "matches_played": 67,
    }
]

# Match condition data
PITCH_CONDITIONS = {
    "Mumbai": {"batting_friendly": 8, "pace_friendly": 5, "spin_friendly": 4},
    "Chennai": {"batting_friendly": 5, "pace_friendly": 3, "spin_friendly": 9},
    "Kolkata": {"batting_friendly": 7, "pace_friendly": 6, "spin_friendly": 6},
    "Delhi": {"batting_friendly": 6, "pace_friendly": 7, "spin_friendly": 5},
    "Bangalore": {"batting_friendly": 9, "pace_friendly": 4, "spin_friendly": 3},
    "Hyderabad": {"batting_friendly": 7, "pace_friendly": 5, "spin_friendly": 7},
    "Punjab": {"batting_friendly": 8, "pace_friendly": 6, "spin_friendly": 4},
    "Rajasthan": {"batting_friendly": 6, "pace_friendly": 5, "spin_friendly": 8}
}

# Convert to pandas DataFrame
players_df = pd.DataFrame(PLAYER_DATA)

def get_player_stats(player_name):
    """Get detailed stats for a specific player"""
    player = players_df[players_df['name'].str.lower() == player_name.lower()]
    if player.empty:
        # Try partial match
        player = players_df[players_df['name'].str.lower().str.contains(player_name.lower())]
    
    if not player.empty:
        return player.iloc[0].to_dict()
    return None

def get_player_form(player_name):
    """Get the current form of a player"""
    player = get_player_stats(player_name)
    if player:
        if 'recent_form' in player:
            avg_form = sum(player['recent_form']) / len(player['recent_form'])
            if avg_form > 60:
                return "excellent"
            elif avg_form > 40:
                return "good"
            elif avg_form > 25:
                return "average"
            else:
                return "poor"
        elif 'recent_wickets' in player:
            avg_wickets = sum(player['recent_wickets']) / len(player['recent_wickets'])
            if avg_wickets > 3:
                return "excellent"
            elif avg_wickets > 2:
                return "good"
            elif avg_wickets > 1:
                return "average"
            else:
                return "poor"
    return None

def get_recommended_players(role=None, venue=None, team=None, budget=None, count=3):
    """Get recommended players based on criteria"""
    filtered_df = players_df.copy()
    
    if role:
        filtered_df = filtered_df[filtered_df['role'] == role]
    
    if team:
        filtered_df = filtered_df[filtered_df['team'] == team]
    
    if budget:
        filtered_df = filtered_df[filtered_df['price'] <= float(budget)]
    
    # Apply venue-based adjustments if venue is provided
    if venue and venue in PITCH_CONDITIONS:
        conditions = PITCH_CONDITIONS[venue]
        
        # Adjust recommendations based on pitch conditions
        if role == "Batsman" and conditions["batting_friendly"] > 7:
            filtered_df = filtered_df.sort_values(by=['batting_avg', 'fantasy_points_avg'], ascending=False)
        elif role == "Bowler" and conditions["pace_friendly"] > 7:
            # Assuming pace bowlers have lower economy
            filtered_df = filtered_df.sort_values(by=['bowling_avg', 'fantasy_points_avg'], ascending=[True, False])
        elif role == "Bowler" and conditions["spin_friendly"] > 7:
            # For spin-friendly pitches - just a simplification
            filtered_df = filtered_df.sort_values(by=['fantasy_points_avg', 'bowling_avg'], ascending=[False, True])
        else:
            # Default sorting by fantasy points
            filtered_df = filtered_df.sort_values(by='fantasy_points_avg', ascending=False)
    else:
        # Default sorting by fantasy points
        filtered_df = filtered_df.sort_values(by='fantasy_points_avg', ascending=False)
    
    # Return top N recommendations
    recommendations = filtered_df.head(count).to_dict('records')
    return recommendations

# Function to get upcoming match details (simulation)
def get_upcoming_matches():
    matches = [
        {"teams": "India vs Australia", "venue": "Mumbai", "date": "Tomorrow"},
        {"teams": "England vs South Africa", "venue": "Chennai", "date": "Day after tomorrow"},
        {"teams": "New Zealand vs Pakistan", "venue": "Delhi", "date": "Next week"}
    ]
    return matches
