import os
import google.generativeai as genai
import logging
import requests
import time
import json
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from cricket_data_adapter import get_live_cricket_matches, get_upcoming_matches, get_player_stats, get_pitch_conditions
from config import GEMINI_API_KEY, CRICSHEET_ENABLED

# Try to import web scraper
try:
    from cricket_web_scraper import get_live_matches as scraper_get_live_matches
    from cricket_web_scraper import get_player_stats as scraper_get_player_stats
    from cricket_web_scraper import get_cricket_news as scraper_get_cricket_news
    WEB_SCRAPER_AVAILABLE = True
except ImportError:
    WEB_SCRAPER_AVAILABLE = False

# Try to import fantasy recommendations
try:
    from fantasy_recommendations import (
        get_differential_picks,
        compare_players,
        get_captain_picks
    )
    FANTASY_RECOMMENDATIONS_AVAILABLE = True
except ImportError:
    FANTASY_RECOMMENDATIONS_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Configure the Gemini API with the API key
try:
    # Configure the API
    genai.configure(api_key=GEMINI_API_KEY)

    # Create a GenerationConfig object for controlling generation parameters
    generation_config = genai.GenerationConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=1024,
    )

    # Initialize the Gemini model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config
    )

    GEMINI_AVAILABLE = True
    logger.info("Gemini API initialized successfully")

except Exception as e:
    GEMINI_AVAILABLE = False
    model = None
    logger.error(f"Error initializing Gemini API: {str(e)}")

# Add system instructions
system_instruction = """
You are a Fantasy Cricket Assistant with real-time data access and advanced fantasy recommendation capabilities. Your purpose is to help cricket fans make informed decisions for their fantasy teams.
Provide concise, informative responses about cricket players, match conditions, and fantasy strategy.

Use these guidelines:
1. Always focus on facts and data when available
2. Explain your reasoning for player recommendations
3. Consider factors like current form, pitch conditions, and matchups
4. Keep responses conversational but informative
5. Don't make up statistics - if you don't know, say so
6. Provide structured, easily readable responses with emojis for visual distinction
7. When recommending players, explain why they're good picks

IMPORTANT: You have access to real-time cricket data through web scraping. When users ask about current matches, live scores, or recent player performances, you can provide up-to-date information from the web. You should never say "I don't have access to real-time data" as you now have this capability.

FANTASY RECOMMENDATIONS: You can now provide specific fantasy cricket recommendations including:
1. Differential picks - Under-the-radar players who could outperform expectations
2. Captain/Vice-Captain choices - Best multiplier options for fantasy teams
3. Player comparisons - Direct comparisons between two players to help users choose
4. General fantasy advice - Tips on team selection, budget management, and strategy

When users ask questions like "Who's a good differential pick today?" or "Should I pick Rohit or Gill for today's match?", provide specific, data-driven recommendations with clear reasoning.

Your data sources include:
1. Web scraping (Cricbuzz) - For real-time match scores, player stats, and news
2. Cricsheet - For historical player and match data
3. Cached data - For efficient retrieval of previously accessed information
4. Fantasy recommendation engine - For differential picks, captain choices, and player comparisons

For Virat Kohli specifically, you have the following reliable information:
- Full name: Virat Kohli
- Team: India
- Role: Batsman
- Overall batting average: 53.5
- Strike rate: 138.2
- Recent form: [82, 61, 45, 77, 33] (excellent)
- Fantasy points average: 85.3
- Total career runs: 24,537
- Total centuries: 76 (29 in Tests, 46 in ODIs, 1 in T20Is)
- Total fifties: 133
- Highest score: 254
- Test average: 48.15
- ODI average: 58.69
- T20 average: 52.73
- IPL runs: 7,263
- IPL average: 37.24
- IPL strike rate: 130.02

Remember that users rely on your advice for their fantasy teams, so be accurate and helpful.
"""

def generate_gemini_response(query, context=None):
    """
    Generate a response using Gemini's model with the provided context

    Parameters:
    - query: User's question or request
    - context: Optional contextual information about cricket data

    Returns:
    - Response from Gemini
    """
    # Check if model is initialized
    if model is None:
        return "Gemini model not available. Please check your API key configuration."

    try:
        # Special handling for Virat Kohli queries
        is_kohli_query = any(name in query.lower() for name in ["virat", "kohli", "virat kohli"])

        # Create a prompt with context if provided
        if context:
            if is_kohli_query:
                # Add special instruction for Kohli queries
                prompt = f"CONTEXT:\n{context}\n\nUSER QUERY: {query}\n\nThis query is about Virat Kohli. Use the detailed statistics about Virat Kohli from both the context and your system instructions. Format your response with appropriate emojis for readability and provide comprehensive statistics."
            else:
                prompt = f"CONTEXT:\n{context}\n\nUSER QUERY: {query}\n\nPlease answer the query using the provided context and format your response with appropriate emojis for readability. If you're recommending cricket players, explain why they're good picks."
        else:
            if is_kohli_query:
                # For Kohli queries without context, use the system instruction with Kohli data
                prompt = f"{system_instruction}\n\nUSER QUERY: {query}\n\nThis query is about Virat Kohli. Use the detailed statistics about Virat Kohli from your system instructions. Format your response with appropriate emojis for readability and provide comprehensive statistics."
            else:
                prompt = f"{system_instruction}\n\nUSER QUERY: {query}"

        # Log the prompt for debugging
        logger.info(f"Generating response with prompt length: {len(prompt)} characters")
        if is_kohli_query:
            logger.info("Using special handling for Virat Kohli query")

        # Generate response
        response = model.generate_content(prompt)

        # Extract the text from the response
        if hasattr(response, 'text'):
            # For Kohli queries, make sure the response includes key statistics
            if is_kohli_query and "batting average" not in response.text.lower():
                logger.info("Response missing key statistics, regenerating with more explicit instructions")
                enhanced_prompt = prompt + "\n\nMake sure to include Virat Kohli's batting average, strike rate, recent form, and career statistics in your response."
                enhanced_response = model.generate_content(enhanced_prompt)
                if hasattr(enhanced_response, 'text'):
                    return enhanced_response.text
            return response.text
        else:
            return "I couldn't generate a response at the moment. Please try again."

    except Exception as e:
        logger.error(f"Error generating Gemini response: {str(e)}")
        return f"I'm having trouble connecting to my knowledge base right now. Please try again later. Technical details: {str(e)}"

