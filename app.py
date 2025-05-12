import streamlit as st
from streamlit_chat import message
import pandas as pd
import random
import time
import os
import importlib
import uuid
import logging
from datetime import datetime, timedelta

# Import custom modules
from cricket_data import get_player_stats, get_recommended_players, get_player_form
from assistant import generate_response, GREETING_MESSAGE
from fantasy_rules import get_fantasy_rule_explanation
from ai_manager import AIManager, AIModel
from db_manager import DatabaseManager
from auth import initialize_session_state, render_login_ui
from visualizations import player_performance_chart, team_comparison_chart, fantasy_points_projection
from logger import get_logger, log_access, log_error, log_chat, ErrorHandler

# Set up logging
logger = get_logger(__name__)

# Use the cricket data adapter for real-time data with fallback
from cricket_data_adapter import (
    get_live_cricket_matches,
    get_upcoming_matches,
    get_pitch_conditions,
    get_player_stats,
    get_recommended_players,
    get_player_form,
    CRICKET_API_AVAILABLE
)

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

if CRICKET_API_AVAILABLE:
    logger.info("Using real-time cricket data from API")
else:
    logger.info("Cricket API not available, using reliable fallback data")

# Page configuration
st.set_page_config(
    page_title="Fantasy Cricket Assistant",
    page_icon="🏏",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/yourusername/fantasy-cricket-assistant',
        'Report a bug': 'https://github.com/yourusername/fantasy-cricket-assistant/issues',
        'About': 'Fantasy Cricket Assistant - Your AI-powered cricket fantasy league advisor'
    }
)

