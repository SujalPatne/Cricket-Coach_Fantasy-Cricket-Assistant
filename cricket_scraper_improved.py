import trafilatura
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from datetime import datetime, timedelta
import random

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
    "pitch_conditions": {"data": None, "timestamp": 0},
    "player_cache": {},  # Player-specific cache
    "espn_failed": False  # Track if ESPN is blocking requests
}

# Cache validity period in seconds (10 minutes)
CACHE_VALIDITY = 600

def get_website_text_content(url):
    """
    Extract main text content from a website using trafilatura with improved reliability
    """
    try:
        # Set a reasonable timeout and use a common browser user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Try to fetch with requests first
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Use trafilatura to extract content
        text = trafilatura.extract(response.text)
        if text:
            return text
            
        # If trafilatura fails, try BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text()
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Remove blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return "Could not download content"

def fetch_with_beautiful_soup(url):
    """
    Fetch and parse HTML content using BeautifulSoup
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def get_live_cricket_matches():
    """
    Get information about currently live cricket matches with improved reliability
    """
    # Check if cache is valid
    now = time.time()
    if data_cache["live_matches"]["data"] and now - data_cache["live_matches"]["timestamp"] < CACHE_VALIDITY:
        return data_cache["live_matches"]["data"]
    
    # Try multiple cricket data sources for better reliability
    urls = [
        "https://www.cricbuzz.com/cricket-match/live-scores",
        "https://www.espncricinfo.com/live-cricket-score",
        "https://www.icc-cricket.com/live-matches"
    ]
    
    matches = []
    
    for url in urls:
        try:
            print(f"Trying to fetch live matches from: {url}")
            content = get_website_text_content(url)
            
            if not content or content == "Could not download content":
                print(f"Failed to get content from {url}, trying next source...")
                continue
            
            # Process the content to extract match information
            lines = content.split('\n')
            match_info = {}
            
            for line in lines:
                # Extract team names (more robust pattern matching)
                if (re.search(r'\bvs\b|\bv\b', line) and len(line) < 100 and 
                    any(team in line for team in ["India", "Australia", "England", "Pakistan", 
                                                  "New Zealand", "South Africa", "West Indies", 
                                                  "Sri Lanka", "Bangladesh", "Afghanistan",
                                                  "Mumbai", "Chennai", "Kolkata", "Delhi",
                                                  "Punjab", "Rajasthan", "Hyderabad", "Bangalore"])):
                    
                    if match_info and 'teams' in match_info:  # Save previous match
                        matches.append(match_info)
                    match_info = {'teams': line.strip()}
                    
                # Extract match status
                elif (match_info and 'teams' in match_info and 
                      not 'status' in match_info and 
                      re.search(r'innings|overs|wicket|run|batting|score|chase|target|need|won|lost|draw|tie', line.lower())):
                    match_info['status'] = line.strip()
                    
                # Extract venue information
                elif (match_info and 'teams' in match_info and 
                      'status' in match_info and 
                      not 'venue' in match_info and 
                      (re.search(r'stadium|ground|oval|field|park', line.lower()) or 
                       any(venue in line for venue in ["Mumbai", "Chennai", "Kolkata", "Delhi", 
                                                      "Bangalore", "Hyderabad", "Ahmedabad", "Pune"]))):
                    match_info['venue'] = line.strip()
                    matches.append(match_info)
                    match_info = {}
            
            # Add the last match if not added
            if match_info and 'teams' in match_info:
                matches.append(match_info)
                
            # If we found matches from this source, stop trying others
            if matches:
                print(f"Successfully found {len(matches)} matches from {url}")
                break
                
        except Exception as e:
            print(f"Error fetching live matches from {url}: {str(e)}")
    
    # Clean up match information for consistency
    for match in matches:
        # Clean up team names
        if 'teams' in match:
            match['teams'] = re.sub(r'\s+', ' ', match['teams']).strip()
        
        # Ensure status field exists with at least something
        if 'status' not in match:
            match['status'] = "Live match"
            
        # Ensure venue field exists
        if 'venue' not in match:
            match['venue'] = "Venue information unavailable"
    
    # Limit to 5 matches and update cache
    matches = matches[:5]
    data_cache["live_matches"]["data"] = matches
    data_cache["live_matches"]["timestamp"] = now
    
    # If we still don't have matches, check if we can use stored match data
    if not matches:
        stored_matches = get_match_data()
        if stored_matches:
            print("Using stored match data as fallback")
            return stored_matches
    
    return matches

def get_player_stats(player_name):
    """
    Get real stats for a cricket player by name with improved reliability
    """
    print(f"Getting stats for player: {player_name}")
    
    # Check if cache is valid to avoid too many requests
    now = time.time()
    cache_key = player_name.lower()
    
    if cache_key in data_cache["player_cache"] and now - data_cache["player_cache"][cache_key]["timestamp"] < CACHE_VALIDITY:
        print(f"Found {player_name} in cache")
        return data_cache["player_cache"][cache_key]["data"]
    
    # Try to find player in stored data first
    stored_players = get_cricket_players()
    if stored_players:
        for player in stored_players:
            if player.get('name', '').lower() == player_name.lower():
                # Check if the data is recent (within last 7 days)
                last_updated = player.get('last_updated', '')
                if last_updated:
                    try:
                        last_date = datetime.strptime(last_updated, "%Y-%m-%d")
                        if (datetime.now() - last_date).days < 7:
                            print(f"Found recent data for {player_name} in stored data")
                            # Store in cache for faster retrieval
                            data_cache["player_cache"][cache_key] = {
                                "data": player,
                                "timestamp": now
                            }
                            return player
                    except:
                        pass
                
    # Possible sources to try for cricket player data
    sources = [
        f"https://www.cricbuzz.com/profiles/search?q={player_name.replace(' ', '+')}",
        f"https://www.espncricinfo.com/cricketers/search?term={player_name}"
    ]
    
    player_info = {'name': player_name}
    stats_found = False
    
    # Try each source
    for source_url in sources:
        try:
            print(f"Trying source: {source_url}")
            
            # Skip ESPNCricinfo if it's been failing (they have stricter anti-scraping)
            if "espncricinfo.com" in source_url and data_cache["espn_failed"]:
                print("Skipping ESPNCricinfo due to previous failures")
                continue
                
            content = get_website_text_content(source_url)
            
            if not content or "Could not download content" in content:
                print(f"Failed to get content from {source_url}")
                if "espncricinfo.com" in source_url:
                    data_cache["espn_failed"] = True
                continue
            
            # Look for player name in the content
            if player_name.lower() not in content.lower():
                print(f"Player {player_name} not found in {source_url}")
                continue
                
            print(f"Found possible match for {player_name} in {source_url}")
            
            # Parse the content - this would be more robust with BeautifulSoup in production
            lines = content.split('\n')
            
            # Look for lines containing the player name
            for i, line in enumerate(lines):
                # Skip very short lines or ones obviously not relevant
                if len(line) < 3 or "search" in line.lower():
                    continue
                    
                if player_name.lower() in line.lower():
                    # Get the context (lines around this mention)
                    start_idx = max(0, i-10)
                    end_idx = min(len(lines), i+20)
                    context = '\n'.join(lines[start_idx:end_idx])
                    
                    # Extract role information
                    if 'role' not in player_info:
                        if re.search(r'bat(ter|sman)', context, re.IGNORECASE):
                            player_info['role'] = 'Batsman'
                            stats_found = True
                        elif re.search(r'bowl(er|ing)', context, re.IGNORECASE):
                            player_info['role'] = 'Bowler'
                            stats_found = True
                        elif re.search(r'all.?round', context, re.IGNORECASE):
                            player_info['role'] = 'All-rounder'
                            stats_found = True
                        elif re.search(r'wicket.?keep', context, re.IGNORECASE):
                            player_info['role'] = 'Wicket-keeper'
                            stats_found = True
                    
                    # Extract batting average
                    if 'batting_avg' not in player_info:
                        batting_avg_match = re.search(r'bat(ting)?.+?avg.+?(\d+\.\d+|\d+)', context, re.IGNORECASE)
                        if batting_avg_match:
                            player_info['batting_avg'] = batting_avg_match.group(2)
                            stats_found = True
                    
                    # Extract bowling average
                    if 'bowling_avg' not in player_info:
                        bowling_avg_match = re.search(r'bowl(ing)?.+?avg.+?(\d+\.\d+|\d+)', context, re.IGNORECASE)
                        if bowling_avg_match:
                            player_info['bowling_avg'] = bowling_avg_match.group(2)
                            stats_found = True
                    
                    # Extract strike rate
                    if 'strike_rate' not in player_info:
                        sr_match = re.search(r'(strike.?rate|sr).+?(\d+\.\d+|\d+)', context, re.IGNORECASE)
                        if sr_match:
                            player_info['strike_rate'] = sr_match.group(2)
                            stats_found = True
                    
                    # Extract team information
                    if 'team' not in player_info:
                        team_match = re.search(r'(team|plays for|country).+?([A-Za-z ]+)', context, re.IGNORECASE)
                        if team_match:
                            team = team_match.group(2).strip()
                            # Only use if it seems like a team name (not too long)
                            if len(team) < 25:
                                player_info['team'] = team
                                stats_found = True
            
            # If we found some stats, no need to try other sources
            if stats_found:
                print(f"Found stats for {player_name}: {player_info}")
                break
                
        except Exception as e:
            print(f"Error processing {source_url}: {str(e)}")
            continue
    
    # Add missing fields with default values
    for field in ['role', 'batting_avg', 'bowling_avg', 'strike_rate', 'team', 'recent_form']:
        if field not in player_info:
            player_info[field] = 'Not available'
    
    # Add last updated timestamp for freshness tracking
    player_info['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    # Add player to cache
    data_cache["player_cache"][cache_key] = {
        "data": player_info,
        "timestamp": now
    }
    
    # Save to persistent storage if we found something useful
    if stats_found:
        new_player = True
        for i, player in enumerate(stored_players):
            if player.get('name', '').lower() == player_name.lower():
                stored_players[i] = player_info
                new_player = False
                break
        
        if new_player:
            stored_players.append(player_info)
            
        save_cricket_players(stored_players)
    
    return player_info

def get_upcoming_matches():
    """
    Get information about upcoming cricket matches with improved reliability
    """
    # Check if cache is valid
    now = time.time()
    if data_cache["upcoming_matches"]["data"] and now - data_cache["upcoming_matches"]["timestamp"] < CACHE_VALIDITY:
        return data_cache["upcoming_matches"]["data"]
    
    # Try multiple sources for better reliability
    urls = [
        "https://www.cricbuzz.com/cricket-schedule/upcoming-matches",
        "https://www.espncricinfo.com/series"
    ]
    
    upcoming = []
    
    for url in urls:
        try:
            print(f"Trying to fetch upcoming matches from: {url}")
            content = get_website_text_content(url)
            
            if not content or content == "Could not download content":
                print(f"Failed to get content from {url}, trying next source...")
                continue
            
            # Process the content to extract match information
            lines = content.split('\n')
            match_info = {}
            date_pattern = re.compile(r'\b\d{1,2}(st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(st|nd|rd|th)?\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b')
            
            current_date = ""
            
            for line in lines:
                # Look for date patterns
                date_match = date_pattern.search(line)
                if date_match:
                    current_date = line.strip()
                    continue
                
                # Extract team names
                if (re.search(r'\bvs\b|\bv\b', line) and len(line) < 100 and 
                    any(team in line for team in ["India", "Australia", "England", "Pakistan", 
                                                  "New Zealand", "South Africa", "West Indies", 
                                                  "Sri Lanka", "Bangladesh", "Afghanistan",
                                                  "Mumbai", "Chennai", "Kolkata", "Delhi",
                                                  "Punjab", "Rajasthan", "Hyderabad", "Bangalore"])):
                    
                    if match_info and 'teams' in match_info:  # Save previous match
                        upcoming.append(match_info)
                    
                    match_info = {
                        'teams': line.strip(),
                        'date': current_date
                    }
                    
                # Extract venue information
                elif (match_info and 'teams' in match_info and 
                      not 'venue' in match_info and 
                      (re.search(r'stadium|ground|oval|field|park', line.lower()) or 
                       any(venue in line for venue in ["Mumbai", "Chennai", "Kolkata", "Delhi", 
                                                      "Bangalore", "Hyderabad", "Ahmedabad", "Pune"]))):
                    match_info['venue'] = line.strip()
                    upcoming.append(match_info)
                    match_info = {}
            
            # Add the last match if not added
            if match_info and 'teams' in match_info:
                upcoming.append(match_info)
                
            # If we found matches from this source, stop trying others
            if upcoming:
                print(f"Successfully found {len(upcoming)} upcoming matches from {url}")
                break
                
        except Exception as e:
            print(f"Error fetching upcoming matches from {url}: {str(e)}")
    
    # Clean up match information for consistency
    for match in upcoming:
        # Ensure all fields exist
        if 'venue' not in match:
            match['venue'] = "Venue information unavailable"
            
        if 'date' not in match:
            match['date'] = "Date information unavailable"
    
    # Limit to 5 matches and update cache
    upcoming = upcoming[:5]
    data_cache["upcoming_matches"]["data"] = upcoming
    data_cache["upcoming_matches"]["timestamp"] = now
    
    # Save to persistent storage
    save_match_data(upcoming)
    
    return upcoming

def get_pitch_conditions(venue):
    """
    Get pitch conditions for a cricket venue with improved reliability
    """
    # Check if we have this venue in cache
    now = time.time()
    cache_key = venue.lower()
    
    if "pitch_cache" not in data_cache:
        data_cache["pitch_cache"] = {}
    
    if cache_key in data_cache["pitch_cache"] and now - data_cache["pitch_cache"][cache_key]["timestamp"] < CACHE_VALIDITY:
        return data_cache["pitch_cache"][cache_key]["data"]
    
    # List of possible pitch descriptions
    pitch_types = [
        "batting friendly", "bowling friendly", "spin friendly", "pace friendly",
        "flat track", "green pitch", "dry pitch", "cracked pitch", "slow pitch",
        "bouncy pitch", "turning pitch", "balanced pitch"
    ]
    
    # Try to find real information
    try:
        # Search for venue information
        search_url = f"https://www.cricbuzz.com/search?q={venue}+pitch+conditions"
        content = get_website_text_content(search_url)
        
        if content and "Could not download content" not in content:
            relevant_lines = []
            lines = content.split('\n')
            
            for line in lines:
                if venue.lower() in line.lower() and any(pt in line.lower() for pt in pitch_types):
                    relevant_lines.append(line)
            
            if relevant_lines:
                # Join the relevant information
                pitch_info = {
                    "venue": venue,
                    "conditions": " ".join(relevant_lines[:2]),  # Limit to first 2 relevant lines
                    "source": "cricbuzz.com"
                }
                
                # Save to cache
                data_cache["pitch_cache"][cache_key] = {
                    "data": pitch_info,
                    "timestamp": now
                }
                
                return pitch_info
    
    except Exception as e:
        print(f"Error fetching pitch conditions for {venue}: {str(e)}")
    
    # Create a basic response if we couldn't find real data
    pitch_info = {
        "venue": venue,
        "conditions": "No specific pitch information available for this venue currently.",
        "note": "Check match previews closer to the match date for updated pitch information."
    }
    
    # Save to cache
    data_cache["pitch_cache"][cache_key] = {
        "data": pitch_info,
        "timestamp": now
    }
    
    return pitch_info

def get_fantasy_player_prices():
    """
    Get fantasy cricket player prices from various sources
    """
    # This would ideally scrape from fantasy platforms
    # For now, we'll return the stored player data which includes fantasy prices
    players = get_cricket_players()
    if players:
        return players
    
    # If no stored data, return empty list
    return []