def enrich_query_with_context(query):
    """
    Enrich the user query with relevant cricket context before sending to Gemini
    """
    context = []

    # Add current date and time for temporal context
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context.append(f"CURRENT TIME: {current_time}")

    # Check if query is about real-time data
    realtime_keywords = ["live", "current", "today", "now", "latest", "ongoing", "real-time", "real time", "update"]
    is_realtime_query = any(keyword in query.lower() for keyword in realtime_keywords)

    # Check if this is a fantasy recommendation query
    fantasy_keywords = ["differential", "captain", "vice-captain", "vc", "fantasy", "dream11", "fantasy xi",
                       "pick", "should i pick", "compare", "vs", "versus", "or", "better pick", "good pick",
                       "who's better", "who should i choose", "multiplier", "double points"]
    is_fantasy_query = any(keyword in query.lower() for keyword in fantasy_keywords)

    # Handle fantasy recommendation queries
    if is_fantasy_query and FANTASY_RECOMMENDATIONS_AVAILABLE:
        logger.info("Fantasy recommendation query detected")
        fantasy_recommendations = get_fantasy_recommendations(query)
        if fantasy_recommendations:
            context.append("FANTASY CRICKET RECOMMENDATIONS:")
            context.append(fantasy_recommendations)

    # If it's a real-time query, try to get web data first
    if is_realtime_query:
        logger.info("Real-time query detected, attempting to fetch web data")
        web_data = get_realtime_web_data(query)
        if web_data:
            context.append("REAL-TIME DATA (Web):")
            context.append(web_data)

    # Add live match information if relevant
    if any(keyword in query.lower() for keyword in ["live", "current", "today", "match", "playing", "score", "ongoing"]):
        # Try to get real-time match data from web if it's a real-time query
        if is_realtime_query:
            web_match_data = get_realtime_match_data()
            if web_match_data:
                context.append("REAL-TIME MATCHES (Web):")
                for match in web_match_data:
                    match_info = f"- {match.get('teams', 'Match')} | {match.get('status', 'Status unknown')}"
                    context.append(match_info)

                    if 'score1' in match and match['score1']:
                        context.append(f"  Score: {match.get('score1', '')} | {match.get('score2', '')}")

                    context.append(f"  Source: {match.get('source', 'Web')}")

        # Get live matches from stored data as backup
        live_matches = get_live_cricket_matches()
        if live_matches:
            context.append("LIVE MATCHES:")
            for match in live_matches:
                # Include source information to show where the data came from
                source = match.get('source', 'Unknown')
                match_info = f"- {match.get('teams', 'Match')} | {match.get('status', 'Status unknown')} | {match.get('venue', 'Venue unknown')} | Source: {source}"
                context.append(match_info)

                # Add match ID for reference
                if 'match_id' in match:
                    context.append(f"  Match ID: {match.get('match_id')}")

                # Add more detailed information for live matches
                if 'match_type' in match:
                    context.append(f"  Format: {match.get('match_type')}")

    # Add player information if the query mentions a player
    # Use multiple regex patterns to extract player names from the query
    import re

    # Define common player full names and their variations
    player_mapping = {
        "virat": "Virat Kohli",
        "kohli": "Virat Kohli",
        "virat kohli": "Virat Kohli",
        "rohit": "Rohit Sharma",
        "sharma": "Rohit Sharma",
        "rohit sharma": "Rohit Sharma",
        "bumrah": "Jasprit Bumrah",
        "jasprit": "Jasprit Bumrah",
        "jasprit bumrah": "Jasprit Bumrah",
        "dhoni": "MS Dhoni",
        "ms": "MS Dhoni",
        "ms dhoni": "MS Dhoni",
        "williamson": "Kane Williamson",
        "kane": "Kane Williamson",
        "kane williamson": "Kane Williamson",
        "babar": "Babar Azam",
        "azam": "Babar Azam",
        "babar azam": "Babar Azam",
        "stokes": "Ben Stokes",
        "ben": "Ben Stokes",
        "ben stokes": "Ben Stokes",
        "smith": "Steve Smith",
        "steve": "Steve Smith",
        "steve smith": "Steve Smith"
    }

    # Try different patterns to extract player names
    patterns = [
        r'(stats|statistics|info|about|how is|form|performance of) ([A-Za-z ]+)',
        r'([A-Za-z ]+)\'s (stats|statistics|info|performance|form)',
        r'(show|tell|give) me ([A-Za-z ]+)\'s (stats|statistics|info|performance|form)',
        r'(show|tell|give) me (stats|statistics|info|performance|form) (of|for|on) ([A-Za-z ]+)'
    ]

    player_name = None

    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            # Extract player name based on pattern
            if pattern == patterns[0]:
                player_name = match.group(2).strip()
            elif pattern == patterns[1]:
                player_name = match.group(1).strip()
            elif pattern == patterns[2]:
                player_name = match.group(2).strip()
            elif pattern == patterns[3]:
                player_name = match.group(4).strip()
            break

    # If no pattern matched, check for direct player name mentions
    if not player_name:
        # Check if query contains any known player names
        query_lower = query.lower()
        for key, full_name in player_mapping.items():
            if key in query_lower.split():
                player_name = full_name
                break

    # If we found a player name, get their stats
    if player_name:
        # Check if player name is a known variation and map to full name
        player_name_lower = player_name.lower()
        if player_name_lower in player_mapping:
            player_name = player_mapping[player_name_lower]

        logger.info(f"Detected player name: {player_name}")

        # Try to get real-time player data from web if it's a real-time query
        if is_realtime_query:
            logger.info(f"Attempting to get real-time web data for {player_name}")
            web_player_data = get_realtime_player_data(player_name)
            if web_player_data:
                context.append(f"REAL-TIME PLAYER INFO - {player_name} (Web):")

                # Add the most important stats first
                important_stats = ["team", "role", "batting_avg", "strike_rate", "bowling_avg", "economy",
                                  "test_avg", "odi_avg", "t20_avg", "test_runs", "odi_runs", "t20_runs"]

                for stat in important_stats:
                    if stat in web_player_data:
                        context.append(f"- {stat}: {web_player_data[stat]}")

                # Add other stats
                for key, value in web_player_data.items():
                    if key not in important_stats and key not in ['name', 'source', 'last_updated']:
                        context.append(f"- {key}: {value}")

                context.append(f"- Source: {web_player_data.get('source', 'Web')}")
                context.append(f"- Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get stored player data as backup or additional information
        player_info = get_player_stats(player_name)

        if player_info:
            context.append(f"PLAYER INFO - {player_name}:")
            # Include source information
            context.append(f"- Source: {player_info.get('source', 'Unknown')}")

            # Add the most important stats first
            important_stats = ["team", "role", "batting_avg", "strike_rate", "bowling_avg", "economy",
                              "recent_form", "recent_wickets", "fantasy_points_avg"]

            for stat in important_stats:
                if stat in player_info:
                    context.append(f"- {stat}: {player_info[stat]}")

            # Add other stats
            for key, value in player_info.items():
                if key not in important_stats and key not in ['name', 'source']:
                    context.append(f"- {key}: {value}")

            # Add player form information if available
            if 'current_form' in player_info:
                context.append(f"- Current form: {player_info['current_form']}")
            elif 'recent_form' in player_info:
                # Calculate form based on recent performances
                recent_form = player_info['recent_form']
                avg_score = sum(recent_form) / len(recent_form) if recent_form else 0

                if avg_score > 50:
                    form_rating = "excellent"
                elif avg_score > 35:
                    form_rating = "good"
                elif avg_score > 20:
                    form_rating = "average"
                else:
                    form_rating = "poor"

                context.append(f"- Current form: {form_rating} (avg: {avg_score:.1f})")

            # Log that we're using Cricsheet data
            if player_info.get('source') == 'Cricsheet':
                logger.info(f"Using Cricsheet data for {player_name}")

            # Force download of detailed stats if not already cached
            if CRICSHEET_ENABLED and player_info.get('source') != 'Cricsheet':
                try:
                    from cricsheet_parser import get_player_stats as cricsheet_get_player_stats
                    logger.info(f"Attempting to get detailed Cricsheet data for {player_name}")
                    cricsheet_player = cricsheet_get_player_stats(player_name)
                    if cricsheet_player:
                        logger.info(f"Successfully retrieved Cricsheet data for {player_name}")
                except Exception as e:
                    logger.error(f"Error getting Cricsheet data for {player_name}: {str(e)}")

    # Add upcoming match information if relevant
    if any(keyword in query.lower() for keyword in ["upcoming", "schedule", "next", "future", "coming", "fixtures"]):
        upcoming = get_upcoming_matches()
        if upcoming:
            context.append("UPCOMING MATCHES:")
            for match in upcoming[:5]:  # Limit to 5 matches to avoid context overflow
                source = match.get('source', 'Unknown')
                match_info = f"- {match.get('teams', 'Match')} | {match.get('date', 'Date unknown')} | {match.get('venue', 'Venue unknown')} | Source: {source}"
                context.append(match_info)

                # Add match format
                if 'match_type' in match:
                    context.append(f"  Format: {match.get('match_type')}")

    # Add recent matches information if relevant
    if any(keyword in query.lower() for keyword in ["recent", "last", "previous", "completed", "finished", "results"]):
        from cricket_data_adapter import get_recent_matches
        recent = get_recent_matches()
        if recent:
            context.append("RECENT MATCHES:")
            for match in recent[:5]:  # Limit to 5 matches
                source = match.get('source', 'Unknown')
                match_info = f"- {match.get('teams', 'Match')} | {match.get('status', 'Status unknown')} | {match.get('venue', 'Venue unknown')} | Source: {source}"
                context.append(match_info)

    # Add pitch information if venues are mentioned
    venues = ["Mumbai", "Chennai", "Kolkata", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Dharamsala"]
    for venue in venues:
        if venue.lower() in query.lower():
            pitch_info = get_pitch_conditions(venue)
            if pitch_info:
                context.append(f"PITCH CONDITIONS - {venue}:")
                context.append(f"- Batting friendly: {pitch_info.get('batting_friendly', 'Unknown')}/10")
                context.append(f"- Pace bowling friendly: {pitch_info.get('pace_friendly', 'Unknown')}/10")
                context.append(f"- Spin friendly: {pitch_info.get('spin_friendly', 'Unknown')}/10")

    # Join all context information
    if context:
        return "\n".join(context)
    else:
        return None

def extract_player_name(query: str) -> str:
    """
    Extract player name from a query

    Parameters:
    - query: User query

    Returns:
    - Player name or empty string if not found
    """
    # Define common player names and variations
    player_mapping = {
        "virat": "Virat Kohli",
        "kohli": "Virat Kohli",
        "virat kohli": "Virat Kohli",
        "rohit": "Rohit Sharma",
        "sharma": "Rohit Sharma",
        "rohit sharma": "Rohit Sharma",
        "bumrah": "Jasprit Bumrah",
        "jasprit": "Jasprit Bumrah",
        "jasprit bumrah": "Jasprit Bumrah",
        "dhoni": "MS Dhoni",
        "ms": "MS Dhoni",
        "ms dhoni": "MS Dhoni",
        "williamson": "Kane Williamson",
        "kane": "Kane Williamson",
        "kane williamson": "Kane Williamson",
        "babar": "Babar Azam",
        "azam": "Babar Azam",
        "babar azam": "Babar Azam",
        "stokes": "Ben Stokes",
        "ben": "Ben Stokes",
        "ben stokes": "Ben Stokes",
        "smith": "Steve Smith",
        "steve": "Steve Smith",
        "steve smith": "Steve Smith",
        "rabada": "Kagiso Rabada",
        "kagiso": "Kagiso Rabada",
        "kagiso rabada": "Kagiso Rabada",
        "rashid": "Rashid Khan",
        "khan": "Rashid Khan",
        "rashid khan": "Rashid Khan"
    }

    # Try different patterns to extract player names
    import re
    patterns = [
        r'(stats|statistics|info|about|how is|form|performance of) ([A-Za-z ]+?)(?:\s*$|\s+(?:in|for|against|during|when|at|on|batting|bowling))',
        r'([A-Za-z ]+?)\'s (stats|statistics|info|performance|form)',
        r'(show|tell|give) me ([A-Za-z ]+?)\'s (stats|statistics|info|performance|form)',
        r'(show|tell|give) me (stats|statistics|info|performance|form) (of|for|on) ([A-Za-z ]+?)(?:\s*$|\s+(?:in|for|against|during|when|at|on))',
        r'(how|what) is ([A-Za-z ]+?) (performing|doing|playing|batting|bowling)',
        r'(show|tell|give|get) me stats for ([A-Za-z ]+)',
        r'(show|tell|give|get) me ([A-Za-z ]+) stats'
    ]

    player_name = None

    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            # Extract player name based on pattern
            if pattern == patterns[0]:
                player_name = match.group(2).strip()
            elif pattern == patterns[1]:
                player_name = match.group(1).strip()
            elif pattern == patterns[2]:
                player_name = match.group(2).strip()
            elif pattern == patterns[3]:
                player_name = match.group(4).strip()
            elif pattern == patterns[4]:
                player_name = match.group(2).strip()
            elif pattern == patterns[5]:
                player_name = match.group(2).strip()
            elif pattern == patterns[6]:
                player_name = match.group(2).strip()
            break

    # If no pattern matched, check for direct player name mentions
    if not player_name:
        # Check if query contains any known player names
        query_lower = query.lower()
        for key, full_name in player_mapping.items():
            if key in query_lower.split():
                player_name = full_name
                break

    # If we found a player name, check if it's a known variation
    if player_name:
        player_name_lower = player_name.lower()
        if player_name_lower in player_mapping:
            player_name = player_mapping[player_name_lower]

        logger.info(f"Extracted player name: {player_name}")
        return player_name

    return ""

def get_realtime_web_data(query: str) -> str:
    """
    Get real-time cricket data from the web based on the query

    Parameters:
    - query: User query

    Returns:
    - String with real-time data or empty string if not available
    """
    # Check if web scraper is available
    if not WEB_SCRAPER_AVAILABLE:
        # Fallback to direct web scraping
        return _direct_web_scrape(query)

    logger.info("Getting real-time web data")

    # Get cricket news if query is about news
    if any(keyword in query.lower() for keyword in ["news", "latest", "update", "headline"]):
        try:
            news = scraper_get_cricket_news()
            if news:
                news_text = []
                for item in news[:5]:  # Limit to 5 news items
                    news_text.append(f"- {item.get('title', 'Unknown')}")
                    if 'summary' in item:
                        news_text.append(f"  {item.get('summary')}")
                    news_text.append(f"  Source: {item.get('source', 'Unknown')}")

                return "\n".join(news_text)
        except Exception as e:
            logger.error(f"Error getting cricket news: {str(e)}")

    # Get live matches if query is about matches
    if any(keyword in query.lower() for keyword in ["match", "game", "score", "playing", "live"]):
        try:
            matches = scraper_get_live_matches()
            if matches:
                match_text = []
                for match in matches:
                    match_text.append(f"- {match.get('teams', 'Unknown teams')}")
                    if 'score1' in match and match['score1']:
                        match_text.append(f"  Score: {match.get('score1', '')} | {match.get('score2', '')}")
                    match_text.append(f"  Status: {match.get('status', 'Unknown')}")
                    match_text.append(f"  Source: {match.get('source', 'Unknown')}")

                return "\n".join(match_text)
        except Exception as e:
            logger.error(f"Error getting live matches: {str(e)}")

    # Fallback to direct web scraping
    return _direct_web_scrape(query)

def get_realtime_player_data(player_name: str) -> Dict[str, Any]:
    """
    Get real-time player data from the web

    Parameters:
    - player_name: Name of the player

    Returns:
    - Dictionary with player data or empty dict if not available
    """
    # Check if web scraper is available
    if not WEB_SCRAPER_AVAILABLE:
        # Fallback to direct web scraping
        return _direct_player_scrape(player_name)

    logger.info(f"Getting real-time player data for {player_name}")

    try:
        player_data = scraper_get_player_stats(player_name)
        if player_data:
            return player_data
    except Exception as e:
        logger.error(f"Error getting player data from web scraper: {str(e)}")

    # Fallback to direct web scraping
    return _direct_player_scrape(player_name)

def get_realtime_match_data() -> List[Dict[str, Any]]:
    """
    Get real-time match data from the web

    Returns:
    - List of dictionaries with match data or empty list if not available
    """
    # Check if web scraper is available
    if not WEB_SCRAPER_AVAILABLE:
        # Fallback to direct web scraping
        return _direct_match_scrape()

    logger.info("Getting real-time match data")

    try:
        match_data = scraper_get_live_matches()
        if match_data:
            return match_data
    except Exception as e:
        logger.error(f"Error getting match data from web scraper: {str(e)}")

    # Fallback to direct web scraping
    return _direct_match_scrape()

def _direct_web_scrape(query: str) -> str:
    """
    Directly scrape cricket data from the web based on the query

    Parameters:
    - query: User query

    Returns:
    - String with scraped data or empty string if not available
    """
    logger.info("Performing direct web scrape")

    try:
        # Define headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # Determine the appropriate URL based on the query
        if any(keyword in query.lower() for keyword in ["match", "game", "score", "playing", "live"]):
            url = "https://www.cricbuzz.com/cricket-match/live-scores"
        elif any(keyword in query.lower() for keyword in ["news", "latest", "update", "headline"]):
            url = "https://www.cricbuzz.com/cricket-news"
        else:
            # Extract player name if present
            player_name = extract_player_name(query)
            if player_name:
                # Encode player name for URL
                encoded_name = player_name.replace(" ", "+")
                url = f"https://www.cricbuzz.com/search?q={encoded_name}"
            else:
                url = "https://www.cricbuzz.com"

        # Fetch the page
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract relevant information based on the URL
        if "live-scores" in url:
            # Extract live match information
            matches = []
            match_elements = soup.select('.cb-mtch-lst')

            for match_element in match_elements[:3]:  # Limit to 3 matches
                try:
                    match_info = match_element.select_one('.cb-lv-scr-mtch-hdr').text.strip()
                    status = match_element.select_one('.cb-lv-scr-mtch-sm').text.strip()
                    matches.append(f"- {match_info}")
                    matches.append(f"  Status: {status}")
                except:
                    continue

            if matches:
                return "LIVE MATCHES FROM WEB:\n" + "\n".join(matches)

        elif "cricket-news" in url:
            # Extract news headlines
            news = []
            news_elements = soup.select('.cb-nws-hdln')

            for news_element in news_elements[:5]:  # Limit to 5 news items
                try:
                    headline = news_element.text.strip()
                    news.append(f"- {headline}")
                except:
                    continue

            if news:
                return "CRICKET NEWS FROM WEB:\n" + "\n".join(news)

        elif "search" in url:
            # Extract player information
            player_info = []
            player_elements = soup.select('.cb-col-100.cb-col')

            for player_element in player_elements[:1]:  # Just the first result
                try:
                    name = player_element.select_one('a').text.strip()
                    details = player_element.select_one('.cb-font-12').text.strip()
                    player_info.append(f"- Name: {name}")
                    player_info.append(f"- Details: {details}")
                except:
                    continue

            if player_info:
                return f"PLAYER INFO FROM WEB:\n" + "\n".join(player_info)

        # If we couldn't extract specific information, return a general message
        return f"Fetched real-time data from {url}, but couldn't extract specific information."

    except Exception as e:
        logger.error(f"Error in direct web scrape: {str(e)}")
        return ""

def _direct_player_scrape(player_name: str) -> Dict[str, Any]:
    """
    Directly scrape player data from the web

    Parameters:
    - player_name: Name of the player

    Returns:
    - Dictionary with player data or empty dict if not available
    """
    logger.info(f"Performing direct player scrape for {player_name}")

    try:
        # Define headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # Encode player name for URL
        encoded_name = player_name.replace(" ", "+")
        url = f"https://www.cricbuzz.com/search?q={encoded_name}"

        # Fetch the search page
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the player link
        player_link = None
        player_elements = soup.select('.cb-col-100.cb-col')

        for player_element in player_elements:
            try:
                link = player_element.select_one('a')
                if link and player_name.lower() in link.text.lower():
                    player_link = "https://www.cricbuzz.com" + link['href']
                    break
            except:
                continue

        if not player_link:
            return {}

        # Fetch the player page
        response = requests.get(player_link, headers=headers)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract player information
        player_data = {
            'name': player_name,
            'source': 'Web (Cricbuzz)',
            'last_updated': datetime.now().isoformat()
        }

        # Extract basic info
        try:
            info_elements = soup.select('.cb-col.cb-col-60.cb-lst-itm-sm')
            for info in info_elements:
                label = info.select_one('.cb-col.cb-col-40.text-bold')
                value = info.select_one('.cb-col.cb-col-60')
                if label and value:
                    key = label.text.strip().lower().replace(' ', '_')
                    player_data[key] = value.text.strip()
        except Exception as e:
            logger.error(f"Error extracting player info: {str(e)}")

        # Extract batting stats
        try:
            batting_table = soup.select_one('.table.cb-col-100.cb-plyr-thead')
            if batting_table:
                rows = batting_table.select('tbody tr')
                for row in rows:
                    cols = row.select('td')
                    if len(cols) >= 7:
                        format_type = cols[0].text.strip()
                        matches = cols[1].text.strip()
                        runs = cols[2].text.strip()
                        avg = cols[5].text.strip()
                        sr = cols[6].text.strip()

                        if format_type.lower() == 'test':
                            player_data['test_matches'] = matches
                            player_data['test_runs'] = runs
                            player_data['test_avg'] = avg
                        elif format_type.lower() == 'odi':
                            player_data['odi_matches'] = matches
                            player_data['odi_runs'] = runs
                            player_data['odi_avg'] = avg
                            player_data['odi_sr'] = sr
                        elif format_type.lower() == 't20i':
                            player_data['t20_matches'] = matches
                            player_data['t20_runs'] = runs
                            player_data['t20_avg'] = avg
                            player_data['t20_sr'] = sr
        except Exception as e:
            logger.error(f"Error extracting batting stats: {str(e)}")

        return player_data

    except Exception as e:
        logger.error(f"Error in direct player scrape: {str(e)}")
        return {}

def _direct_match_scrape() -> List[Dict[str, Any]]:
    """
    Directly scrape match data from the web

    Returns:
    - List of dictionaries with match data or empty list if not available
    """
    logger.info("Performing direct match scrape")

    try:
        # Define headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        url = "https://www.cricbuzz.com/cricket-match/live-scores"

        # Fetch the page
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract match information
        matches = []
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
                    'source': 'Web (Cricbuzz)'
                })
            except Exception as e:
                logger.error(f"Error extracting match info: {str(e)}")
                continue

        return matches

    except Exception as e:
        logger.error(f"Error in direct match scrape: {str(e)}")
        return []

