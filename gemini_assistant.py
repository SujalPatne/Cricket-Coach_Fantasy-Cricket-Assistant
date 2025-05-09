import os
import google.generativeai as genai
from cricket_scraper import get_live_cricket_matches, get_upcoming_matches, get_player_stats, get_pitch_conditions

# Configure the Gemini API with the API key
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Set up the model
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    system_instruction="""
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
)

def generate_gemini_response(query, context=None):
    """
    Generate a response using Gemini's model with the provided context
    
    Parameters:
    - query: User's question or request
    - context: Optional contextual information about cricket data
    
    Returns:
    - Response from Gemini
    """
    try:
        # Create a prompt with context if provided
        if context:
            prompt = f"CONTEXT:\n{context}\n\nUSER QUERY: {query}\n\nPlease answer the query using the provided context."
        else:
            prompt = query
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract the text from the response
        if hasattr(response, 'text'):
            return response.text
        else:
            return "I couldn't generate a response at the moment. Please try again."
    
    except Exception as e:
        print(f"Error generating Gemini response: {str(e)}")
        return f"I'm having trouble connecting to my knowledge base right now. Please try again later. Technical details: {str(e)}"

def enrich_query_with_context(query):
    """
    Enrich the user query with relevant cricket context before sending to Gemini
    """
    context = []
    
    # Add live match information if relevant
    if any(keyword in query.lower() for keyword in ["live", "current", "today", "match", "playing", "score"]):
        live_matches = get_live_cricket_matches()
        if live_matches:
            context.append("LIVE MATCHES:")
            for match in live_matches:
                match_info = f"- {match.get('teams', 'Match')} | {match.get('status', 'Status unknown')} | {match.get('venue', 'Venue unknown')}"
                context.append(match_info)
    
    # Add player information if the query mentions a player
    player_names = ["Kohli", "Rohit", "Bumrah", "Dhoni", "Williamson", "Babar", "Stokes", "Smith"]
    for player in player_names:
        if player.lower() in query.lower():
            player_info = get_player_stats(player)
            if player_info:
                context.append(f"PLAYER INFO - {player}:")
                for key, value in player_info.items():
                    context.append(f"- {key}: {value}")
    
    # Add upcoming match information if relevant
    if any(keyword in query.lower() for keyword in ["upcoming", "schedule", "next", "future", "coming", "fixtures"]):
        upcoming = get_upcoming_matches()
        if upcoming:
            context.append("UPCOMING MATCHES:")
            for match in upcoming:
                match_info = f"- {match.get('teams', 'Match')} | {match.get('date', 'Date unknown')} | {match.get('venue', 'Venue unknown')}"
                context.append(match_info)
    
    # Add pitch information if venues are mentioned
    venues = ["Mumbai", "Chennai", "Kolkata", "Delhi", "Bangalore", "Hyderabad"]
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

def process_cricket_query(query):
    """
    Process a cricket-related query using Gemini with relevant context
    """
    # Get relevant cricket context
    context = enrich_query_with_context(query)
    
    # Generate response with context
    response = generate_gemini_response(query, context)
    
    return response