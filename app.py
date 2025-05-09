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

def get_text():
    """Get the user input text"""
    input_text = st.text_input("You: ", key="input", value=st.session_state['user_input'])
    return input_text

def process_input():
    """Process the input and return a response"""
    user_input = st.session_state.user_input
    if not user_input:
        return
        
    st.session_state.user_input = ""
    
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

# Container for chat history - this needs to be ABOVE the input container in the UI
chat_container = st.container()

# Display chat history
with chat_container:
    if st.session_state['generated']:
        for i in range(len(st.session_state['generated'])):
            if i < len(st.session_state['past']):
                message(st.session_state['past'][i], is_user=True, key=f"user_{i}", avatar_style="thumbs")
            message(st.session_state['generated'][i], key=f"bot_{i}", avatar_style="fun-emoji")

# Container for text box
input_container = st.container()

with input_container:
    user_input = get_text()
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        submit_button = st.button("Send", on_click=process_input)

# Quick action buttons
st.markdown("### Quick Actions")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Best Batsmen Today"):
        st.session_state.user_input = "Recommend batsmen for today's match"
        process_input()
with col2:
    if st.button("Top Bowlers"):
        st.session_state.user_input = "Who are the best bowlers to pick for fantasy cricket?"
        process_input()
with col3:
    if st.button("Fantasy Rules"):
        st.session_state.user_input = "Explain fantasy cricket rules"
        process_input()
with col4:
    if st.button("Captain Picks"):
        st.session_state.user_input = "Suggest captain and vice-captain"
        process_input()

# Footer
st.markdown("---")
st.markdown("*This assistant provides recommendations based on cricket data and AI analysis. Always use your own judgment when making fantasy cricket decisions.*")