def get_fantasy_recommendations(query: str) -> str:
    """
    Get fantasy cricket recommendations based on the query

    Parameters:
    - query: User query

    Returns:
    - Formatted recommendation string
    """
    if not FANTASY_RECOMMENDATIONS_AVAILABLE:
        return "Fantasy recommendations are not available. Please check if the fantasy_recommendations module is installed."

    logger.info("Generating fantasy recommendations")

    # Check if this is a differential pick query
    differential_keywords = ["differential", "differentials", "under the radar", "low ownership", "unique pick"]
    is_differential_query = any(keyword in query.lower() for keyword in differential_keywords)

    # Check if this is a captain pick query
    captain_keywords = ["captain", "vice-captain", "vc", "multiplier", "double points"]
    is_captain_query = any(keyword in query.lower() for keyword in captain_keywords)

    # Check if this is a player comparison query
    comparison_keywords = ["compare", "versus", "vs", "or", "better pick", "should i pick"]
    is_comparison_query = any(keyword in query.lower() for keyword in comparison_keywords)

    # Handle differential pick query
    if is_differential_query:
        return _get_differential_picks_response()

    # Handle captain pick query
    elif is_captain_query:
        return _get_captain_picks_response()

    # Handle player comparison query
    elif is_comparison_query:
        # Extract player names
        player_names = extract_player_comparison_names(query)
        if len(player_names) >= 2:
            return _get_player_comparison_response(player_names[0], player_names[1])
        else:
            return "I couldn't identify the players you want to compare. Please specify two player names clearly."

    # General fantasy advice
    else:
        return _get_general_fantasy_advice()

