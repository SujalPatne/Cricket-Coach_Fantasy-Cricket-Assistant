"""
Configuration for pytest fixtures and shared test resources.
"""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application modules
from config import TEST_MODE

@pytest.fixture
def sample_cricsheet_data():
    """Fixture providing sample Cricsheet match data for testing."""
    return {
        "meta": {
            "data_version": "1.1.0",
            "created": "2022-01-01",
            "revision": 1
        },
        "info": {
            "balls_per_over": 6,
            "city": "Mumbai",
            "dates": ["2022-01-01"],
            "event": {
                "name": "IPL 2022",
                "match_number": 1
            },
            "gender": "male",
            "match_type": "T20",
            "officials": {
                "match_referees": ["Referee Name"],
                "reserve_umpires": ["Reserve Umpire"],
                "tv_umpires": ["TV Umpire"],
                "umpires": ["Umpire 1", "Umpire 2"]
            },
            "outcome": {
                "winner": "Team A",
                "by": {
                    "runs": 25
                }
            },
            "overs": 20,
            "player_of_match": ["Player Name"],
            "players": {
                "Team A": ["Player 1", "Player 2", "Player 3", "Player 4", "Player 5", 
                           "Player 6", "Player 7", "Player 8", "Player 9", "Player 10", "Player 11"],
                "Team B": ["Player 12", "Player 13", "Player 14", "Player 15", "Player 16", 
                           "Player 17", "Player 18", "Player 19", "Player 20", "Player 21", "Player 22"]
            },
            "registry": {
                "people": {
                    "Player 1": "Virat Kohli",
                    "Player 12": "Rohit Sharma"
                }
            },
            "season": "2022",
            "team_type": "club",
            "teams": ["Team A", "Team B"],
            "toss": {
                "decision": "bat",
                "winner": "Team A"
            },
            "venue": "Wankhede Stadium"
        },
        "innings": [
            {
                "team": "Team A",
                "overs": [
                    {
                        "over": 0,
                        "deliveries": [
                            {
                                "batter": "Player 1",
                                "bowler": "Player 12",
                                "non_striker": "Player 2",
                                "runs": {
                                    "batter": 4,
                                    "extras": 0,
                                    "total": 4
                                }
                            },
                            {
                                "batter": "Player 1",
                                "bowler": "Player 12",
                                "non_striker": "Player 2",
                                "runs": {
                                    "batter": 0,
                                    "extras": 0,
                                    "total": 0
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "team": "Team B",
                "overs": [
                    {
                        "over": 0,
                        "deliveries": [
                            {
                                "batter": "Player 12",
                                "bowler": "Player 1",
                                "non_striker": "Player 13",
                                "runs": {
                                    "batter": 1,
                                    "extras": 0,
                                    "total": 1
                                }
                            },
                            {
                                "batter": "Player 13",
                                "bowler": "Player 1",
                                "non_striker": "Player 12",
                                "wicket": {
                                    "player_out": "Player 13",
                                    "kind": "bowled",
                                    "fielders": []
                                },
                                "runs": {
                                    "batter": 0,
                                    "extras": 0,
                                    "total": 0
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

@pytest.fixture
def sample_cricbuzz_live_match():
    """Fixture providing sample Cricbuzz live match data for testing."""
    return {
        "match_id": "12345",
        "series_id": "54321",
        "series_name": "IPL 2023",
        "match_description": "1st Match",
        "match_format": "T20",
        "match_status": "Live",
        "status_note": "Team A needs 50 runs in 30 balls",
        "teams": {
            "home": {
                "id": "101",
                "name": "Team A",
                "short_name": "TA",
                "logo_url": "https://example.com/teama_logo.png"
            },
            "away": {
                "id": "102",
                "name": "Team B",
                "short_name": "TB",
                "logo_url": "https://example.com/teamb_logo.png"
            }
        },
        "venue": {
            "name": "Wankhede Stadium",
            "location": "Mumbai",
            "country": "India"
        },
        "toss": {
            "winner": "Team B",
            "decision": "bat"
        },
        "current_innings": 2,
        "innings": [
            {
                "innings_number": 1,
                "team": "Team B",
                "score": 180,
                "wickets": 6,
                "overs": 20.0,
                "run_rate": 9.0
            },
            {
                "innings_number": 2,
                "team": "Team A",
                "score": 131,
                "wickets": 3,
                "overs": 15.0,
                "run_rate": 8.73,
                "required_run_rate": 10.0
            }
        ],
        "players": {
            "Team A": [
                {"id": "1001", "name": "Virat Kohli", "role": "Batsman", "batting_style": "Right-handed", "bowling_style": "Right-arm medium"},
                {"id": "1002", "name": "Ravindra Jadeja", "role": "All-rounder", "batting_style": "Left-handed", "bowling_style": "Left-arm orthodox"}
            ],
            "Team B": [
                {"id": "2001", "name": "Rohit Sharma", "role": "Batsman", "batting_style": "Right-handed", "bowling_style": "Right-arm off break"},
                {"id": "2002", "name": "Jasprit Bumrah", "role": "Bowler", "batting_style": "Right-handed", "bowling_style": "Right-arm fast"}
            ]
        },
        "current_batsmen": [
            {"id": "1001", "name": "Virat Kohli", "runs": 75, "balls": 50, "fours": 6, "sixes": 3, "strike_rate": 150.0},
            {"id": "1002", "name": "Ravindra Jadeja", "runs": 25, "balls": 15, "fours": 2, "sixes": 1, "strike_rate": 166.67}
        ],
        "current_bowler": {"id": "2002", "name": "Jasprit Bumrah", "overs": 3.0, "maidens": 0, "runs": 25, "wickets": 1, "economy": 8.33},
        "last_wicket": {"player_name": "Player 3", "runs": 15, "balls": 10, "dismissal_type": "caught", "bowler": "Jasprit Bumrah"},
        "last_five_overs": [10, 12, 8, 15, 9],
        "match_time": "2023-04-15T14:00:00Z",
        "last_updated": "2023-04-15T15:45:00Z"
    }

@pytest.fixture
def sample_player_stats():
    """Fixture providing sample aggregated player statistics for testing."""
    return {
        "Virat Kohli": {
            "batting": {
                "matches": 100,
                "innings": 95,
                "runs": 3500,
                "balls_faced": 2500,
                "highest_score": 113,
                "average": 45.5,
                "strike_rate": 140.0,
                "not_outs": 15,
                "fours": 300,
                "sixes": 120,
                "ducks": 5,
                "fifties": 25,
                "hundreds": 5,
                "recent_scores": [45, 67, 12, 89, 33],
                "recent_form": "Good",
                "variance": 28.5,
                "risk_level": "Medium"
            },
            "bowling": {
                "matches": 100,
                "innings": 20,
                "balls_bowled": 240,
                "runs_conceded": 360,
                "wickets": 10,
                "best_bowling": "2/15",
                "average": 36.0,
                "economy_rate": 9.0,
                "strike_rate": 24.0,
                "recent_wickets": [0, 1, 0, 0, 0],
                "recent_form": "Poor",
                "variance": 0.4,
                "risk_level": "Low"
            },
            "fantasy_points": {
                "average": 75.5,
                "last_5_matches": [65, 85, 40, 110, 60],
                "variance": 25.5,
                "captain_rating": 8.5,
                "vice_captain_rating": 9.0,
                "risk_level": "Medium"
            },
            "team": "Royal Challengers Bangalore",
            "role": "Batsman",
            "batting_style": "Right-handed",
            "bowling_style": "Right-arm medium",
            "last_updated": "2023-04-15"
        },
        "Jasprit Bumrah": {
            "batting": {
                "matches": 80,
                "innings": 30,
                "runs": 120,
                "balls_faced": 100,
                "highest_score": 16,
                "average": 8.0,
                "strike_rate": 120.0,
                "not_outs": 15,
                "fours": 10,
                "sixes": 5,
                "ducks": 8,
                "fifties": 0,
                "hundreds": 0,
                "recent_scores": [0, 6, 2, 0, 4],
                "recent_form": "Poor",
                "variance": 2.5,
                "risk_level": "Low"
            },
            "bowling": {
                "matches": 80,
                "innings": 80,
                "balls_bowled": 1800,
                "runs_conceded": 2000,
                "wickets": 95,
                "best_bowling": "5/10",
                "average": 21.05,
                "economy_rate": 6.67,
                "strike_rate": 18.95,
                "recent_wickets": [3, 2, 1, 4, 2],
                "recent_form": "Excellent",
                "variance": 1.1,
                "risk_level": "Low"
            },
            "fantasy_points": {
                "average": 85.0,
                "last_5_matches": [95, 75, 60, 110, 80],
                "variance": 18.5,
                "captain_rating": 7.5,
                "vice_captain_rating": 8.0,
                "risk_level": "Low"
            },
            "team": "Mumbai Indians",
            "role": "Bowler",
            "batting_style": "Right-handed",
            "bowling_style": "Right-arm fast",
            "last_updated": "2023-04-15"
        }
    }

@pytest.fixture
def mock_gemini_response():
    """Fixture providing a mock Gemini API response for testing."""
    mock_response = MagicMock()
    mock_response.text = """
    Based on the current match situation and player statistics, here are my recommendations:

    **Top Batsmen Picks:**
    1. Virat Kohli (RCB) - Currently in excellent form with an average of 45.5 and strike rate of 140.0. Risk Level: Medium
    2. Rohit Sharma (MI) - Consistent performer with good record at this venue. Risk Level: Low

    **Top Bowlers Picks:**
    1. Jasprit Bumrah (MI) - Economy of 6.67 and taking wickets consistently. Risk Level: Low
    2. Yuzvendra Chahal (RR) - Spin-friendly conditions favor his bowling style. Risk Level: Medium

    **All-rounders:**
    1. Ravindra Jadeja (CSK) - Contributes with both bat and ball. Risk Level: Low
    2. Andre Russell (KKR) - High ceiling but inconsistent. Risk Level: High

    **Captain/Vice-Captain Recommendations:**
    - Captain: Virat Kohli (2x points) - Currently batting and in good touch
    - Vice-Captain: Jasprit Bumrah (1.5x points) - Likely to bowl at death overs

    **Fantasy Point Breakdown (Last Match):**
    - Virat Kohli: 89 runs (89 pts) + 1 catch (10 pts) = 99 pts
    - Jasprit Bumrah: 3 wickets (75 pts) + 1 maiden (5 pts) + 4 runs (4 pts) = 84 pts
    """
    return mock_response

@pytest.fixture
def mock_cricbuzz_api():
    """Fixture providing a mock for the Cricbuzz API client."""
    with patch('cricbuzz_client.CricbuzzClient') as MockCricbuzzClient:
        mock_client = MagicMock()
        
        # Mock the get_live_matches method
        mock_client.get_live_matches.return_value = [
            {
                "match_id": "12345",
                "series_name": "IPL 2023",
                "match_format": "T20",
                "match_status": "Live",
                "teams": {
                    "home": {"name": "Team A"},
                    "away": {"name": "Team B"}
                },
                "venue": {"name": "Wankhede Stadium"}
            }
        ]
        
        # Mock the get_match_details method
        with open(os.path.join(os.path.dirname(__file__), 'test_data/sample_match.json'), 'r') as f:
            mock_client.get_match_details.return_value = json.load(f)
        
        # Mock the get_player_stats method
        with open(os.path.join(os.path.dirname(__file__), 'test_data/sample_player.json'), 'r') as f:
            mock_client.get_player_stats.return_value = json.load(f)
        
        MockCricbuzzClient.return_value = mock_client
        yield mock_client

# Create test directories if they don't exist
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment by creating necessary directories."""
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Create sample test data files if they don't exist
    sample_match_path = os.path.join(test_data_dir, 'sample_match.json')
    if not os.path.exists(sample_match_path):
        with open(sample_match_path, 'w') as f:
            json.dump({
                "match_id": "12345",
                "series_name": "IPL 2023",
                "match_format": "T20",
                "match_status": "Live",
                "teams": {
                    "home": {"name": "Team A"},
                    "away": {"name": "Team B"}
                },
                "venue": {"name": "Wankhede Stadium"}
            }, f)
    
    sample_player_path = os.path.join(test_data_dir, 'sample_player.json')
    if not os.path.exists(sample_player_path):
        with open(sample_player_path, 'w') as f:
            json.dump({
                "id": "1001",
                "name": "Virat Kohli",
                "team": "Royal Challengers Bangalore",
                "role": "Batsman",
                "batting_stats": {
                    "matches": 100,
                    "runs": 3500,
                    "average": 45.5,
                    "strike_rate": 140.0
                }
            }, f)
    
    yield
    
    # Cleanup can be added here if needed
