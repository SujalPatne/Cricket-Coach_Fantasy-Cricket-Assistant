"""
Cricket Web Scraper - For fetching real-time cricket data from the web

This module provides functionality to scrape real-time cricket data from various websites
and convert it to a format that can be used by the Fantasy Cricket Assistant.
"""

import requests
import logging
import json
import re
import time
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Constants
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Cache for scraped data
CACHE = {
    'live_matches': {'data': None, 'timestamp': 0},
    'recent_matches': {'data': None, 'timestamp': 0},
    'upcoming_matches': {'data': None, 'timestamp': 0},
    'player_stats': {},
    'news': {'data': None, 'timestamp': 0}
}

# Cache expiration (in seconds)
CACHE_EXPIRY = {
    'live_matches': 60,  # 1 minute
    'recent_matches': 3600,  # 1 hour
    'upcoming_matches': 3600,  # 1 hour
    'player_stats': 3600,  # 1 hour
    'news': 1800  # 30 minutes
}

def get_live_matches() -> List[Dict[str, Any]]:
    """
    Get live cricket matches from the web
    
    Returns:
    - List of live match dictionaries
    """
    # Check cache first
    if CACHE['live_matches']['data'] is not None:
        if (time.time() - CACHE['live_matches']['timestamp']) < CACHE_EXPIRY['live_matches']:
            logger.info("Using cached live matches data")
            return CACHE['live_matches']['data']
    
    logger.info("Fetching live matches from the web")
    
    try:
        # Try ESPN Cricinfo first
        matches = _scrape_espn_live_matches()
        if matches:
            # Update cache
            CACHE['live_matches'] = {
                'data': matches,
                'timestamp': time.time()
            }
            return matches
    except Exception as e:
        logger.error(f"Error scraping ESPN live matches: {str(e)}")
    
    try:
        # Try Cricbuzz as fallback
        matches = _scrape_cricbuzz_live_matches()
        if matches:
            # Update cache
            CACHE['live_matches'] = {
                'data': matches,
                'timestamp': time.time()
            }
            return matches
    except Exception as e:
        logger.error(f"Error scraping Cricbuzz live matches: {str(e)}")
    
    # Return empty list if all scraping attempts fail
    return []

def get_player_stats(player_name: str) -> Optional[Dict[str, Any]]:
    """
    Get player statistics from the web
    
    Parameters:
    - player_name: Name of the player
    
    Returns:
    - Player statistics dictionary or None if not found
    """
    # Normalize player name for cache key
    normalized_name = player_name.lower().replace(" ", "_")
    
    # Check cache first
    if normalized_name in CACHE['player_stats']:
        if (time.time() - CACHE['player_stats'][normalized_name]['timestamp']) < CACHE_EXPIRY['player_stats']:
            logger.info(f"Using cached player stats for {player_name}")
            return CACHE['player_stats'][normalized_name]['data']
    
    logger.info(f"Fetching player stats for {player_name} from the web")
    
    try:
        # Try ESPN Cricinfo first
        player_stats = _scrape_espn_player_stats(player_name)
        if player_stats:
            # Update cache
            CACHE['player_stats'][normalized_name] = {
                'data': player_stats,
                'timestamp': time.time()
            }
            return player_stats
    except Exception as e:
        logger.error(f"Error scraping ESPN player stats: {str(e)}")
    
    try:
        # Try Cricbuzz as fallback
        player_stats = _scrape_cricbuzz_player_stats(player_name)
        if player_stats:
            # Update cache
            CACHE['player_stats'][normalized_name] = {
                'data': player_stats,
                'timestamp': time.time()
            }
            return player_stats
    except Exception as e:
        logger.error(f"Error scraping Cricbuzz player stats: {str(e)}")
    
    # Return None if all scraping attempts fail
    return None