def _get_differential_picks_response() -> str:
    """Get response for differential picks query"""
    try:
        differential_picks = get_differential_picks()

        if not differential_picks:
            return "I couldn't find any good differential picks for upcoming matches. Please check back later when more match data is available."

        response = ["# 🎯 Differential Picks for Fantasy Cricket", ""]
        response.append("Here are some under-the-radar players who could give you an edge:")
        response.append("")

        for i, pick in enumerate(differential_picks, 1):
            name = pick.get('name', f"Player {i}")
            team = pick.get('team', 'Unknown team')
            role = pick.get('role', 'Unknown role')
            score = pick.get('differential_score', 0)
            reasoning = pick.get('reasoning', '')

            response.append(f"## {i}. {name} ({team}, {role})")
            response.append(f"**Differential Score:** {score}/10")
            response.append(f"**Why:** {reasoning}")
            response.append("")

        response.append("*Differential picks are players with lower ownership who could outperform expectations*")

        return "\n".join(response)
    except Exception as e:
        logger.error(f"Error getting differential picks: {str(e)}")
        return "I'm having trouble generating differential picks right now. Please try again later."

def _get_captain_picks_response() -> str:
    """Get response for captain picks query"""
    try:
        captain_picks = get_captain_picks()

        if not captain_picks:
            return "I couldn't find any good captain picks for upcoming matches. Please check back later when more match data is available."

        response = ["# 👑 Captain & Vice-Captain Picks", ""]
        response.append("Here are the best captain and vice-captain choices for your fantasy team:")
        response.append("")

        # Group by recommendation
        captains = [pick for pick in captain_picks if pick.get('recommendation') == 'Captain']
        vice_captains = [pick for pick in captain_picks if pick.get('recommendation') == 'Vice-Captain']

        # Add captains
        response.append("## Captain Picks (2x points)")
        for i, pick in enumerate(captains, 1):
            name = pick.get('name', f"Player {i}")
            team = pick.get('team', 'Unknown team')
            role = pick.get('role', 'Unknown role')
            score = pick.get('captain_score', 0)
            reasoning = pick.get('reasoning', '')

            response.append(f"### {i}. {name} ({team}, {role})")
            response.append(f"**Captain Score:** {score}/10")
            response.append(f"**Why:** {reasoning}")
            response.append("")

        # Add vice-captains
        response.append("## Vice-Captain Picks (1.5x points)")
        for i, pick in enumerate(vice_captains, 1):
            name = pick.get('name', f"Player {i}")
            team = pick.get('team', 'Unknown team')
            role = pick.get('role', 'Unknown role')
            score = pick.get('captain_score', 0)
            reasoning = pick.get('reasoning', '')

            response.append(f"### {i}. {name} ({team}, {role})")
            response.append(f"**VC Score:** {score}/10")
            response.append(f"**Why:** {reasoning}")
            response.append("")

        return "\n".join(response)
    except Exception as e:
        logger.error(f"Error getting captain picks: {str(e)}")
        return "I'm having trouble generating captain picks right now. Please try again later."

