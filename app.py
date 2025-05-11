import streamlit as st
from streamlit_chat import message
import pandas as pd
import random
import time
import os

# Import modules for cricket data and assistant functionality
from cricket_data import get_player_stats, get_recommended_players, get_player_form
from cricket_scraper import get_live_cricket_matches, get_upcoming_matches, get_pitch_conditions
from assistant import generate_response, GREETING_MESSAGE
from fantasy_rules import get_fantasy_rule_explanation
from gemini_assistant import process_cricket_query

# Page configuration
st.set_page_config(
    page_title="Fantasy Cricket Assistant",
    page_icon="🏏",
    layout="wide"
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
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = [GREETING_MESSAGE]
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

# Flag to determine if we should use Gemini or the rule-based assistant
if 'use_gemini' not in st.session_state:
    st.session_state['use_gemini'] = True
    
# Initialize user ID for tracking chat history
if 'user_id' not in st.session_state:
    import uuid
    st.session_state['user_id'] = str(uuid.uuid4())
    
# Import data storage functions
from data_storage import get_chat_history, export_chat_history_to_csv

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
    user_input = st.session_state.user_input
    if not user_input:
        return
        
    # Reset user_input but NOT input_text as that would cause an error
    # since we can't modify widget values after creation
    st.session_state.user_input = ""
    
    # Add user message to chat history
    st.session_state.past.append(user_input)
    
    # Show "typing" indicator
    with st.spinner("⌛ The assistant is thinking..."):
        try:
            if st.session_state['use_gemini'] and os.environ.get("GEMINI_API_KEY"):
                # Use Gemini for AI-powered responses
                output = process_cricket_query(user_input)
            else:
                # Fallback to rule-based responses
                output = generate_response(user_input)
        except Exception as e:
            output = f"I'm having trouble processing your request. Please try again. Error: {str(e)}"
    
    # Save to chat history in JSON file
    from data_storage import save_chat_history
    # Use session ID as user ID
    user_id = st.session_state.get('user_id', 'anonymous')
    save_chat_history(user_id, user_input, output)
    
    # Add assistant response to chat history
    st.session_state.generated.append(output)
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

# Live matches display
try:
    live_matches = get_live_cricket_matches()
    if live_matches:
        st.sidebar.markdown("## 🔴 Live Matches")
        for match in live_matches:
            if isinstance(match, dict) and 'teams' in match:
                st.sidebar.markdown(f"**{match.get('teams', 'Match')}**")
                st.sidebar.markdown(f"*{match.get('status', '')}*")
                st.sidebar.markdown(f"Venue: {match.get('venue', 'Unknown')}")
                st.sidebar.markdown("---")
except Exception as e:
    st.sidebar.markdown("## Live Matches")
    st.sidebar.markdown("Unable to load live matches at the moment.")

# Model selector
model_col1, model_col2 = st.sidebar.columns(2)
with model_col1:
    st.sidebar.markdown("### AI Model")
with model_col2:
    gemini_toggle = st.sidebar.checkbox("Use Gemini AI", value=st.session_state['use_gemini'])
    if gemini_toggle != st.session_state['use_gemini']:
        st.session_state['use_gemini'] = gemini_toggle
        st.rerun()

# Chat history section in sidebar
st.sidebar.markdown("### 📝 Chat History")
if st.sidebar.button("Export Chat History"):
    if export_chat_history_to_csv():
        st.sidebar.success("Chat history exported to chat_history_export.csv")
    else:
        st.sidebar.error("Failed to export chat history")

# Show recent conversations
st.sidebar.markdown("#### Recent Conversations")
recent_chats = get_chat_history(limit=5)
if recent_chats:
    for i, chat in enumerate(reversed(recent_chats)):
        st.sidebar.markdown(f"**User**: {chat['user_message'][:30]}..." if len(chat['user_message']) > 30 else f"**User**: {chat['user_message']}")
        st.sidebar.markdown(f"**Bot**: {chat['assistant_response'][:30]}..." if len(chat['assistant_response']) > 30 else f"**Bot**: {chat['assistant_response']}")
        if i < len(recent_chats) - 1:
            st.sidebar.markdown("---")

# Container for chat history - this needs to be ABOVE the input container in the UI
chat_container = st.container()

# Display chat history in pairs (user message followed by assistant response)
with chat_container:
    if st.session_state['generated']:
        # Creating a container for each message pair to ensure they stay together
        message_pairs = []
        
        # Create pairs of messages (user message + assistant response)
        for i in range(len(st.session_state['generated'])):
            if i == 0 and len(st.session_state['past']) == 0:
                # Handle greeting message case
                message_pairs.append((None, st.session_state['generated'][i]))
            elif i < len(st.session_state['past']):
                message_pairs.append((st.session_state['past'][i], st.session_state['generated'][i]))
        
        # Display each message pair
        for i, (user_msg, assistant_msg) in enumerate(message_pairs):
            if user_msg is not None:
                message(user_msg, is_user=True, key=f"user_{i}", avatar_style="thumbs")
            message(assistant_msg, key=f"bot_{i}", avatar_style="fun-emoji")

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

# Quick action buttons
st.markdown("### Quick Actions")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Best Batsmen Today", key="btn_batsmen"):
        st.session_state.input_text = "Recommend batsmen for today's match"
        st.session_state.user_input = st.session_state.input_text
        process_input()
with col2:
    if st.button("Top Bowlers", key="btn_bowlers"):
        st.session_state.input_text = "Who are the best bowlers to pick for fantasy cricket?"
        st.session_state.user_input = st.session_state.input_text
        process_input()
with col3:
    if st.button("Fantasy Rules", key="btn_rules"):
        st.session_state.input_text = "Explain fantasy cricket rules"
        st.session_state.user_input = st.session_state.input_text
        process_input()
with col4:
    if st.button("Captain Picks", key="btn_captain"):
        st.session_state.input_text = "Suggest captain and vice-captain"
        st.session_state.user_input = st.session_state.input_text
        process_input()

# Footer
st.markdown("---")
st.markdown("*This assistant provides recommendations based on cricket data and AI analysis. Always use your own judgment when making fantasy cricket decisions.*")