# Set up page styling for better chat appearance
st.markdown("""
<style>
.user-message {
    background-color: #1A73E8;
    color: white;
    border-radius: 20px 20px 0 20px;
    padding: 10px 15px;
    margin: 5px 0;
    text-align: right;
    max-width: 80%;
    float: right;
    clear: both;
}
.assistant-message {
    background-color: #F8F9FA;
    color: #202124;
    border-radius: 20px 20px 20px 0;
    padding: 10px 15px;
    margin: 5px 0;
    text-align: left;
    max-width: 80%;
    float: left;
    clear: both;
}
.streamlit-chat-message {
    margin-bottom: 15px !important;
}

/* Status message styling */
.status-message {
    background-color: #F0F8FF;
    border-left: 5px solid #1A73E8;
    padding: 10px;
    margin: 10px 0;
    border-radius: 5px;
    font-size: 14px;
    animation: pulse 2s infinite;
}

/* Pulse animation for status messages */
@keyframes pulse {
    0% { opacity: 0.7; }
    50% { opacity: 1; }
    100% { opacity: 0.7; }
}

/* Style for the info messages */
div[data-testid="stInfo"] {
    background-color: #E8F0FE;
    border-left: 5px solid #1A73E8;
    padding: 10px 15px;
    border-radius: 4px;
    margin: 10px 0;
    font-size: 14px;
    animation: pulse 2s infinite;
}

/* Style for error messages */
div[data-testid="stError"] {
    background-color: #FEECEC;
    border-left: 5px solid #EA4335;
    padding: 10px 15px;
    border-radius: 4px;
    margin: 10px 0;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = [GREETING_MESSAGE]
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

# Initialize authentication state
initialize_session_state()

# Initialize AI manager
if 'ai_manager' not in st.session_state:
    logger.info("Creating new AI manager")

    # Force Gemini as default since we know it's working
    st.session_state['ai_manager'] = AIManager(default_model=AIModel.GEMINI)

    # Log available models
    available_models = st.session_state['ai_manager'].get_available_models()
    logger.info(f"Available AI models: {available_models}")
    logger.info(f"Default model: {st.session_state['ai_manager'].default_model.value}")

    # Make sure Gemini is set as default if available
    if AIModel.GEMINI.value in available_models:
        st.session_state['ai_manager'].set_default_model(AIModel.GEMINI)
        logger.info("Gemini set as default model")

# Initialize database manager
if 'db_manager' not in st.session_state:
    st.session_state['db_manager'] = DatabaseManager()

    # Migrate data from JSON files to database if needed
    try:
        st.session_state['db_manager'].migrate_from_json()
    except Exception as e:
        logger.error(f"Error migrating data: {str(e)}")

# Initialize visualization state
if 'show_visualization' not in st.session_state:
    st.session_state['show_visualization'] = False
if 'visualization_type' not in st.session_state:
    st.session_state['visualization_type'] = None
if 'visualization_params' not in st.session_state:
    st.session_state['visualization_params'] = {}

def get_text():
    """Get the user input text"""
    # Simple text input without callbacks when used in a form
    return st.text_input(
        "You: ",
        key="input_text"
    )

def set_user_input():
    """Set the user input in session state when the input field changes"""
    st.session_state['user_input'] = st.session_state.input_text

# Function removed as we're using st.form for Enter key handling

def process_input():
    """Process the input and return a response"""
    # Import time module at the function level to avoid scoping issues
    import time

    user_input = st.session_state.user_input
    if not user_input:
        return

    # Reset user_input but NOT input_text as that would cause an error
    # since we can't modify widget values after creation
    st.session_state.user_input = ""

    # Add user message to chat history
    st.session_state.past.append(user_input)

    # Log access
    log_access(
        user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
        endpoint="chat",
        method="POST"
    )

    # Use the status container to show detailed status messages
    with status_container:
        # Create a placeholder for the status message
        status_placeholder = st.empty()

        # Show initial "thinking" message
        status_placeholder.info("⌛ The assistant is thinking...")

        # Process the query with detailed status updates
        try:
            # Process query with AI manager
            ai_manager = st.session_state['ai_manager']

            # Import the player name extraction function
            from gemini_assistant import extract_player_name

            # Check if query is about player stats
            if any(keyword in user_input.lower() for keyword in ["stats", "statistics", "info", "about", "player", "form", "performance"]):
                player_name = extract_player_name(user_input)

                if player_name:
                    # Show a sequence of loading messages to indicate what's happening
                    status_placeholder.info(f"⌛ Fetching statistics for {player_name}...")

                    # Add a more detailed status after a short delay
                    time.sleep(0.5)

                    # Check if we have cached data
                    import os
                    normalized_name = player_name.lower().replace(" ", "_")
                    cache_file = os.path.join("cricsheet_data/cache", f"player_{normalized_name}.json")

                    if os.path.exists(cache_file):
                        # Check how old the cache is
                        cache_age = time.time() - os.path.getmtime(cache_file)
                        if cache_age < 24 * 60 * 60:  # Less than 24 hours old
                            status_placeholder.info(f"⌛ Loading cached data for {player_name}...")
                            time.sleep(0.5)
                            status_placeholder.info(f"⌛ Checking for real-time updates from Cricbuzz...")
                        else:
                            status_placeholder.info(f"⌛ Cached data is outdated. Refreshing statistics for {player_name}...")
                            time.sleep(0.5)
                            status_placeholder.info(f"⌛ Downloading and analyzing {player_name}'s recent performances...")
                    else:
                        # No cache exists
                        status_placeholder.info(f"⌛ Downloading and analyzing {player_name}'s recent performances...")
                        time.sleep(0.5)
                        status_placeholder.info(f"⌛ Checking Cricsheet for historical data...")
                        time.sleep(0.5)
                        status_placeholder.info(f"⌛ Checking Cricbuzz for real-time updates...")
                else:
                    # Try to extract player name
                    words = user_input.split()
                    for word in words:
                        if len(word) > 3 and word.lower() not in ["show", "stats", "statistics", "about", "info", "player"]:
                            status_placeholder.info(f"⌛ Searching for player data: {word}...")
                            break

            # Check if query is about fantasy recommendations
            fantasy_keywords = ["differential", "captain", "vice-captain", "vc", "fantasy", "dream11", "fantasy xi",
                              "pick", "should i pick", "compare", "vs", "versus", "or", "better pick", "good pick",
                              "who's better", "who should i choose", "multiplier", "double points"]
            is_fantasy_query = any(keyword in user_input.lower() for keyword in fantasy_keywords)

            if is_fantasy_query:
                status_placeholder.info("⌛ Analyzing fantasy cricket recommendations...")

                # Add more detailed status after a short delay
                import time
                time.sleep(0.5)

                # Check if query is about differential picks
                if any(keyword in user_input.lower() for keyword in ["differential", "under the radar", "low ownership", "unique pick"]):
                    status_placeholder.info("⌛ Finding differential picks for today's matches...")
                    time.sleep(0.5)
                    status_placeholder.info("⌛ Analyzing player ownership and form...")

                # Check if query is about captain picks
                elif any(keyword in user_input.lower() for keyword in ["captain", "vice-captain", "vc", "multiplier", "double points"]):
                    status_placeholder.info("⌛ Identifying best captain and vice-captain options...")
                    time.sleep(0.5)
                    status_placeholder.info("⌛ Analyzing player form and matchups...")

                # Check if query is about player comparison
                elif any(keyword in user_input.lower() for keyword in ["compare", "versus", "vs", "or", "better pick", "should i pick"]):
                    status_placeholder.info("⌛ Comparing player statistics and matchups...")
                    time.sleep(0.5)

                    # Try to extract player names
                    from gemini_assistant import extract_player_comparison_names
                    player_names = extract_player_comparison_names(user_input)
                    if len(player_names) >= 2:
                        status_placeholder.info(f"⌛ Comparing {player_names[0]} and {player_names[1]}...")
                    else:
                        status_placeholder.info("⌛ Analyzing player comparison...")

                # Generic fantasy recommendation message
                else:
                    status_placeholder.info("⌛ Generating fantasy cricket advice...")

            # Check if query is about real-time data
            elif any(keyword in user_input.lower() for keyword in ["live", "current", "today", "now", "latest", "ongoing", "real-time", "real time", "update"]):
                status_placeholder.info("⌛ Fetching real-time cricket data from the web...")

                # Add more detailed status after a short delay
                import time
                time.sleep(0.5)

                # Check if query is about matches
                if any(keyword in user_input.lower() for keyword in ["match", "game", "score", "playing"]):
                    status_placeholder.info("⌛ Scraping live match scores from Cricbuzz...")
                    time.sleep(0.5)
                    status_placeholder.info("⌛ Processing match data...")

                # Check if query is about news
                elif any(keyword in user_input.lower() for keyword in ["news", "latest", "update", "headline"]):
                    status_placeholder.info("⌛ Fetching latest cricket news...")
                    time.sleep(0.5)
                    status_placeholder.info("⌛ Processing news articles...")

                # Check if query is about player stats
                elif any(keyword in user_input.lower() for keyword in ["stats", "statistics", "performance", "form"]):
                    # Try to extract player name
                    from gemini_assistant import extract_player_name
                    player_name = extract_player_name(user_input)
                    if player_name:
                        status_placeholder.info(f"⌛ Fetching real-time stats for {player_name} from Cricbuzz...")
                        time.sleep(0.5)
                        status_placeholder.info(f"⌛ Scraping {player_name}'s current performance data...")
                    else:
                        status_placeholder.info("⌛ Searching for player information...")

                # Generic real-time data message
                else:
                    status_placeholder.info("⌛ Fetching real-time cricket information...")

            # Check if query is about matches (but not real-time)
            elif any(keyword in user_input.lower() for keyword in ["match", "matches", "upcoming", "recent"]):
                if "upcoming" in user_input.lower():
                    status_placeholder.info("⌛ Fetching upcoming match schedule...")
                elif "recent" in user_input.lower():
                    status_placeholder.info("⌛ Fetching recent match results...")
                else:
                    status_placeholder.info("⌛ Searching for match information...")

            # Generic processing message
            else:
                status_placeholder.info("⌛ Processing your query...")

            # Process the query
            result = ai_manager.process_query(user_input)

            # Update status to show we're formatting the response
            status_placeholder.info("⌛ Formatting response...")

            # Check if result contains a response
            if result and "response" in result:
                output = result["response"]
                model_used = result.get("model_used", "unknown")
            else:
                # Fallback response if something went wrong
                output = "I'm sorry, I couldn't generate a response. Please try again."
                model_used = "fallback"

            # Log chat interaction
            log_chat(
                user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
                query=user_input,
                response=output[:100] + "..." if len(output) > 100 else output,
                model_used=model_used
            )

            # Clear the status message when done
            status_placeholder.empty()

        except Exception as e:
            output = f"I'm having trouble processing your request. Please try again. Error: {str(e)}"
            log_error(e, context={"user_input": user_input})

            # Show error in status
            status_placeholder.error("❌ Error processing your request")
            # Clear after 3 seconds
            import time
            time.sleep(3)
            status_placeholder.empty()

    # Save to database
    try:
        db = st.session_state['db_manager']
        user_id = st.session_state.get('db_user_id')

        # If user is authenticated, save to their history
        if user_id:
            db.save_chat(
                user_id=user_id,
                user_message=user_input,
                assistant_response=output,
                ai_model_used=model_used if 'model_used' in locals() else "unknown"
            )
    except Exception as e:
        log_error(e, context={"action": "save_chat"})

    # Add assistant response to chat history
    st.session_state.generated.append(output)

    # Check for visualization triggers in the response
    if any(keyword in user_input.lower() for keyword in ["chart", "graph", "visual", "compare", "stats", "statistics"]):
        # Try to extract player names or teams for visualization
        import re
        player_match = re.search(r'(stats|statistics|performance|form) (of|for) ([A-Za-z ]+)', user_input, re.IGNORECASE)
        compare_match = re.search(r'compare ([A-Za-z ]+) (and|vs|versus) ([A-Za-z ]+)', user_input, re.IGNORECASE)

        if player_match:
            player_name = player_match.group(3).strip()
            st.session_state['show_visualization'] = True
            st.session_state['visualization_type'] = 'player'
            st.session_state['visualization_params'] = {'player_name': player_name}
        elif compare_match:
            team1 = compare_match.group(1).strip()
            team2 = compare_match.group(3).strip()
            st.session_state['show_visualization'] = True
            st.session_state['visualization_type'] = 'compare'
            st.session_state['visualization_params'] = {'team1': team1, 'team2': team2}

    st.rerun()

# App header
st.title("🏏 Fantasy Cricket Assistant")
st.markdown("""
Welcome to your Fantasy Cricket Assistant! Ask me about:
- Player recommendations for your fantasy team
- Player statistics and current form
- Fantasy cricket rules and scoring
- Match conditions and pitch reports
""")

# Render authentication UI
render_login_ui()

# Navigation section
st.sidebar.markdown("## 🧭 Navigation")
st.sidebar.markdown("""
- [💬 Chat Assistant](/) - Ask questions and get recommendations
- [🏏 Matches](/1_%F0%9F%8F%8F_Matches) - View live and upcoming matches
- [👤 Players](/2_%F0%9F%91%A4_Players) - Player statistics and analysis
""")

# Live matches display with refresh button
st.sidebar.markdown("## 🔴 Live Cricket")

# Add refresh button for live data
refresh_col1, refresh_col2 = st.sidebar.columns([3, 1])
with refresh_col1:
    st.markdown("### Live Matches")
with refresh_col2:
    if st.button("🔄", key="refresh_matches", help="Refresh live match data"):
        st.session_state['refresh_timestamp'] = datetime.now().strftime("%H:%M:%S")
        st.rerun()

# Display last refresh time if available
if 'refresh_timestamp' in st.session_state:
    st.sidebar.caption(f"Last updated: {st.session_state['refresh_timestamp']}")

# Display live matches
try:
    with ErrorHandler(context="fetch_live_matches"):
        # Force refresh from API if refresh button was clicked
        force_refresh = 'refresh_timestamp' in st.session_state and st.session_state.get('refresh_timestamp') == datetime.now().strftime("%H:%M:%S")

        live_matches = get_live_cricket_matches()
        if live_matches:
            for match in live_matches:
                if isinstance(match, dict) and 'teams' in match:
                    # Create an expander for each match
                    with st.sidebar.expander(f"**{match.get('teams', 'Match')}**", expanded=True):
                        st.markdown(f"**Status:** *{match.get('status', '')}*")
                        st.markdown(f"**Venue:** {match.get('venue', 'Unknown')}")

                        # Add match type if available
                        if 'match_type' in match:
                            st.markdown(f"**Format:** {match.get('match_type', 'Unknown')}")

                        # Add pitch conditions if available
                        if 'pitch_conditions' in match:
                            conditions = match['pitch_conditions']
                            st.markdown("**Pitch Conditions:**")
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Batting", f"{conditions.get('batting_friendly', 5)}/10")
                            with cols[1]:
                                st.metric("Pace", f"{conditions.get('pace_friendly', 5)}/10")
                            with cols[2]:
                                st.metric("Spin", f"{conditions.get('spin_friendly', 5)}/10")
        else:
            st.sidebar.info("No live matches at the moment.")

            # Show upcoming matches instead
            upcoming = get_upcoming_matches()
            if upcoming and len(upcoming) > 0:
                st.sidebar.markdown("### Coming Up Next:")
                next_match = upcoming[0]
                st.sidebar.markdown(f"**{next_match.get('teams', 'Match')}**")
                st.sidebar.markdown(f"**Date:** {next_match.get('date', 'Unknown')}")
                st.sidebar.markdown(f"**Venue:** {next_match.get('venue', 'Unknown')}")
except Exception as e:
    st.sidebar.error("Unable to load live matches at the moment.")
    log_error(e, context="sidebar_live_matches")

# Model selector
st.sidebar.markdown("### 🤖 AI Model")
ai_manager = st.session_state['ai_manager']
available_models = ai_manager.get_available_models()

selected_model = st.sidebar.selectbox(
    "Select AI Model",
    available_models,
    index=available_models.index(ai_manager.default_model.value) if ai_manager.default_model.value in available_models else 0
)

# Update default model if changed
if selected_model != ai_manager.default_model.value:
    ai_manager.set_default_model(AIModel(selected_model))
    st.sidebar.success(f"AI model changed to {selected_model}")

# Chat history section in sidebar
if st.session_state.get('authenticated', False):
    st.sidebar.markdown("### 📝 Chat History")

    # Get user's chat history from database
    try:
        db = st.session_state['db_manager']
        user_id = st.session_state.get('db_user_id')
        recent_chats = db.get_user_chats(user_id, limit=5)

        if recent_chats:
            for i, chat in enumerate(recent_chats):
                st.sidebar.markdown(f"**You**: {chat.user_message[:30]}..." if len(chat.user_message) > 30 else f"**You**: {chat.user_message}")
                st.sidebar.markdown(f"**Bot**: {chat.assistant_response[:30]}..." if len(chat.assistant_response) > 30 else f"**Bot**: {chat.assistant_response}")
                if i < len(recent_chats) - 1:
                    st.sidebar.markdown("---")
        else:
            st.sidebar.markdown("No chat history yet.")
    except Exception as e:
        st.sidebar.markdown("Error loading chat history.")
        log_error(e, context="load_chat_history")

# Container for chat history - this needs to be ABOVE the input container in the UI
chat_container = st.container()

# Display chat history in strict chronological order
with chat_container:
    # Display messages in alternating user/assistant order
    # First message is always from the assistant (greeting)
    message(st.session_state.generated[0], key=f"bot_0", avatar_style="fun-emoji")

    # Then display the rest of the conversation in alternating order
    for i in range(len(st.session_state.past)):
        # User message
        message(st.session_state.past[i], is_user=True, key=f"user_{i}", avatar_style="thumbs")

        # Assistant response (if available)
        if i + 1 < len(st.session_state.generated):
            message(st.session_state.generated[i + 1], key=f"bot_{i + 1}", avatar_style="fun-emoji")

# Status container for loading indicator and status messages
status_container = st.container()

# Container for text box
input_container = st.container()

with input_container:
    # Create a form to handle 'Enter' key submission
    with st.form(key="message_form", clear_on_submit=True):
        user_input = get_text()
        submit_button = st.form_submit_button("Send")

    # Process when the form is submitted (either by button or Enter key)
    if submit_button:
        # Update session state with the current input
        st.session_state['user_input'] = st.session_state.input_text

        # Only process if there's actual input
        if st.session_state.user_input.strip():
            process_input()

# Display visualizations if triggered
if st.session_state.get('show_visualization', False):
    st.markdown("### 📊 Data Visualization")

    viz_type = st.session_state.get('visualization_type')
    params = st.session_state.get('visualization_params', {})

    try:
        if viz_type == 'player':
            player_name = params.get('player_name')
            if player_name:
                st.subheader(f"Performance Analysis: {player_name}")
                player_performance_chart(player_name)

        elif viz_type == 'compare':
            team1 = params.get('team1')
            team2 = params.get('team2')
            if team1 and team2:
                st.subheader(f"Team Comparison: {team1} vs {team2}")
                team_comparison_chart(team1, team2)

        # Add button to hide visualization
        if st.button("Hide Visualization"):
            st.session_state['show_visualization'] = False
            st.rerun()

    except Exception as e:
        st.error(f"Error displaying visualization: {str(e)}")
        log_error(e, context=f"visualization_{viz_type}")

# Quick action buttons
st.markdown("### Quick Actions")
col1, col2, col3, col4, col5 = st.columns(5)

# Helper function to process quick action button clicks
def handle_quick_action(query):
    """Process a quick action button click with proper message ordering"""
    # Import time module at the function level to avoid scoping issues
    import time

    # Add user message to chat history
    st.session_state.past.append(query)

    # Log access
    log_access(
        user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
        endpoint="quick_action",
        method="POST"
    )

    # Use the status container to show detailed status messages
    with status_container:
        # Create a placeholder for the status message
        status_placeholder = st.empty()

        # Show initial "thinking" message
        status_placeholder.info("⌛ The assistant is thinking...")

        try:
            # Process query with AI manager
            ai_manager = st.session_state['ai_manager']

            # Update status based on the quick action type
            if "batsmen" in query.lower():
                status_placeholder.info("⌛ Finding the best batsmen for today's matches...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Analyzing batsmen form and matchups...")
            elif "bowlers" in query.lower():
                status_placeholder.info("⌛ Analyzing top bowlers for fantasy cricket...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Evaluating bowling conditions and recent performances...")
            elif "differential" in query.lower():
                status_placeholder.info("⌛ Finding differential picks for today's matches...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Analyzing player ownership and form...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Identifying under-the-radar players...")
            elif "captain" in query.lower():
                status_placeholder.info("⌛ Identifying best captain and vice-captain options...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Analyzing player form and matchups...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Calculating multiplier value...")
            elif "fantasy" in query.lower() or "tips" in query.lower():
                status_placeholder.info("⌛ Generating fantasy cricket advice...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Compiling team selection strategies...")
            elif "stats" in query.lower():
                status_placeholder.info("⌛ Preparing player statistics options...")
            else:
                status_placeholder.info("⌛ Processing your request...")

            # Process the query
            result = ai_manager.process_query(query)

            # Update status to show we're formatting the response
            status_placeholder.info("⌛ Formatting response...")

            # Check if result contains a response
            if result and "response" in result:
                output = result["response"]
                model_used = result.get("model_used", "unknown")
            else:
                # Fallback response if something went wrong
                output = "I'm sorry, I couldn't generate a response. Please try again."
                model_used = "fallback"

            # Log chat interaction
            log_chat(
                user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
                query=query,
                response=output[:100] + "..." if len(output) > 100 else output,
                model_used=model_used
            )

            # Clear the status message when done
            status_placeholder.empty()

        except Exception as e:
            output = f"I'm having trouble processing your request. Please try again. Error: {str(e)}"
            log_error(e, context={"quick_action": query})

            # Show error in status
            status_placeholder.error("❌ Error processing your request")
            # Clear after 3 seconds
            time.sleep(3)
            status_placeholder.empty()

    # Save to database if user is authenticated
    try:
        if st.session_state.get('authenticated', False):
            db = st.session_state['db_manager']
            user_id = st.session_state.get('db_user_id')

            db.save_chat(
                user_id=user_id,
                user_message=query,
                assistant_response=output,
                ai_model_used=model_used if 'model_used' in locals() else "unknown"
            )
    except Exception as e:
        log_error(e, context={"action": "save_quick_action"})

    # Add assistant response to chat history
    st.session_state.generated.append(output)

    # Force a rerun to update the UI
    st.rerun()

# Import the necessary modules for fantasy recommendations
try:
    from fantasy_recommendations import get_differential_picks, compare_players, get_captain_picks
    from gemini_assistant import get_fantasy_recommendations, extract_player_comparison_names
    FANTASY_MODULES_AVAILABLE = True
except ImportError:
    FANTASY_MODULES_AVAILABLE = False
    logger.warning("Fantasy recommendation modules not available")

# Quick action buttons
with col1:
    if st.button("Best Batsmen", key="btn_batsmen"):
        handle_quick_action("Recommend batsmen for today's match")

with col2:
    if st.button("Top Bowlers", key="btn_bowlers"):
        handle_quick_action("Who are the best bowlers to pick for fantasy cricket?")

with col3:
    if st.button("Differential Picks", key="btn_differential"):
        handle_quick_action("Who are good differential picks for today's match?")

with col4:
    if st.button("Captain Picks", key="btn_captain"):
        handle_quick_action("Suggest captain and vice-captain for today's match")

with col5:
    if st.button("Fantasy Tips", key="btn_fantasy"):
        handle_quick_action("Give me fantasy cricket advice")

# Footer
st.markdown("---")
st.markdown("*This assistant provides recommendations based on cricket data and AI analysis. Always use your own judgment when making fantasy cricket decisions.*")