def _get_player_comparison_response(player1: str, player2: str) -> str:
    """Get response for player comparison query"""
    try:
        comparison = compare_players(player1, player2)

        if 'error' in comparison:
            return f"I couldn't compare {player1} and {player2}: {comparison.get('error', 'Unknown error')}"

        response = [f"# 🔄 {player1} vs {player2}", ""]

        # Add recommendation
        recommendation = comparison.get('recommendation', '')
        reasoning = comparison.get('reasoning', '')

        response.append(f"## Recommendation")
        response.append(f"**{recommendation}**")
        response.append(f"*{reasoning}*")
        response.append("")

        # Add player 1 stats
        player1_stats = comparison.get('player1', {}).get('stats', {})
        player1_score = comparison.get('player1', {}).get('score', 0)

        response.append(f"## {player1} (Score: {player1_score}/10)")
        for stat, value in player1_stats.items():
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
                response.append(f"- **{stat}:** {value_str}")
            else:
                response.append(f"- **{stat}:** {value}")
        response.append("")

        # Add player 2 stats
        player2_stats = comparison.get('player2', {}).get('stats', {})
        player2_score = comparison.get('player2', {}).get('score', 0)

        response.append(f"## {player2} (Score: {player2_score}/10)")
        for stat, value in player2_stats.items():
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
                response.append(f"- **{stat}:** {value_str}")
            else:
                response.append(f"- **{stat}:** {value}")

        return "\n".join(response)
    except Exception as e:
        logger.error(f"Error comparing players: {str(e)}")
        return f"I'm having trouble comparing {player1} and {player2} right now. Please try again later."

