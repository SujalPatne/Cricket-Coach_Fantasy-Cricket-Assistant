import os
from openai import OpenAI
from typing import Dict, List, Any, Optional
import logging
from cricket_data_adapter import get_live_cricket_matches, get_upcoming_matches, get_player_stats, get_pitch_conditions
from config import OPENAI_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

# Configure the OpenAI API with the API key
try:
    # Initialize the OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Test the client with a simple request
    models = client.models.list()

    OPENAI_AVAILABLE = True
    logger.info("OpenAI API initialized successfully")

except Exception as e:
    OPENAI_AVAILABLE = False
    client = None
    logger.error(f"Error initializing OpenAI API: {str(e)}")

# System instructions for the assistant
system_instruction = """
You are a Fantasy Cricket Assistant. Your purpose is to help cricket fans make informed decisions for their fantasy teams.
Provide concise, informative responses about cricket players, match conditions, and fantasy strategy.

Use these guidelines:
1. Always focus on facts and data when available
2. Explain your reasoning for player recommendations
3. Consider factors like current form, pitch conditions, and matchups
4. Keep responses conversational but informative
5. Don't make up statistics - if you don't know, say so
6. Provide structured, easily readable responses with emojis for visual distinction
7. When recommending players, explain why they're good picks

Remember that users rely on your advice for their fantasy teams, so be accurate and helpful.
"""

def generate_openai_response(query: str, context: Optional[str] = None) -> str:
    """
    Generate a response using OpenAI's model with the provided context

    Parameters:
    - query: User's question or request
    - context: Optional contextual information about cricket data

    Returns:
    - Response from OpenAI
    """
    # Check if API is available
    if not OPENAI_AVAILABLE:
        return "OpenAI model not available. Please check your API key configuration."

    try:
        # Create a prompt with context if provided
        if context:
            prompt = f"CONTEXT:\n{context}\n\nUSER QUERY: {query}\n\nPlease answer the query using the provided context and format your response with appropriate emojis for readability. If you're recommending cricket players, explain why they're good picks."
        else:
            prompt = f"{system_instruction}\n\nUSER QUERY: {query}"

        # Generate response using OpenAI's chat completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # You can change to a different model if needed
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )

        # Extract the text from the response
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "I couldn't generate a response at the moment. Please try again."

    except Exception as e:
        logger.error(f"Error generating OpenAI response: {str(e)}")
        return f"I'm having trouble connecting to my knowledge base right now. Please try again later. Technical details: {str(e)}"

def enrich_query_with_context(query: str) -> str:
    """
    Enrich the user query with relevant cricket context before sending to OpenAI
    """
    context = []

    # Add live match information if relevant
    if any(keyword in query.lower() for keyword in ["live", "current", "today", "match", "playing", "score", "ongoing"]):
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

    # Add upcoming match information if relevant
    if any(keyword in query.lower() for keyword in ["upcoming", "schedule", "next", "future", "tomorrow", "fixtures"]):
        upcoming_matches = get_upcoming_matches()
        if upcoming_matches:
            context.append("\nUPCOMING MATCHES:")
            for match in upcoming_matches[:5]:  # Limit to 5 matches to avoid context overflow
                source = match.get('source', 'Unknown')
                match_info = f"- {match.get('teams', 'Match')} | {match.get('date', 'Date unknown')} | {match.get('venue', 'Venue unknown')} | Source: {source}"
                context.append(match_info)

                # Add match format
                if 'match_type' in match:
                    context.append(f"  Format: {match.get('match_type')}")

    # Add recent matches information if relevant
    if any(keyword in query.lower() for keyword in ["recent", "last", "previous", "completed", "finished", "results"]):
        from cricket_data_adapter import get_recent_matches
        recent_matches = get_recent_matches()
        if recent_matches:
            context.append("\nRECENT MATCHES:")
            for match in recent_matches[:5]:  # Limit to 5 matches
                source = match.get('source', 'Unknown')
                match_info = f"- {match.get('teams', 'Match')} | {match.get('status', 'Status unknown')} | {match.get('venue', 'Venue unknown')} | Source: {source}"
                context.append(match_info)

    # Add player information if query mentions a specific player
    import re
    player_match = re.search(r'(stats|statistics|info|about|how is|form|performance of) ([A-Za-z ]+)', query, re.IGNORECASE)
    if player_match:
        player_name = player_match.group(2).strip()
        player_info = get_player_stats(player_name)
        if player_info:
            context.append(f"\nPLAYER INFORMATION for {player_name}:")
            # Include source information
            context.append(f"- Source: {player_info.get('source', 'Unknown')}")
            for key, value in player_info.items():
                if key not in ['name', 'id', 'source']:  # Skip redundant info
                    context.append(f"- {key}: {value}")

            # Add player form information
            player_form = get_player_form(player_name)
            context.append(f"- Current form: {player_form}")
    else:
        # Check for common player names if no specific pattern is found
        player_names = ["Kohli", "Rohit", "Bumrah", "Dhoni", "Williamson", "Babar", "Stokes", "Smith"]
        for player in player_names:
            if player.lower() in query.lower():
                player_info = get_player_stats(player)
                if player_info:
                    context.append(f"\nPLAYER INFORMATION for {player}:")
                    # Include source information
                    context.append(f"- Source: {player_info.get('source', 'Unknown')}")
                    for key, value in player_info.items():
                        if key not in ['name', 'id', 'source']:  # Skip redundant info
                            context.append(f"- {key}: {value}")

                    # Add player form information
                    player_form = get_player_form(player)
                    context.append(f"- Current form: {player_form}")

    # Add pitch conditions if relevant
    if any(keyword in query.lower() for keyword in ["pitch", "ground", "stadium", "conditions", "weather"]):
        pitch_match = re.search(r'(pitch|ground|stadium|conditions) (in|at|of) ([A-Za-z ]+)', query, re.IGNORECASE)
        if pitch_match:
            venue = pitch_match.group(3).strip()
            pitch_info = get_pitch_conditions(venue)
            if pitch_info:
                context.append(f"\nPITCH CONDITIONS at {venue}:")
                for key, value in pitch_info.items():
                    context.append(f"- {key}: {value}")
        else:
            # Check for common venues if no specific pattern is found
            venues = ["Mumbai", "Chennai", "Kolkata", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Dharamsala"]
            for venue in venues:
                if venue.lower() in query.lower():
                    pitch_info = get_pitch_conditions(venue)
                    if pitch_info:
                        context.append(f"\nPITCH CONDITIONS at {venue}:")
                        context.append(f"- Batting friendly: {pitch_info.get('batting_friendly', 'Unknown')}/10")
                        context.append(f"- Pace bowling friendly: {pitch_info.get('pace_friendly', 'Unknown')}/10")
                        context.append(f"- Spin friendly: {pitch_info.get('spin_friendly', 'Unknown')}/10")

    # Join all context information
    return "\n".join(context)

def process_cricket_query(query: str) -> str:
    """
    Process a cricket-related query using OpenAI with relevant context
    """
    # Check if OpenAI is available
    if not OPENAI_AVAILABLE:
        # Import the fallback assistant function
        from assistant import generate_response
        return generate_response(query) + "\n\n(Response generated using rule-based system due to OpenAI API not being available)"

    try:
        # Get relevant cricket context
        context = enrich_query_with_context(query)

        # Generate response with context
        response = generate_openai_response(query, context)

        return response
    except Exception as e:
        logger.error(f"Error processing query with OpenAI: {str(e)}")
        # Fallback to rule-based responses
        from assistant import generate_response
        return generate_response(query) + f"\n\n(Fallback response due to error: {str(e)})"
