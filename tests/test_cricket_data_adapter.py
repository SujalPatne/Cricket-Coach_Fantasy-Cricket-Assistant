"""
Tests for the cricket_data_adapter.py module
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import module to test
from cricket_data_adapter import (
    get_live_cricket_matches,
    get_upcoming_matches,
    get_recent_matches,
    get_player_stats,
    get_player_form,
    get_recommended_players,
    get_pitch_conditions,
    get_match_details
)

class TestCricketDataAdapter(unittest.TestCase):
    """Test cases for cricket_data_adapter.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock data
        self.mock_live_matches = [
            {
                "teams": "India vs Australia",
                "venue": "Sydney Cricket Ground",
                "status": "Live: India 245/6 (45.2 ov)",
                "match_type": "ODI",
                "match_id": "12345",
                "source": "Cricbuzz"
            }
        ]
        
        self.mock_upcoming_matches = [
            {
                "teams": "England vs New Zealand",
                "venue": "Lord's",
                "date": "2023-06-15",
                "match_type": "Test",
                "source": "Cricbuzz"
            }
        ]
        
        self.mock_recent_matches = [
            {
                "teams": "Pakistan vs South Africa",
                "venue": "Lahore",
                "date": "2023-06-01",
                "status": "Pakistan won by 5 wickets",
                "match_type": "T20",
                "match_id": "67890",
                "source": "Cricbuzz"
            }
        ]
        
        self.mock_player = {
            "name": "Virat Kohli",
            "team": "India",
            "role": "Batsman",
            "batting_avg": 59.07,
            "strike_rate": 93.17,
            "recent_form": [45, 67, 112, 23, 89],
            "fantasy_points_avg": 85.5,
            "price": 10.5,
            "ownership": 78.3,
            "source": "Cricsheet"
        }
    
    @patch('cricket_data_adapter.cricbuzz')
    def test_get_live_cricket_matches(self, mock_cricbuzz):
        """Test get_live_cricket_matches function"""
        # Configure mock
        mock_cricbuzz.get_live_matches.return_value = self.mock_live_matches
        
        # Call function
        result = get_live_cricket_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['teams'], "India vs Australia")
        self.assertEqual(result[0]['source'], "Cricbuzz")
        
        # Verify mock was called
        mock_cricbuzz.get_live_matches.assert_called_once()
    
    @patch('cricket_data_adapter.cricbuzz')
    def test_get_upcoming_matches(self, mock_cricbuzz):
        """Test get_upcoming_matches function"""
        # Configure mock
        mock_cricbuzz.get_upcoming_matches.return_value = self.mock_upcoming_matches
        
        # Call function
        result = get_upcoming_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['teams'], "England vs New Zealand")
        self.assertEqual(result[0]['source'], "Cricbuzz")
        
        # Verify mock was called
        mock_cricbuzz.get_upcoming_matches.assert_called_once()
    
    @patch('cricket_data_adapter.cricbuzz')
    def test_get_recent_matches(self, mock_cricbuzz):
        """Test get_recent_matches function"""
        # Configure mock
        mock_cricbuzz.get_recent_matches.return_value = self.mock_recent_matches
        
        # Call function
        result = get_recent_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['teams'], "Pakistan vs South Africa")
        self.assertEqual(result[0]['source'], "Cricbuzz")
        
        # Verify mock was called
        mock_cricbuzz.get_recent_matches.assert_called_once()
    
    @patch('cricket_data_adapter.cricsheet')
    def test_get_player_stats(self, mock_cricsheet):
        """Test get_player_stats function"""
        # Configure mock
        mock_cricsheet.get_player_stats.return_value = self.mock_player
        
        # Call function
        result = get_player_stats("Virat Kohli")
        
        # Assertions
        self.assertEqual(result['name'], "Virat Kohli")
        self.assertEqual(result['team'], "India")
        self.assertEqual(result['role'], "Batsman")
        self.assertEqual(result['source'], "Cricsheet")
        
        # Verify mock was called
        mock_cricsheet.get_player_stats.assert_called_once_with("Virat Kohli")
    
    def test_get_player_form(self):
        """Test get_player_form function"""
        # Mock the get_player_stats function
        with patch('cricket_data_adapter.get_player_stats') as mock_get_stats:
            # Configure mock
            mock_get_stats.return_value = self.mock_player
            
            # Call function
            result = get_player_form("Virat Kohli")
            
            # Assertions
            self.assertIn(result, ["excellent", "good", "average", "poor", "unknown"])
            
            # Verify mock was called
            mock_get_stats.assert_called_once_with("Virat Kohli")
    
    def test_get_pitch_conditions(self):
        """Test get_pitch_conditions function"""
        # Call function
        result = get_pitch_conditions("Sydney Cricket Ground")
        
        # Assertions
        self.assertIn('batting_friendly', result)
        self.assertIn('pace_friendly', result)
        self.assertIn('spin_friendly', result)
        
        # Check values are in expected range
        self.assertTrue(0 <= result['batting_friendly'] <= 10)
        self.assertTrue(0 <= result['pace_friendly'] <= 10)
        self.assertTrue(0 <= result['spin_friendly'] <= 10)

if __name__ == '__main__':
    unittest.main()