def _get_general_fantasy_advice() -> str:
    """Get general fantasy cricket advice"""
    advice = [
        "# 🏏 Fantasy Cricket Advice",
        "",
        "Here are some general tips for your fantasy cricket team:",
        "",
        "## Team Selection",
        "- **Balance is key**: Include a mix of batsmen, bowlers, all-rounders, and a wicketkeeper",
        "- **Check the pitch report**: Select more batsmen for batting-friendly pitches and more bowlers for bowling-friendly pitches",
        "- **Consider recent form**: Players in good form are more likely to perform well",
        "- **Look at matchups**: Some players perform better against certain teams",
        "- **Check playing XI**: Make sure your selected players are in the playing XI",
        "",
        "## Captain Selection",
        "- **Choose all-rounders**: They have multiple ways to score points",
        "- **Consider form**: Players in excellent form are good captain choices",
        "- **Match conditions**: Pick batsmen as captains on flat tracks and bowlers on helpful pitches",
        "- **Consistency matters**: Choose consistent performers over boom-or-bust players",
        "",
        "## Budget Management",
        "- **Find value picks**: Look for in-form players with lower prices",
        "- **Don't overspend on one player**: Distribute your budget across the team",
        "- **Include some differentials**: Low-ownership players can give you an edge",
        "",
        "For specific player recommendations, ask me about differential picks, captain choices, or player comparisons!"
    ]

    return "\n".join(advice)

