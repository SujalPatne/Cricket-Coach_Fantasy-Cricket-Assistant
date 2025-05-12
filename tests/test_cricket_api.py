"""
Tests for the cricket API client
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
import cricket_api_client as api
from cricket_data_adapter import get_player_stats, get_live_cricket_matches, get_upcoming_matches

class TestCricketAPI(unittest.TestCase):
    """Test cases for cricket API client"""
    
    @patch('cricket_api_client.requests.get')
    def test_make_api_request(self, mock_get):
        """Test the make_api_request function"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": [{"name": "Test Player"}]
        }
        mock_get.return_value = mock_response
        
        # Call the function
        result = api.make_api_request("players", {"search": "Test"}, force_refresh=True)
        
        # Assertions
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["name"], "Test Player")
        
        # Verify the API was called with correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue("apikey" in kwargs["params"])
        self.assertTrue("search" in kwargs["params"])
    
    @patch('cricket_api_client.make_api_request')
    def test_get_current_matches(self, mock_make_request):
        """Test the get_current_matches function"""
        # Mock response
        mock_make_request.return_value = {
            "status": "success",
            "data": [
                {
                    "name": "Team A vs Team B",
                    "venue": "Test Stadium",
                    "date": "2023-05-15",
                    "matchType": "t20"
                }
            ]
        }
        
        # Call the function
        result = api.get_current_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Team A vs Team B")
        
        # Verify the API was called correctly
        mock_make_request.assert_called_once_with("currentMatches")
    
    @patch('cricket_api_client.make_api_request')
    def test_get_upcoming_matches(self, mock_make_request):
        """Test the get_upcoming_matches function"""
        # Mock response
        mock_make_request.return_value = {
            "status": "success",
            "data": [
                {
                    "name": "Team C vs Team D",
                    "venue": "Another Stadium",
                    "date": "2023-05-20",
                    "matchType": "odi",
                    "matchStatus": "upcoming"
                }
            ]
        }
        
        # Call the function
        result = api.get_upcoming_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Team C vs Team D")
        
        # Verify the API was called correctly
        mock_make_request.assert_called_once()
        self.assertEqual(mock_make_request.call_args[0][0], "matches")
    
    @patch('cricket_api_client.make_api_request')
    def test_search_players(self, mock_make_request):
        """Test the search_players function"""
        # Mock response
        mock_make_request.return_value = {
            "status": "success",
            "data": [
                {
                    "id": "player123",
                    "name": "Virat Kohli",
                    "country": "India"
                }
            ]
        }
        
        # Call the function
        result = api.search_players("Kohli")
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Virat Kohli")
        
        # Verify the API was called correctly
        mock_make_request.assert_called_once_with("players", {"search": "Kohli"})
    
    @patch('cricket_api_client.make_api_request')
    def test_get_player_stats(self, mock_make_request):
        """Test the get_player_stats function"""
        # Mock response
        mock_make_request.return_value = {
            "status": "success",
            "data": {
                "id": "player123",
                "name": "Virat Kohli",
                "country": "India",
                "battingStats": {
                    "matches": 100,
                    "avg": 50.5,
                    "strikeRate": 135.7
                }
            }
        }
        
        # Call the function
        result = api.get_player_stats("player123")
        
        # Assertions
        self.assertEqual(result["name"], "Virat Kohli")
        self.assertEqual(result["battingStats"]["avg"], 50.5)
        
        # Verify the API was called correctly
        mock_make_request.assert_called_once_with("playerStats", {"id": "player123"})

class TestCricketDataAdapter(unittest.TestCase):
    """Test cases for cricket data adapter"""
    
    @patch('cricket_data_adapter.api.search_players')
    @patch('cricket_data_adapter.api.get_player_stats')
    def test_get_player_stats(self, mock_get_stats, mock_search):
        """Test the get_player_stats function in the adapter"""
        # Mock responses
        mock_search.return_value = [{"id": "player123", "name": "Virat Kohli"}]
        mock_get_stats.return_value = {
            "name": "Virat Kohli",
            "country": "India",
            "isBatsman": True,
            "isBowler": False,
            "isKeeper": False,
            "battingStats": {
                "matches": 100,
                "avg": 50.5,
                "strikeRate": 135.7
            }
        }
        
        # Call the function
        result = get_player_stats("Kohli")
        
        # Assertions
        self.assertEqual(result["name"], "Virat Kohli")
        self.assertEqual(result["team"], "India")
        self.assertEqual(result["role"], "Batsman")
        self.assertGreater(result["fantasy_points_avg"], 0)
        
        # Verify the API functions were called correctly
        mock_search.assert_called_once_with("Kohli")
        mock_get_stats.assert_called_once_with("player123")
    
    @patch('cricket_data_adapter.api.get_current_matches')
    def test_get_live_cricket_matches(self, mock_get_matches):
        """Test the get_live_cricket_matches function in the adapter"""
        # Mock response
        mock_get_matches.return_value = [
            {
                "name": "India vs Australia",
                "venue": "Mumbai",
                "date": "2023-05-15",
                "matchType": "t20",
                "teams": [
                    {"name": "India"},
                    {"name": "Australia"}
                ],
                "score": [
                    {"r": 180, "w": 4, "o": 20},
                    {"r": 160, "w": 8, "o": 19.2}
                ]
            }
        ]
        
        # Call the function
        result = get_live_cricket_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["teams"], "India vs Australia")
        self.assertEqual(result[0]["venue"], "Mumbai")
        self.assertIn("pitch_conditions", result[0])
        
        # Verify the API function was called correctly
        mock_get_matches.assert_called_once()
    
    @patch('cricket_data_adapter.api.get_upcoming_matches')
    def test_get_upcoming_matches(self, mock_get_matches):
        """Test the get_upcoming_matches function in the adapter"""
        # Mock response
        mock_get_matches.return_value = [
            {
                "name": "England vs New Zealand",
                "venue": "London",
                "date": "2023-05-20",
                "matchType": "odi",
                "teams": [
                    {"name": "England"},
                    {"name": "New Zealand"}
                ]
            }
        ]
        
        # Call the function
        result = get_upcoming_matches()
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["teams"], "England vs New Zealand")
        self.assertEqual(result[0]["venue"], "London")
        self.assertEqual(result[0]["match_type"], "ODI")
        
        # Verify the API function was called correctly
        mock_get_matches.assert_called_once()

if __name__ == '__main__':
    unittest.main()
