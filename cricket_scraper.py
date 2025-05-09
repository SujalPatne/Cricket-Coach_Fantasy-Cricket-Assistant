import trafilatura
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from datetime import datetime, timedelta

# Import data storage module
from data_storage import (
    save_cricket_players, get_cricket_players,
    save_match_data, get_match_data,
    is_data_stale, PLAYERS_DATA_FILE, MATCH_DATA_FILE
)

# Cache for storing scraped data with timestamps
data_cache = {
    "live_matches": {"data": None, "timestamp": 0},
    "players": {"data": None, "timestamp": 0},
    "upcoming_matches": {"data": None, "timestamp": 0},
    "player_rankings": {"data": None, "timestamp": 0}
}

# Cache validity period in seconds (10 minutes)
CACHE_VALIDITY = 600

def get_website_text_content(url):
    """
    Extract main text content from a website using trafilatura
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text
        return "Could not download content"
    except Exception as e:
        return f"Error extracting content: {str(e)}"

def fetch_with_beautiful_soup(url):
    """
    Fetch and parse HTML content using BeautifulSoup
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def get_live_cricket_matches():
    """
    Get information about currently live cricket matches
    """
    # Check if cache is valid
    now = time.time()
    if data_cache["live_matches"]["data"] and now - data_cache["live_matches"]["timestamp"] < CACHE_VALIDITY:
        return data_cache["live_matches"]["data"]
    
    try:
        # Fallback to text extraction if needed
        content = get_website_text_content("https://www.espncricinfo.com/live-cricket-score")
        
        # Process the content to extract match information
        matches = []
        if content:
            lines = content.split('\n')
            match_info = {}
            
            for line in lines:
                if re.search(r'vs', line) and len(line) < 100:  # Likely a team vs team line
                    if match_info and 'teams' in match_info:  # Save previous match
                        matches.append(match_info)
                    match_info = {'teams': line.strip()}
                elif match_info and 'teams' in match_info and not 'status' in match_info and re.search(r'innings|overs|wicket|run|batting', line.lower()):
                    match_info['status'] = line.strip()
                elif match_info and 'teams' in match_info and 'status' in match_info and not 'venue' in match_info and len(line.strip()) > 5:
                    match_info['venue'] = line.strip()
                    matches.append(match_info)
                    match_info = {}
            
            # Add the last match if not added
            if match_info and 'teams' in match_info:
                matches.append(match_info)
        
        # Limit to 5 matches
        matches = matches[:5]
        
        # Update cache
        data_cache["live_matches"]["data"] = matches
        data_cache["live_matches"]["timestamp"] = now
        
        return matches
    except Exception as e:
        print(f"Error fetching live matches: {str(e)}")
        # Return empty list as fallback
        return []

def get_player_stats(player_name):
    """
    Get real stats for a cricket player by name
    """
    # Check if we have stored player data
    stored_players = get_cricket_players()
    
    # Try to find player in stored data first
    if stored_players:
        for player in stored_players:
            if player.get('name', '').lower() == player_name.lower():
                return player
            
            # Try partial match
            if player_name.lower() in player.get('name', '').lower():
                return player
    
    # If we need to fetch from web (either no stored data or player not found)
    try:
        # Fetch from web
        search_content = get_website_text_content(f"https://www.espncricinfo.com/cricketers/search?term={player_name}")
        
        # Extract basic information from content
        if search_content:
            # Very basic extraction - would need refinement in a real app
            lines = search_content.split('\n')
            player_info = {}
            
            for i, line in enumerate(lines):
                if player_name.lower() in line.lower() and i < len(lines) - 5:
                    player_info['name'] = line.strip()
                    
                    # Try to extract role from next few lines
                    for j in range(1, 5):
                        if i+j < len(lines):
                            role_line = lines[i+j].lower()
                            if 'batsman' in role_line or 'batter' in role_line:
                                player_info['role'] = 'Batsman'
                                break
                            elif 'bowler' in role_line:
                                player_info['role'] = 'Bowler'
                                break
                            elif 'all-rounder' in role_line or 'allrounder' in role_line:
                                player_info['role'] = 'All-rounder'
                                break
                            elif 'wicket' in role_line or 'keeper' in role_line:
                                player_info['role'] = 'Wicketkeeper'
                                break
                    
                    # Try to extract team
                    for j in range(1, 5):
                        if i+j < len(lines):
                            team_line = lines[i+j]
                            for team in ['India', 'Australia', 'England', 'South Africa', 'New Zealand', 
                                        'Pakistan', 'Sri Lanka', 'West Indies', 'Bangladesh', 'Afghanistan']:
                                if team in team_line:
                                    player_info['team'] = team
                                    break
                            if 'team' in player_info:
                                break
                    
                    break
            
            # If we found player info, update stored data
            if player_info and 'name' in player_info:
                # Get existing player data
                players_data = get_cricket_players()
                
                # Add this player if not already in the list
                player_exists = False
                for i, player in enumerate(players_data):
                    if player.get('name', '') == player_info['name']:
                        # Update existing player
                        players_data[i] = {**player, **player_info}
                        player_exists = True
                        break
                
                if not player_exists:
                    players_data.append(player_info)
                
                # Save updated player data
                save_cricket_players(players_data)
                
                return player_info
    except Exception as e:
        print(f"Error fetching player stats: {str(e)}")
    
    # If all else fails, return data from cricket_data module
    from cricket_data import get_player_stats as get_backup_player_stats
    return get_backup_player_stats(player_name)