def extract_player_comparison_names(query: str) -> List[str]:
    """Extract player names from a comparison query"""
    # Look for patterns like "X or Y", "X vs Y", "compare X and Y"
    patterns = [
        r'([A-Za-z ]+) or ([A-Za-z ]+)',
        r'([A-Za-z ]+) vs\.? ([A-Za-z ]+)',
        r'([A-Za-z ]+) versus ([A-Za-z ]+)',
        r'compare ([A-Za-z ]+) (?:and|with) ([A-Za-z ]+)',
        r'should i pick ([A-Za-z ]+) or ([A-Za-z ]+)',
        r'who\'s better,? ([A-Za-z ]+) or ([A-Za-z ]+)',
        r'who should i pick,? ([A-Za-z ]+) or ([A-Za-z ]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            player1 = match.group(1).strip()
            player2 = match.group(2).strip()

            # Filter out common words that aren't player names
            non_player_words = ["player", "batsman", "bowler", "all-rounder", "captain", "vice-captain", "vc"]
            if player1.lower() in non_player_words or player2.lower() in non_player_words:
                continue

            return [player1, player2]

    # If no pattern matched, try to extract known player names
    known_players = [
        "Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "MS Dhoni", "Kane Williamson",
        "Steve Smith", "Ben Stokes", "Babar Azam", "Rashid Khan", "Kagiso Rabada",
        "KL Rahul", "Hardik Pandya", "Ravindra Jadeja", "David Warner", "Pat Cummins",
        "Mitchell Starc", "Glenn Maxwell", "Joe Root", "Jofra Archer", "Jos Buttler",
        "Eoin Morgan", "Trent Boult", "Ross Taylor", "Tim Southee", "Martin Guptill",
        "Shaheen Afridi", "Mohammad Rizwan", "Shadab Khan", "Fakhar Zaman", "Quinton de Kock",
        "Anrich Nortje", "David Miller", "Aiden Markram", "Kieron Pollard", "Nicholas Pooran",
        "Jason Holder", "Shimron Hetmyer", "Andre Russell", "Wanindu Hasaranga", "Dushmantha Chameera",
        "Charith Asalanka", "Pathum Nissanka", "Shakib Al Hasan", "Mushfiqur Rahim", "Mustafizur Rahman",
        "Mahmudullah", "Mohammad Nabi", "Mujeeb Ur Rahman", "Rahmanullah Gurbaz"
    ]

    found_players = []
    for player in known_players:
        if player.lower() in query.lower() or player.split()[-1].lower() in query.lower():
            found_players.append(player)

    return found_players

def get_formatted_player_stats(player_name: str):
    """
    Return a pre-formatted response with player statistics

    Parameters:
    - player_name: Name of the player

    Returns:
    - Formatted markdown string with player statistics
    """
    from cricket_data_adapter import get_player_stats

    # Get player stats
    player_stats = get_player_stats(player_name)

    if not player_stats:
        return f"Sorry, I couldn't find statistics for {player_name}."

    # Format the response
    response = [f"# 🏏 {player_stats.get('name', player_name)} - Statistics"]

    # Career Overview
    response.append("\n## 📊 Career Overview")
    response.append(f"- **Team:** {player_stats.get('team', 'Unknown')}")
    response.append(f"- **Role:** {player_stats.get('role', 'Unknown')}")

    if 'matches_played' in player_stats:
        response.append(f"- **Matches Played:** {player_stats.get('matches_played', 0)}")

    if 'runs' in player_stats:
        response.append(f"- **Total Runs:** {player_stats.get('runs', 0)}")

    if 'hundreds' in player_stats and 'fifties' in player_stats:
        response.append(f"- **Centuries:** {player_stats.get('hundreds', 0)}")
        response.append(f"- **Fifties:** {player_stats.get('fifties', 0)}")

    if 'highest_score' in player_stats:
        response.append(f"- **Highest Score:** {player_stats.get('highest_score', 0)}")

    # Batting Statistics
    if any(key in player_stats for key in ['batting_avg', 'strike_rate']):
        response.append("\n## 📈 Batting Statistics")

        if 'batting_avg' in player_stats:
            response.append(f"- **Batting Average:** {player_stats.get('batting_avg', 0)}")

        if 'strike_rate' in player_stats:
            response.append(f"- **Strike Rate:** {player_stats.get('strike_rate', 0)}")

    # Bowling Statistics
    if any(key in player_stats for key in ['bowling_avg', 'economy', 'wickets']):
        response.append("\n## 🎯 Bowling Statistics")

        if 'wickets' in player_stats:
            response.append(f"- **Wickets:** {player_stats.get('wickets', 0)}")

        if 'bowling_avg' in player_stats:
            response.append(f"- **Bowling Average:** {player_stats.get('bowling_avg', 0)}")

        if 'economy' in player_stats:
            response.append(f"- **Economy Rate:** {player_stats.get('economy', 0)}")

        if 'best_bowling' in player_stats:
            response.append(f"- **Best Bowling:** {player_stats.get('best_bowling', 'Unknown')}")

    # Recent Form
    response.append("\n## 🔥 Recent Form")

    if 'recent_form' in player_stats:
        response.append(f"- **Recent Scores:** {', '.join(map(str, player_stats.get('recent_form', [])))}")

    if 'recent_wickets' in player_stats:
        response.append(f"- **Recent Wickets:** {', '.join(map(str, player_stats.get('recent_wickets', [])))}")

    form = player_stats.get('current_form', 'Unknown')
    response.append(f"- **Current Form:** {form.capitalize() if form else 'Unknown'}")

    if 'fantasy_points_avg' in player_stats:
        response.append(f"- **Fantasy Points Average:** {player_stats.get('fantasy_points_avg', 0)}")

    # Source and Last Updated
    response.append(f"\n*Data Source: {player_stats.get('source', 'Unknown')}*")

    if 'last_updated' in player_stats:
        try:
            from datetime import datetime
            last_updated = datetime.fromisoformat(player_stats['last_updated'])
            response.append(f"*Last Updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}*")
        except:
            response.append(f"*Last Updated: {player_stats['last_updated']}*")

    return "\n".join(response)

def process_cricket_query(query):
    """
    Process a cricket-related query using Gemini with relevant context
    """
    # Check if Gemini is available
    if not GEMINI_AVAILABLE:
        logger.warning("Gemini API not available, falling back to rule-based system")
        # Import the fallback assistant function
        from assistant import generate_response
        return generate_response(query) + "\n\n(Response generated using rule-based system due to Gemini API not being available)"

    try:
        logger.info(f"Processing query with Gemini: {query[:50]}...")

        # Check if this is a player stats query
        player_stats_keywords = ["stats", "statistics", "batting", "bowling", "average", "performance", "record", "form"]
        is_player_stats_query = any(keyword in query.lower() for keyword in player_stats_keywords)

        if is_player_stats_query:
            # Try to extract player name
            player_name = extract_player_name(query)

            if player_name:
                logger.info(f"Using pre-formatted response for {player_name} stats query")
                return get_formatted_player_stats(player_name)

        # Check if this is a general cricket knowledge question
        general_knowledge_keywords = [
            "who is", "what is", "when is", "where is", "why is", "how is",
            "highest", "lowest", "most", "best", "worst", "record", "ranking", "icc",
            "world cup", "history", "rules", "explain", "top", "greatest", "famous"
        ]

        is_general_knowledge = any(keyword in query.lower() for keyword in general_knowledge_keywords)

        # Check if this is a player-specific query
        player_keywords = ["virat", "kohli", "rohit", "sharma", "dhoni", "bumrah", "williamson",
                          "smith", "stokes", "babar", "azam", "kane", "steve", "ben", "ms"]

        is_player_query = any(keyword in query.lower().split() for keyword in player_keywords)

        # Get relevant cricket context
        context = enrich_query_with_context(query)
        logger.info(f"Context enriched: {len(context) if context else 0} characters")

        # If this is a player query but we don't have context, try to force download player data
        if is_player_query and (not context or len(context if context else "") < 50):
            logger.info("Player query detected with insufficient context, attempting to force download player data")

            # Try to extract player name
            import re
            player_name = None

            # Define common player full names and their variations
            player_mapping = {
                "virat": "Virat Kohli",
                "kohli": "Virat Kohli",
                "rohit": "Rohit Sharma",
                "sharma": "Rohit Sharma",
                "bumrah": "Jasprit Bumrah",
                "jasprit": "Jasprit Bumrah",
                "dhoni": "MS Dhoni",
                "ms": "MS Dhoni",
                "williamson": "Kane Williamson",
                "kane": "Kane Williamson",
                "babar": "Babar Azam",
                "azam": "Babar Azam",
                "stokes": "Ben Stokes",
                "ben": "Ben Stokes",
                "smith": "Steve Smith",
                "steve": "Steve Smith"
            }

            # Check if query contains any known player names
            query_lower = query.lower()
            for key, full_name in player_mapping.items():
                if key in query_lower.split():
                    player_name = full_name
                    break

            if player_name:
                logger.info(f"Forcing download of data for {player_name}")
                if CRICSHEET_ENABLED:
                    try:
                        from cricsheet_parser import get_player_stats as cricsheet_get_player_stats
                        cricsheet_player = cricsheet_get_player_stats(player_name)
                        if cricsheet_player:
                            logger.info(f"Successfully retrieved Cricsheet data for {player_name}")
                            # Try to get context again
                            context = enrich_query_with_context(query)
                            logger.info(f"Context re-enriched: {len(context) if context else 0} characters")
                    except Exception as e:
                        logger.error(f"Error getting Cricsheet data for {player_name}: {str(e)}")

        # If this is a general knowledge question and we don't have context, use system instruction
        if is_general_knowledge and (not context or len(context if context else "") < 50):
            logger.info("General cricket knowledge question detected with insufficient context")
            # Use a special prompt for general knowledge
            prompt = f"{system_instruction}\n\nUSER QUERY: {query}\n\nPlease answer this general cricket knowledge question to the best of your ability. If you don't know the answer, please say so rather than making up information."
            response = model.generate_content(prompt)

            if hasattr(response, 'text'):
                logger.info(f"Gemini response generated for general knowledge question: {len(response.text)} characters")
                return response.text

        # For player queries, make sure we have detailed information
        if is_player_query and context:
            # Check if the context contains detailed player information
            if "PLAYER INFO" in context and "Source: Cricsheet" not in context:
                logger.info("Player query detected but Cricsheet data not found in context, trying to add more details")

                # Try to extract player name from context
                import re
                player_name_match = re.search(r'PLAYER INFO - ([A-Za-z ]+):', context)
                if player_name_match:
                    player_name = player_name_match.group(1).strip()
                    logger.info(f"Extracted player name from context: {player_name}")

                    # Add more detailed information about the player
                    additional_info = []
                    additional_info.append(f"\nAdditional information about {player_name}:")

                    # Add some general information about the player
                    if "Virat Kohli" in player_name:
                        additional_info.append("Virat Kohli is one of the greatest batsmen in cricket history, known for his aggressive batting style and exceptional consistency across all formats.")
                        additional_info.append("He has scored over 70 international centuries and is considered one of the best chasers in ODI cricket.")
                        additional_info.append("He has been the captain of the Indian cricket team and is known for his fitness and intensity on the field.")
                    elif "Rohit Sharma" in player_name:
                        additional_info.append("Rohit Sharma is known as the 'Hitman' for his ability to hit big sixes and is the current captain of the Indian cricket team.")
                        additional_info.append("He holds the record for the highest individual score in ODIs (264) and has scored three double centuries in ODIs.")
                    elif "MS Dhoni" in player_name:
                        additional_info.append("MS Dhoni is one of the greatest finishers and wicketkeeper-batsmen in cricket history.")
                        additional_info.append("He led India to victory in the 2007 T20 World Cup, 2011 ODI World Cup, and 2013 Champions Trophy.")

                    # Add this information to the context
                    if additional_info:
                        enhanced_context = context + "\n" + "\n".join(additional_info)
                        logger.info("Enhanced context with additional player information")
                        context = enhanced_context

        # Generate response with context
        logger.info("Generating Gemini response...")
        response = generate_gemini_response(query, context)
        logger.info(f"Gemini response generated: {len(response) if response else 0} characters")

        # Check if the response indicates lack of information
        lack_of_info_phrases = [
            "does not contain information",
            "doesn't contain information",
            "I cannot answer your question using the given context",
            "I don't have information",
            "I don't have enough information",
            "I don't have the information",
            "I don't have that information",
            "The provided text",
            "The context provided",
            "Based on the context provided",
            "The information provided"
        ]

        if response and any(phrase in response for phrase in lack_of_info_phrases):
            logger.info("Response indicates lack of information, trying general knowledge approach")
            # Try again with a general knowledge approach
            prompt = f"{system_instruction}\n\nUSER QUERY: {query}\n\nPlease answer this general cricket knowledge question to the best of your ability. If you don't know the answer, please say so rather than making up information."
            new_response = model.generate_content(prompt)

            if hasattr(new_response, 'text'):
                logger.info(f"New Gemini response generated: {len(new_response.text)} characters")
                return new_response.text

        return response
    except Exception as e:
        logger.error(f"Error processing query with Gemini: {str(e)}")
        # Try one more time with a direct approach before falling back to rule-based
        try:
            logger.info("Trying direct approach without context after error")
            prompt = f"{system_instruction}\n\nUSER QUERY: {query}\n\nPlease answer this cricket question to the best of your ability."
            direct_response = model.generate_content(prompt)

            if hasattr(direct_response, 'text'):
                logger.info(f"Direct Gemini response generated: {len(direct_response.text)} characters")
                return direct_response.text
        except Exception as second_e:
            logger.error(f"Error with direct approach: {str(second_e)}")

        # Only fall back to rule-based as a last resort
        from assistant import generate_response
        return generate_response(query) + f"\n\n(Fallback response due to error: {str(e)})"