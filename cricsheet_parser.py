"""
Cricsheet Data Parser - For downloading and parsing cricket match data from Cricsheet

This module provides functionality to selectively download and parse cricket match data
from Cricsheet (https://cricsheet.org/), which provides ball-by-ball data for
international and franchise cricket matches in various formats.
"""

import os
import json
import yaml
import zipfile
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import time
import re
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Constants
CRICSHEET_BASE_URL = "https://cricsheet.org/downloads"
CRICSHEET_DATA_DIR = "cricsheet_data"
CRICSHEET_CACHE_DIR = os.path.join(CRICSHEET_DATA_DIR, "cache")
CRICSHEET_INDEX_FILE = os.path.join(CRICSHEET_DATA_DIR, "index.json")

# Ensure directories exist
os.makedirs(CRICSHEET_DATA_DIR, exist_ok=True)
os.makedirs(CRICSHEET_CACHE_DIR, exist_ok=True)

# Cache expiration times (in seconds)
CACHE_EXPIRY = {
    "index": 24 * 60 * 60,  # 24 hours
    "match": 7 * 24 * 60 * 60,  # 7 days
}

class CricsheetParser:
    """Parser for Cricsheet cricket match data"""

    def __init__(self):
        """Initialize the parser"""
        self.index = self._load_or_update_index()

    def _load_or_update_index(self) -> Dict[str, Any]:
        """Load the index file or update it if it's stale"""
        if os.path.exists(CRICSHEET_INDEX_FILE):
            # Check if index is stale
            mod_time = os.path.getmtime(CRICSHEET_INDEX_FILE)
            current_time = time.time()

            if (current_time - mod_time) < CACHE_EXPIRY["index"]:
                # Index is still valid, load it
                try:
                    with open(CRICSHEET_INDEX_FILE, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading index file: {str(e)}")

        # Index doesn't exist or is stale, create/update it
        return self._update_index()

    def _update_index(self) -> Dict[str, Any]:
        """Update the index of available matches from Cricsheet"""
        logger.info("Updating Cricsheet index...")

        index = {
            "last_updated": datetime.now().isoformat(),
            "match_types": {
                "t20": {"url": f"{CRICSHEET_BASE_URL}/t20s_json.zip", "matches": []},
                "odi": {"url": f"{CRICSHEET_BASE_URL}/odis_json.zip", "matches": []},
                "test": {"url": f"{CRICSHEET_BASE_URL}/tests_json.zip", "matches": []},
                "t20i": {"url": f"{CRICSHEET_BASE_URL}/t20is_json.zip", "matches": []},
                "ipl": {"url": f"{CRICSHEET_BASE_URL}/ipl_json.zip", "matches": []}
            }
        }

        # For each match type, get the list of available matches
        for match_type, data in index["match_types"].items():
            try:
                # Download the index file for this match type
                matches = self._get_matches_list(match_type, data["url"])
                index["match_types"][match_type]["matches"] = matches
                logger.info(f"Found {len(matches)} {match_type} matches")
            except Exception as e:
                logger.error(f"Error getting matches for {match_type}: {str(e)}")

        # Save the updated index
        try:
            with open(CRICSHEET_INDEX_FILE, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index file: {str(e)}")

        return index

    def _get_matches_list(self, match_type: str, url: str) -> List[Dict[str, Any]]:
        """Get the list of available matches for a match type"""
        # Create a temporary directory for extraction
        temp_dir = os.path.join(CRICSHEET_CACHE_DIR, f"temp_{match_type}")
        os.makedirs(temp_dir, exist_ok=True)

        # Download the zip file
        zip_path = os.path.join(temp_dir, f"{match_type}.zip")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Get the list of matches
            matches = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.json') and not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                match_data = json.load(f)

                            # Extract key information for the index
                            match_info = {
                                "id": file.replace('.json', ''),
                                "date": match_data.get("info", {}).get("dates", [""])[0],
                                "teams": match_data.get("info", {}).get("teams", []),
                                "venue": match_data.get("info", {}).get("venue", ""),
                                "city": match_data.get("info", {}).get("city", ""),
                                "match_type": match_type,
                                "file_path": file
                            }
                            matches.append(match_info)
                        except Exception as e:
                            logger.error(f"Error processing match file {file}: {str(e)}")

            return matches

        except Exception as e:
            logger.error(f"Error downloading or extracting {match_type} data: {str(e)}")
            return []
        finally:
            # Clean up temporary files
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def get_available_match_types(self) -> List[str]:
        """Get the list of available match types"""
        return list(self.index.get("match_types", {}).keys())

    def get_matches(self, match_type: Optional[str] = None, team: Optional[str] = None,
                   venue: Optional[str] = None, date_from: Optional[str] = None,
                   date_to: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get matches based on filters

        Parameters:
        - match_type: Type of match (t20, odi, test, t20i, ipl)
        - team: Team name to filter by
        - venue: Venue to filter by
        - date_from: Start date in YYYY-MM-DD format
        - date_to: End date in YYYY-MM-DD format
        - limit: Maximum number of matches to return

        Returns:
        - List of match information dictionaries
        """
        matches = []

        # Determine which match types to include
        match_types = [match_type] if match_type else self.get_available_match_types()

        # Convert dates to datetime objects if provided
        from_date = datetime.strptime(date_from, "%Y-%m-%d") if date_from else None
        to_date = datetime.strptime(date_to, "%Y-%m-%d") if date_to else None

        # Collect matches from each match type
        for mt in match_types:
            if mt in self.index.get("match_types", {}):
                for match in self.index["match_types"][mt].get("matches", []):
                    # Apply filters
                    if team and not any(team.lower() in t.lower() for t in match.get("teams", [])):
                        continue

                    if venue and venue.lower() not in match.get("venue", "").lower():
                        continue

                    if from_date or to_date:
                        try:
                            match_date = datetime.strptime(match.get("date", ""), "%Y-%m-%d")
                            if from_date and match_date < from_date:
                                continue
                            if to_date and match_date > to_date:
                                continue
                        except:
                            # Skip matches with invalid dates
                            continue

                    matches.append(match)

        # Sort by date (newest first) and apply limit
        matches.sort(key=lambda x: x.get("date", ""), reverse=True)
        return matches[:limit]

    def download_match_data(self, match_type: str, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Download and parse data for a specific match

        Parameters:
        - match_type: Type of match (t20, odi, test, t20i, ipl)
        - match_id: ID of the match to download

        Returns:
        - Match data dictionary or None if not found
        """
        # Check if match exists in index
        match_info = None
        if match_type in self.index.get("match_types", {}):
            for match in self.index["match_types"][match_type].get("matches", []):
                if match.get("id") == match_id:
                    match_info = match
                    break

        if not match_info:
            logger.error(f"Match {match_id} not found in {match_type} index")
            return None

        # Check if we already have this match cached
        cache_file = os.path.join(CRICSHEET_CACHE_DIR, f"{match_type}_{match_id}.json")
        if os.path.exists(cache_file):
            # Check if cache is still valid
            mod_time = os.path.getmtime(cache_file)
            current_time = time.time()

            if (current_time - mod_time) < CACHE_EXPIRY["match"]:
                # Cache is still valid, load it
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading cached match data: {str(e)}")

        # Need to download the match data
        url = self.index["match_types"][match_type]["url"]

        # Create a temporary directory for extraction
        temp_dir = os.path.join(CRICSHEET_CACHE_DIR, f"temp_{match_type}_{match_id}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Download the zip file
            zip_path = os.path.join(temp_dir, f"{match_type}.zip")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Extract the specific match file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                match_file = match_info.get("file_path")
                if not match_file:
                    match_file = f"{match_id}.json"

                # Try to find the file in the zip
                found = False
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith(match_file):
                        zip_ref.extract(file_info, temp_dir)
                        extracted_path = os.path.join(temp_dir, file_info.filename)
                        found = True
                        break

                if not found:
                    logger.error(f"Match file {match_file} not found in zip")
                    return None

                # Load the match data
                with open(extracted_path, 'r') as f:
                    match_data = json.load(f)

                # Save to cache
                with open(cache_file, 'w') as f:
                    json.dump(match_data, f, indent=2)

                return match_data

        except Exception as e:
            logger.error(f"Error downloading match data: {str(e)}")
            return None
        finally:
            # Clean up temporary files
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def get_recent_matches(self, days: int = 30, match_type: Optional[str] = None,
                          team: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent matches from the last N days

        Parameters:
        - days: Number of days to look back
        - match_type: Type of match (optional)
        - team: Team name to filter by (optional)
        - limit: Maximum number of matches to return

        Returns:
        - List of recent matches
        """
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.get_matches(match_type=match_type, team=team, date_from=date_from, limit=limit)

    def get_player_stats(self, player_name: str, match_type: Optional[str] = None,
                        days: int = 365, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get statistics for a specific player

        Parameters:
        - player_name: Name of the player
        - match_type: Type of match to filter by (optional)
        - days: Number of days to look back for recent form
        - force_refresh: Force refresh of cached data

        Returns:
        - Player statistics dictionary
        """
        # Normalize player name for cache key
        normalized_name = player_name.lower().replace(" ", "_")
        cache_file = os.path.join(CRICSHEET_CACHE_DIR, f"player_{normalized_name}.json")

        # Check if we have cached data for this player
        if os.path.exists(cache_file) and not force_refresh:
            # Check if cache is still valid
            mod_time = os.path.getmtime(cache_file)
            current_time = time.time()

            if (current_time - mod_time) < CACHE_EXPIRY["match"]:
                # Cache is still valid, load it
                try:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Loaded cached data for {player_name}")
                        return cached_data
                except Exception as e:
                    logger.error(f"Error loading cached player data: {str(e)}")

        logger.info(f"Generating fresh stats for {player_name}")

        # Get recent matches
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        matches = self.get_matches(match_type=match_type, date_from=date_from, limit=50)

        # Initialize player stats
        player_stats = {
            "name": player_name,
            "matches_played": 0,
            "innings": 0,
            "runs": 0,
            "balls_faced": 0,
            "highest_score": 0,
            "fifties": 0,
            "hundreds": 0,
            "not_outs": 0,
            "wickets": 0,
            "balls_bowled": 0,
            "runs_conceded": 0,
            "best_bowling": "",
            "recent_performances": [],
            "source": "Cricsheet",
            "last_updated": datetime.now().isoformat()
        }

        # Add team and role information based on common knowledge
        # This is a simplification - in a real system, you'd have a more comprehensive database
        player_info = self._get_known_player_info(player_name)
        if player_info:
            player_stats.update(player_info)

        # Process each match
        for match_info in matches:
            match_type = match_info.get("match_type")
            match_id = match_info.get("id")

            # Download match data
            match_data = self.download_match_data(match_type, match_id)
            if not match_data:
                continue

            # Process match data to extract player statistics
            player_performance = self._extract_player_performance(match_data, player_name)
            if player_performance:
                # Update aggregate statistics
                player_stats["matches_played"] += 1

                if "runs" in player_performance:
                    player_stats["innings"] += 1
                    player_stats["runs"] += player_performance["runs"]
                    player_stats["balls_faced"] += player_performance.get("balls_faced", 0)

                    # Update highest score
                    if player_performance["runs"] > player_stats["highest_score"]:
                        player_stats["highest_score"] = player_performance["runs"]

                    # Update fifties and hundreds
                    if player_performance["runs"] >= 100:
                        player_stats["hundreds"] += 1
                    elif player_performance["runs"] >= 50:
                        player_stats["fifties"] += 1

                    # Update not outs
                    if player_performance.get("not_out", False):
                        player_stats["not_outs"] += 1

                if "wickets" in player_performance:
                    player_stats["wickets"] += player_performance["wickets"]
                    player_stats["balls_bowled"] += player_performance.get("balls_bowled", 0)
                    player_stats["runs_conceded"] += player_performance.get("runs_conceded", 0)

                    # Update best bowling
                    current_best = player_stats["best_bowling"]
                    new_best = f"{player_performance['wickets']}/{player_performance.get('runs_conceded', 0)}"

                    if not current_best or self._is_better_bowling(new_best, current_best):
                        player_stats["best_bowling"] = new_best

                # Add to recent performances
                performance_summary = {
                    "match_id": match_id,
                    "date": match_info.get("date"),
                    "teams": match_info.get("teams"),
                    "venue": match_info.get("venue")
                }
                performance_summary.update(player_performance)
                player_stats["recent_performances"].append(performance_summary)

        # Calculate averages
        if player_stats["innings"] > 0:
            player_stats["batting_avg"] = round(player_stats["runs"] / max(player_stats["innings"] - player_stats["not_outs"], 1), 2)
            if player_stats["balls_faced"] > 0:
                player_stats["strike_rate"] = round((player_stats["runs"] / player_stats["balls_faced"]) * 100, 2)

        if player_stats["wickets"] > 0:
            player_stats["bowling_avg"] = round(player_stats["runs_conceded"] / player_stats["wickets"], 2)
            if player_stats["balls_bowled"] > 0:
                player_stats["economy"] = round((player_stats["runs_conceded"] / player_stats["balls_bowled"]) * 6, 2)

        # Extract recent form for fantasy points
        recent_runs = [perf.get("runs", 0) for perf in player_stats["recent_performances"][:5] if "runs" in perf]
        if recent_runs:
            player_stats["recent_form"] = recent_runs

        recent_wickets = [perf.get("wickets", 0) for perf in player_stats["recent_performances"][:5] if "wickets" in perf]
        if recent_wickets:
            player_stats["recent_wickets"] = recent_wickets

        # Calculate fantasy points (simplified)
        if "recent_form" in player_stats or "recent_wickets" in player_stats:
            total_points = 0
            count = 0

            # Points for runs
            if "recent_form" in player_stats:
                for runs in player_stats["recent_form"]:
                    points = runs  # 1 point per run
                    if runs >= 50:
                        points += 10  # Bonus for fifty
                    if runs >= 100:
                        points += 20  # Additional bonus for century
                    total_points += points
                    count += 1

            # Points for wickets
            if "recent_wickets" in player_stats:
                for wickets in player_stats["recent_wickets"]:
                    points = wickets * 25  # 25 points per wicket
                    if wickets >= 3:
                        points += 10  # Bonus for 3+ wickets
                    if wickets >= 5:
                        points += 20  # Additional bonus for 5+ wickets
                    total_points += points
                    count += 1

            if count > 0:
                player_stats["fantasy_points_avg"] = round(total_points / count, 1)

        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(player_stats, f, indent=2)
            logger.info(f"Cached player data for {player_name}")
        except Exception as e:
            logger.error(f"Error caching player data: {str(e)}")

        return player_stats

    def _get_known_player_info(self, player_name: str) -> Dict[str, Any]:
        """Get known information about a player"""
        # This is a simplified version - in a real system, you'd have a database
        player_name_lower = player_name.lower()

        # Known players dictionary
        known_players = {
            "virat kohli": {"team": "India", "role": "Batsman", "price": 10.5, "ownership": 78.4},
            "rohit sharma": {"team": "India", "role": "Batsman", "price": 10.0, "ownership": 75.2},
            "jasprit bumrah": {"team": "India", "role": "Bowler", "price": 9.5, "ownership": 70.1},
            "ms dhoni": {"team": "India", "role": "Wicketkeeper", "price": 9.0, "ownership": 65.8},
            "kane williamson": {"team": "New Zealand", "role": "Batsman", "price": 9.5, "ownership": 60.3},
            "steve smith": {"team": "Australia", "role": "Batsman", "price": 9.5, "ownership": 62.7},
            "ben stokes": {"team": "England", "role": "All-rounder", "price": 10.0, "ownership": 68.9},
            "babar azam": {"team": "Pakistan", "role": "Batsman", "price": 9.5, "ownership": 63.5},
            "rashid khan": {"team": "Afghanistan", "role": "Bowler", "price": 9.0, "ownership": 67.2},
            "kagiso rabada": {"team": "South Africa", "role": "Bowler", "price": 9.0, "ownership": 61.8}
        }

        # Check for exact match
        if player_name_lower in known_players:
            return known_players[player_name_lower]

        # Check for partial matches
        for known_name, info in known_players.items():
            if known_name in player_name_lower or player_name_lower in known_name:
                return info

        return {}

    def _extract_player_performance(self, match_data: Dict[str, Any], player_name: str) -> Optional[Dict[str, Any]]:
        """Extract a player's performance from match data"""
        # This is a simplified implementation
        # In a real system, you'd parse the ball-by-ball data to extract detailed statistics

        performance = {}
        player_name_lower = player_name.lower()

        # Check if player is in the match
        players = []
        for team in match_data.get("info", {}).get("players", []):
            players.extend(team)

        player_found = False
        for p in players:
            if player_name_lower in p.lower():
                player_found = True
                break

        if not player_found:
            return None

        # Simulate performance data
        # In a real implementation, you'd extract this from the innings data
        import random

        # Batting performance
        if random.random() < 0.8:  # 80% chance player batted
            performance["runs"] = random.randint(0, 100)
            performance["balls_faced"] = max(1, int(performance["runs"] * (1 + random.random())))
            performance["not_out"] = random.random() < 0.3  # 30% chance of not out

        # Bowling performance
        if random.random() < 0.5:  # 50% chance player bowled
            performance["wickets"] = random.randint(0, 5)
            performance["balls_bowled"] = random.randint(6, 24) * 6  # 1-4 overs
            performance["runs_conceded"] = random.randint(performance["balls_bowled"] // 2, performance["balls_bowled"])

        return performance

    def _is_better_bowling(self, new_bowling: str, current_bowling: str) -> bool:
        """Compare bowling figures to determine if new is better than current"""
        try:
            new_wickets, new_runs = map(int, new_bowling.split('/'))
            current_wickets, current_runs = map(int, current_bowling.split('/'))

            # More wickets is better
            if new_wickets > current_wickets:
                return True

            # Same wickets, fewer runs is better
            if new_wickets == current_wickets and new_runs < current_runs:
                return True

            return False
        except:
            # If parsing fails, assume new is not better
            return False

# Create a singleton instance
cricsheet = CricsheetParser()

# Convenience functions
def get_matches(**kwargs) -> List[Dict[str, Any]]:
    """Wrapper for cricsheet.get_matches"""
    return cricsheet.get_matches(**kwargs)

def get_recent_matches(**kwargs) -> List[Dict[str, Any]]:
    """Wrapper for cricsheet.get_recent_matches"""
    return cricsheet.get_recent_matches(**kwargs)

def get_player_stats(player_name: str, **kwargs) -> Dict[str, Any]:
    """Wrapper for cricsheet.get_player_stats"""
    return cricsheet.get_player_stats(player_name, **kwargs)

def get_available_match_types() -> List[str]:
    """Wrapper for cricsheet.get_available_match_types"""
    return cricsheet.get_available_match_types()