def get_cricket_news() -> List[Dict[str, Any]]:
    """
    Get latest cricket news from the web
    
    Returns:
    - List of news article dictionaries
    """
    # Check cache first
    if CACHE['news']['data'] is not None:
        if (time.time() - CACHE['news']['timestamp']) < CACHE_EXPIRY['news']:
            logger.info("Using cached cricket news")
            return CACHE['news']['data']
    
    logger.info("Fetching cricket news from the web")
    
    try:
        # Try ESPN Cricinfo first
        news = _scrape_espn_cricket_news()
        if news:
            # Update cache
            CACHE['news'] = {
                'data': news,
                'timestamp': time.time()
            }
            return news
    except Exception as e:
        logger.error(f"Error scraping ESPN cricket news: {str(e)}")
    
    try:
        # Try Cricbuzz as fallback
        news = _scrape_cricbuzz_cricket_news()
        if news:
            # Update cache
            CACHE['news'] = {
                'data': news,
                'timestamp': time.time()
            }
            return news
    except Exception as e:
        logger.error(f"Error scraping Cricbuzz cricket news: {str(e)}")
    
    # Return empty list if all scraping attempts fail
    return []

def _scrape_espn_live_matches() -> List[Dict[str, Any]]:
    """Scrape live matches from ESPN Cricinfo"""
    url = "https://www.espncricinfo.com/live-cricket-score"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    matches = []
    
    # This is a simplified implementation
    # In a real system, you'd need to analyze the page structure and extract data accordingly
    match_elements = soup.select('.match-info')
    
    for match_element in match_elements:
        try:
            teams_element = match_element.select_one('.teams')
            if not teams_element:
                continue
                
            team1 = teams_element.select_one('.team:nth-child(1) .name').text.strip()
            team2 = teams_element.select_one('.team:nth-child(2) .name').text.strip()
            
            score_elements = match_element.select('.score')
            score1 = score_elements[0].text.strip() if len(score_elements) > 0 else ""
            score2 = score_elements[1].text.strip() if len(score_elements) > 1 else ""
            
            status = match_element.select_one('.status').text.strip()
            
            matches.append({
                'teams': f"{team1} vs {team2}",
                'score1': score1,
                'score2': score2,
                'status': status,
                'source': 'ESPNCricinfo'
            })
        except Exception as e:
            logger.error(f"Error parsing match element: {str(e)}")
    
    return matches

def _scrape_cricbuzz_live_matches() -> List[Dict[str, Any]]:
    """Scrape live matches from Cricbuzz"""
    url = "https://www.cricbuzz.com/cricket-match/live-scores"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    matches = []
    
    # This is a simplified implementation
    # In a real system, you'd need to analyze the page structure and extract data accordingly
    match_elements = soup.select('.cb-mtch-lst')
    
    for match_element in match_elements:
        try:
            match_info = match_element.select_one('.cb-lv-scr-mtch-hdr').text.strip()
            status = match_element.select_one('.cb-lv-scr-mtch-sm').text.strip()
            
            # Extract teams from match info
            teams_match = re.search(r'(.+) vs (.+),', match_info)
            if teams_match:
                team1 = teams_match.group(1).strip()
                team2 = teams_match.group(2).strip()
                teams = f"{team1} vs {team2}"
            else:
                teams = match_info
            
            # Extract scores
            score_elements = match_element.select('.cb-lv-scrs-col')
            scores = [score.text.strip() for score in score_elements]
            
            matches.append({
                'teams': teams,
                'score1': scores[0] if len(scores) > 0 else "",
                'score2': scores[1] if len(scores) > 1 else "",
                'status': status,
                'source': 'Cricbuzz'
            })
        except Exception as e:
            logger.error(f"Error parsing match element: {str(e)}")
    
    return matches

# Placeholder implementations for other scraping functions
def _scrape_espn_player_stats(player_name: str) -> Optional[Dict[str, Any]]:
    """Scrape player stats from ESPN Cricinfo"""
    # This would be implemented with actual web scraping logic
    return None

def _scrape_cricbuzz_player_stats(player_name: str) -> Optional[Dict[str, Any]]:
    """Scrape player stats from Cricbuzz"""
    # This would be implemented with actual web scraping logic
    return None

def _scrape_espn_cricket_news() -> List[Dict[str, Any]]:
    """Scrape cricket news from ESPN Cricinfo"""
    # This would be implemented with actual web scraping logic
    return []

def _scrape_cricbuzz_cricket_news() -> List[Dict[str, Any]]:
    """Scrape cricket news from Cricbuzz"""
    # This would be implemented with actual web scraping logic
    return []
