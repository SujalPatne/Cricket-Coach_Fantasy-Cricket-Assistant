"""
Cricket API Client for fetching real-time cricket data
"""

import requests
import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from config import CRICKET_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

# API Base URL
API_BASE_URL = "https://api.cricapi.com/v1"

# Cache directory
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache expiration times (in seconds)
CACHE_EXPIRY = {
    "matches": 15 * 60,  # 15 minutes
    "players": 24 * 60 * 60,  # 24 hours
    "player_stats": 6 * 60 * 60,  # 6 hours
    "match_stats": 30 * 60,  # 30 minutes
    "series": 24 * 60 * 60,  # 24 hours
}

def get_cache_file_path(endpoint: str, params: Dict[str, Any] = None) -> str:
    """Get the cache file path for an API endpoint with parameters"""
    if params:
        # Create a string representation of params for the filename
        params_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items())])
        return os.path.join(CACHE_DIR, f"{endpoint}_{params_str}.json")
    return os.path.join(CACHE_DIR, f"{endpoint}.json")

def is_cache_valid(cache_file: str, endpoint_type: str) -> bool:
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

def save_to_cache(data: Dict[str, Any], cache_file: str) -> None:
    """Save data to cache file"""
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")

def load_from_cache(cache_file: str) -> Optional[Dict[str, Any]]:
    """Load data from cache file"""
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading from cache: {str(e)}")
        return None

def make_api_request(endpoint: str, params: Dict[str, Any] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Make an API request to CricAPI with caching
    
    Parameters:
    - endpoint: API endpoint (e.g., 'currentMatches', 'playerStats')
    - params: Additional parameters for the API request
    - force_refresh: Whether to force a refresh from the API instead of using cache
    
    Returns:
    - API response as a dictionary
    """
    # Determine endpoint type for cache expiry
    endpoint_type = endpoint.split('/')[0] if '/' in endpoint else endpoint
    if endpoint_type == 'currentMatches' or endpoint_type == 'matches':
        endpoint_type = 'matches'
    elif endpoint_type == 'players' or endpoint_type == 'player':
        endpoint_type = 'players'
    elif endpoint_type == 'playerStats':
        endpoint_type = 'player_stats'
    elif endpoint_type == 'match_info' or endpoint_type == 'matchStats':
        endpoint_type = 'match_stats'
    
    # Get cache file path
    cache_file = get_cache_file_path(endpoint, params)
    
    # Check if we can use cache
    if not force_refresh and is_cache_valid(cache_file, endpoint_type):
        logger.info(f"Loading {endpoint} from cache")
        cached_data = load_from_cache(cache_file)
        if cached_data:
            return cached_data
    
    # If no valid cache, make API request
    logger.info(f"Fetching {endpoint} from API")
    
    # Prepare request parameters
    request_params = {
        "apikey": CRICKET_API_KEY
    }
    if params:
        request_params.update(params)
    
    # Make the request
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        response = requests.get(url, params=request_params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Check if API request was successful
        if data.get("status") != "success":
            error_msg = data.get("message", "Unknown API error")
            logger.error(f"API error: {error_msg}")
            
            # If we have cached data, use it as fallback
            if os.path.exists(cache_file):
                logger.info(f"Using cached data as fallback for {endpoint}")
                cached_data = load_from_cache(cache_file)
                if cached_data:
                    return cached_data
            
            # Return error response
            return {
                "status": "error",
                "message": error_msg,
                "data": []
            }
        
        # Save successful response to cache
        save_to_cache(data, cache_file)
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        
        # If we have cached data, use it as fallback
        if os.path.exists(cache_file):
            logger.info(f"Using cached data as fallback for {endpoint}")
            cached_data = load_from_cache(cache_file)
            if cached_data:
                return cached_data
        
        # Return error response
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

# API Functions

def get_current_matches() -> List[Dict[str, Any]]:
    """Get current/live cricket matches"""
    response = make_api_request("currentMatches")
    
    if response.get("status") == "success":
        return response.get("data", [])
    return []

def get_upcoming_matches() -> List[Dict[str, Any]]:
    """Get upcoming cricket matches"""
    # Set date range for upcoming matches (next 7 days)
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    response = make_api_request("matches", {
        "date": f"{today},{next_week}"
    })
    
    if response.get("status") == "success":
        # Filter to only include upcoming matches
        matches = response.get("data", [])
        return [m for m in matches if m.get("matchStatus") == "upcoming"]
    return []

def search_players(name: str) -> List[Dict[str, Any]]:
    """Search for players by name"""
    response = make_api_request("players", {
        "search": name
    })
    
    if response.get("status") == "success":
        return response.get("data", [])
    return []

def get_player_stats(player_id: str) -> Dict[str, Any]:
    """Get detailed stats for a player by ID"""
    response = make_api_request("playerStats", {
        "id": player_id
    })
    
    if response.get("status") == "success":
        return response.get("data", {})
    return {}

def get_match_info(match_id: str) -> Dict[str, Any]:
    """Get detailed information about a match by ID"""
    response = make_api_request("match_info", {
        "id": match_id
    })
    
    if response.get("status") == "success":
        return response.get("data", {})
    return {}

def get_series_info(series_id: str) -> Dict[str, Any]:
    """Get information about a series by ID"""
    response = make_api_request("series_info", {
        "id": series_id
    })
    
    if response.get("status") == "success":
        return response.get("data", {})
    return {}
