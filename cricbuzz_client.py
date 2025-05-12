"""
Cricbuzz Data Client - For fetching real-time cricket data from Cricbuzz via RapidAPI

This module provides functionality to fetch live cricket data from the Cricbuzz API via RapidAPI,
including live scores, upcoming matches, and recent matches.
"""

import os
import json
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
from config import CRICBUZZ_API_KEY, CRICBUZZ_API_HOST

# Set up logging
logger = logging.getLogger(__name__)

# Constants
CRICBUZZ_BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"
CRICBUZZ_CACHE_DIR = "cricbuzz_cache"
os.makedirs(CRICBUZZ_CACHE_DIR, exist_ok=True)

# Cache expiration times (in seconds)
CACHE_EXPIRY = {
    "live_matches": 60,  # 1 minute
    "upcoming_matches": 15 * 60,  # 15 minutes
    "recent_matches": 15 * 60,  # 15 minutes
    "match_score": 60,  # 1 minute
}

class CricbuzzClient:
    """Client for interacting with the Cricbuzz API via RapidAPI"""

    def __init__(self):
        """Initialize the client"""
        self.session = requests.Session()
        self.session.headers.update({
            "X-RapidAPI-Key": CRICBUZZ_API_KEY,
            "X-RapidAPI-Host": CRICBUZZ_API_HOST
        })

    def _get_cache_file_path(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Get the cache file path for an API endpoint with parameters"""
        if params:
            # Create a string representation of params for the filename
            params_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items())])
            return os.path.join(CRICBUZZ_CACHE_DIR, f"{endpoint}_{params_str}.json")
        return os.path.join(CRICBUZZ_CACHE_DIR, f"{endpoint}.json")

    def _is_cache_valid(self, cache_file: str, endpoint_type: str) -> bool:
        """Check if a cache file is still valid based on its modification time"""
        if not os.path.exists(cache_file):
            return False

        # Get file modification time
        mod_time = os.path.getmtime(cache_file)
        current_time = time.time()

        # Get expiry time for this endpoint type
        expiry_time = CACHE_EXPIRY.get(endpoint_type, 60 * 60)  # Default: 1 hour

        # Check if cache is still valid
        return (current_time - mod_time) < expiry_time

    def _save_to_cache(self, data: Dict[str, Any], cache_file: str) -> None:
        """Save data to cache file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")

    def _load_from_cache(self, cache_file: str) -> Optional[Dict[str, Any]]:
        """Load data from cache file"""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading from cache: {str(e)}")
            return None

    def _make_api_request(self, endpoint: str, params: Dict[str, Any] = None,
                         force_refresh: bool = False, endpoint_type: str = None) -> Dict[str, Any]:
        """
        Make an API request to Cricbuzz API via RapidAPI with caching

        Parameters:
        - endpoint: API endpoint (e.g., 'matches/v1/live')
        - params: Additional parameters for the API request
        - force_refresh: Whether to force a refresh from the API instead of using cache
        - endpoint_type: Type of endpoint for cache expiry (if different from endpoint)

        Returns:
        - API response as a dictionary
        """
        # Determine endpoint type for cache expiry
        if not endpoint_type:
            if "live" in endpoint:
                endpoint_type = "live_matches"
            elif "upcoming" in endpoint:
                endpoint_type = "upcoming_matches"
            elif "recent" in endpoint:
                endpoint_type = "recent_matches"
            elif "score" in endpoint:
                endpoint_type = "match_score"

        # Get cache file path
        cache_file = self._get_cache_file_path(endpoint, params)

        # Check if we can use cache
        if not force_refresh and self._is_cache_valid(cache_file, endpoint_type):
            logger.info(f"Loading {endpoint} from cache")
            cached_data = self._load_from_cache(cache_file)
            if cached_data:
                return cached_data

        # If no valid cache, make API request
        logger.info(f"Fetching {endpoint} from API")

        # Make the request
        try:
            url = f"{CRICBUZZ_BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors

            data = response.json()

            # Save successful response to cache
            self._save_to_cache(data, cache_file)
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")

            # If we have cached data, use it as fallback
            if os.path.exists(cache_file):
                logger.info(f"Using cached data as fallback for {endpoint}")
                cached_data = self._load_from_cache(cache_file)
                if cached_data:
                    return cached_data

            # Return error response
            return {
                "message": f"Error: {str(e)}",
                "data": {}
            }

    def get_live_matches(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get live cricket matches

        Parameters:
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - List of live matches
        """
        endpoint = "matches/v1/live"

        response = self._make_api_request(endpoint, None, force_refresh, "live_matches")

        # Process the response based on RapidAPI Cricbuzz format
        matches = []
        if isinstance(response, dict) and "typeMatches" in response:
            for match_type in response.get("typeMatches", []):
                for series_match in match_type.get("seriesMatches", []):
                    if "seriesAdWrapper" in series_match:
                        series_matches = series_match["seriesAdWrapper"].get("matches", [])
                        matches.extend(series_matches)

        return matches

    def get_upcoming_matches(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get upcoming cricket matches

        Parameters:
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - List of upcoming matches
        """
        # For upcoming matches, we'll use the matches endpoint with a filter
        endpoint = "matches/v1/upcoming"

        response = self._make_api_request(endpoint, None, force_refresh, "upcoming_matches")

        # Process the response based on RapidAPI Cricbuzz format
        matches = []

        # Handle different response formats
        if isinstance(response, dict) and "matchScheduleMap" in response:
            # Format 1: Schedule response
            for date, schedule in response.get("matchScheduleMap", {}).items():
                for match in schedule:
                    matches.append(match.get("matchInfo", {}))
        elif isinstance(response, dict) and "typeMatches" in response:
            # Format 2: Matches response
            for match_type in response.get("typeMatches", []):
                for series_match in match_type.get("seriesMatches", []):
                    if "seriesAdWrapper" in series_match:
                        series_matches = series_match["seriesAdWrapper"].get("matches", [])
                        for match in series_matches:
                            matches.append(match.get("matchInfo", match))
        elif isinstance(response, list):
            # Format 3: Direct list of matches
            for match in response:
                if "matchInfo" in match:
                    matches.append(match["matchInfo"])
                else:
                    matches.append(match)

        # Filter for upcoming matches
        current_time = int(time.time() * 1000)  # Convert to milliseconds
        upcoming_matches = []
        for match in matches:
            match_date = match.get("startDate", 0)
            if isinstance(match_date, str):
                try:
                    match_date = int(match_date)
                except:
                    match_date = 0

            if match_date > current_time:
                upcoming_matches.append(match)

        return upcoming_matches

    def get_recent_matches(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get recent cricket matches

        Parameters:
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - List of recent matches
        """
        # For recent matches, we'll use the matches endpoint with a filter
        endpoint = "matches/v1/recent"

        response = self._make_api_request(endpoint, None, force_refresh, "recent_matches")

        # Process the response based on RapidAPI Cricbuzz format
        matches = []

        # Handle different response formats
        if isinstance(response, dict) and "matchScheduleMap" in response:
            # Format 1: Schedule response
            for date, schedule in response.get("matchScheduleMap", {}).items():
                for match in schedule:
                    matches.append(match.get("matchInfo", {}))
        elif isinstance(response, dict) and "typeMatches" in response:
            # Format 2: Matches response
            for match_type in response.get("typeMatches", []):
                for series_match in match_type.get("seriesMatches", []):
                    if "seriesAdWrapper" in series_match:
                        series_matches = series_match["seriesAdWrapper"].get("matches", [])
                        for match in series_matches:
                            matches.append(match.get("matchInfo", match))
        elif isinstance(response, list):
            # Format 3: Direct list of matches
            for match in response:
                if "matchInfo" in match:
                    matches.append(match["matchInfo"])
                else:
                    matches.append(match)

        # Filter for recent matches (past matches)
        current_time = int(time.time() * 1000)  # Convert to milliseconds
        recent_matches = []
        for match in matches:
            match_date = match.get("startDate", 0)
            if isinstance(match_date, str):
                try:
                    match_date = int(match_date)
                except:
                    match_date = 0

            if match_date < current_time:
                recent_matches.append(match)

        # Sort by date (newest first) and limit to 10
        recent_matches.sort(key=lambda x: int(x.get("startDate", 0)) if isinstance(x.get("startDate", 0), (int, str)) else 0, reverse=True)
        return recent_matches[:10]

    def get_match_score(self, match_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get detailed score for a specific match

        Parameters:
        - match_id: ID of the match
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - Match score details
        """
        endpoint = f"mcenter/v1/{match_id}"

        response = self._make_api_request(endpoint, None, force_refresh, "match_score")

        return response

    def get_all_matches(self, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all matches (live, upcoming, and recent)

        Parameters:
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - Dictionary with live, upcoming, and recent matches
        """
        return {
            "live": self.get_live_matches(force_refresh),
            "upcoming": self.get_upcoming_matches(force_refresh),
            "recent": self.get_recent_matches(force_refresh)
        }

    def get_player_info(self, player_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get detailed information about a player

        Parameters:
        - player_id: ID of the player
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - Player information
        """
        # Try different endpoint formats
        endpoints = [
            f"stats/v1/player/profile/{player_id}",
            f"players/v1/{player_id}",
            f"players/v1/profile/{player_id}"
        ]

        for endpoint in endpoints:
            try:
                response = self._make_api_request(endpoint, None, force_refresh, "player_info")

                # If we got a valid response, return it
                if isinstance(response, dict) and not response.get("message", "").startswith("Error:"):
                    return response
            except Exception as e:
                logger.error(f"Error getting player info from {endpoint}: {str(e)}")

        # If all endpoints failed, return a default response
        return {
            "id": player_id,
            "name": "Unknown",
            "error": "Could not retrieve player information"
        }

    def search_players(self, query: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Search for players by name

        Parameters:
        - query: Search query (player name)
        - force_refresh: Whether to force a refresh from the API

        Returns:
        - List of matching players
        """
        endpoint = "stats/v1/player/search"
        params = {"plrN": query}

        response = self._make_api_request(endpoint, params, force_refresh, "player_search")

        if isinstance(response, dict) and "player" in response:
            return response["player"]
        return []

# Create a singleton instance
cricbuzz = CricbuzzClient()

# Convenience functions
def get_live_matches(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Wrapper for cricbuzz.get_live_matches"""
    return cricbuzz.get_live_matches(force_refresh)

def get_upcoming_matches(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Wrapper for cricbuzz.get_upcoming_matches"""
    return cricbuzz.get_upcoming_matches(force_refresh)

def get_recent_matches(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Wrapper for cricbuzz.get_recent_matches"""
    return cricbuzz.get_recent_matches(force_refresh)

def get_match_score(match_id: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Wrapper for cricbuzz.get_match_score"""
    return cricbuzz.get_match_score(match_id, force_refresh)

def get_all_matches(force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """Wrapper for cricbuzz.get_all_matches"""
    return cricbuzz.get_all_matches(force_refresh)

def get_player_info(player_id: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Wrapper for cricbuzz.get_player_info"""
    return cricbuzz.get_player_info(player_id, force_refresh)

def search_players(query: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Wrapper for cricbuzz.search_players"""
    return cricbuzz.search_players(query, force_refresh)