def get_upcoming_matches():
    """
    Get information about upcoming cricket matches
    """
    # Check if we can use stored data (if it's not stale)
    if not is_data_stale(MATCH_DATA_FILE, 3600):  # 1 hour validity
        stored_matches = get_match_data()
        if stored_matches:
            return stored_matches
    
    # Check if cache is valid
    now = time.time()
    if data_cache["upcoming_matches"]["data"] and now - data_cache["upcoming_matches"]["timestamp"] < CACHE_VALIDITY:
        return data_cache["upcoming_matches"]["data"]
    
    try:
        content = get_website_text_content("https://www.espncricinfo.com/series")
        
        # Process the content to extract upcoming matches
        matches = []
        if content:
            lines = content.split('\n')
            
            # Find date patterns and match information
            date_pattern = re.compile(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)')
            
            for i, line in enumerate(lines):
                if re.search(r'vs', line) and len(line) < 100:
                    teams = line.strip()
                    date = ""
                    venue = ""
                    
                    # Look for date in next few lines
                    for j in range(1, 5):
                        if i+j < len(lines) and date_pattern.search(lines[i+j]):
                            date = lines[i+j].strip()
                            break
                    
                    # Look for venue in nearby lines
                    for j in range(-2, 5):
                        if i+j < len(lines) and i+j >= 0 and "Stadium" in lines[i+j]:
                            venue = lines[i+j].strip()
                            break
                    
                    if date or venue:
                        matches.append({
                            "teams": teams,
                            "date": date if date else "Date not found",
                            "venue": venue if venue else "Venue not found"
                        })
        
        # Limit to 5 matches
        matches = matches[:5]
        
        # Update cache and save to file
        if matches:
            data_cache["upcoming_matches"]["data"] = matches
            data_cache["upcoming_matches"]["timestamp"] = now
            save_match_data(matches)
        
        return matches
    except Exception as e:
        print(f"Error fetching upcoming matches: {str(e)}")
        
        # Try to use stored data even if it's stale
        stored_matches = get_match_data()
        if stored_matches:
            return stored_matches
        
        # Fallback data if web scraping fails and no stored data
        today = datetime.now()
        matches = [
            {"teams": "India vs Australia", "venue": "Mumbai", "date": today.strftime("%d %b")},
            {"teams": "England vs South Africa", "venue": "Chennai", "date": (today + timedelta(days=2)).strftime("%d %b")},
            {"teams": "New Zealand vs Pakistan", "venue": "Delhi", "date": (today + timedelta(days=5)).strftime("%d %b")}
        ]
        # Save the fallback data too
        save_match_data(matches)
        return matches

def get_pitch_conditions(venue):
    """
    Get pitch conditions for a cricket venue
    """
    # This would ideally scrape from a cricket analysis website
    # For now, using predefined conditions
    pitch_conditions = {
        "Mumbai": {"batting_friendly": 8, "pace_friendly": 5, "spin_friendly": 4},
        "Chennai": {"batting_friendly": 5, "pace_friendly": 3, "spin_friendly": 9},
        "Kolkata": {"batting_friendly": 7, "pace_friendly": 6, "spin_friendly": 6},
        "Delhi": {"batting_friendly": 6, "pace_friendly": 7, "spin_friendly": 5},
        "Bangalore": {"batting_friendly": 9, "pace_friendly": 4, "spin_friendly": 3},
        "Hyderabad": {"batting_friendly": 7, "pace_friendly": 5, "spin_friendly": 7},
        "Punjab": {"batting_friendly": 8, "pace_friendly": 6, "spin_friendly": 4},
        "Rajasthan": {"batting_friendly": 6, "pace_friendly": 5, "spin_friendly": 8}
    }
    
    # Try to find venue in our predefined list
    for known_venue in pitch_conditions.keys():
        if venue.lower() in known_venue.lower() or known_venue.lower() in venue.lower():
            return pitch_conditions[known_venue]
    
    # Default values if venue not found
    return {"batting_friendly": 6, "pace_friendly": 6, "spin_friendly": 6}

def get_fantasy_player_prices():
    """
    Get fantasy cricket player prices (would ideally scrape from fantasy platforms)
    """
    # This would ideally scrape from fantasy cricket websites
    # For demonstration, returning predefined data
    top_players = [
        {"name": "Virat Kohli", "price": 10.5, "team": "India", "role": "Batsman", "ownership": 78.4},
        {"name": "Rohit Sharma", "price": 10.0, "team": "India", "role": "Batsman", "ownership": 74.1},
        {"name": "Jasprit Bumrah", "price": 9.5, "team": "India", "role": "Bowler", "ownership": 65.3},
        {"name": "Babar Azam", "price": 10.0, "team": "Pakistan", "role": "Batsman", "ownership": 68.9},
        {"name": "Kane Williamson", "price": 9.0, "team": "New Zealand", "role": "Batsman", "ownership": 42.1},
        {"name": "Ben Stokes", "price": 10.5, "team": "England", "role": "All-rounder", "ownership": 72.3},
        {"name": "Rashid Khan", "price": 9.0, "team": "Afghanistan", "role": "Bowler", "ownership": 58.7},
        {"name": "Mitchell Starc", "price": 9.5, "team": "Australia", "role": "Bowler", "ownership": 63.8},
        {"name": "Jos Buttler", "price": 9.5, "team": "England", "role": "Wicketkeeper", "ownership": 61.2},
        {"name": "Shakib Al Hasan", "price": 9.0, "team": "Bangladesh", "role": "All-rounder", "ownership": 45.2}
    ]
    
    return top_players