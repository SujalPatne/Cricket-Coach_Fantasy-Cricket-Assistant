import streamlit as st
from streamlit_chat import message
import pandas as pd
import random
import time

from cricket_data import get_player_stats, get_recommended_players, get_player_form
from assistant import generate_response, GREETING_MESSAGE
from fantasy_rules import get_fantasy_rule_explanation

# Page configuration
st.set_page_config(
    page_title="Fantasy Cricket Assistant",
    page_icon="🏏",
    layout="wide"
)

# Initialize session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = [GREETING_MESSAGE]
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

def get_text():
    """Get the user input text"""
    input_text = st.text_input("You: ", key="input", value=st.session_state['user_input'])
    return input_text

def process_input():
    """Process the input and return a response"""
    user_input = st.session_state.user_input
    st.session_state.user_input = ""
    
    st.session_state.past.append(user_input)
    
    # Show "typing" indicator
    with st.spinner("⌛ The assistant is typing..."):
        time.sleep(0.5)  # Simulating processing time
        output = generate_response(user_input)
    
    st.session_state.generated.append(output)
    st.rerun()

st.title("🏏 Fantasy Cricket Assistant")
st.markdown("""
Welcome to your Fantasy Cricket Assistant! Ask me about:
- Player recommendations for your fantasy team
- Player statistics and current form
- Fantasy cricket rules and scoring
- Match conditions and pitch reports
""")

# Container for chat history
chat_container = st.container()

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
        st.session_state.user_input = "Who are the best bowlers to pick?"
        process_input()
with col3:
    if st.button("Fantasy Rules"):
        st.session_state.user_input = "Explain fantasy cricket rules"
        process_input()
with col4:
    if st.button("Captain Picks"):
        st.session_state.user_input = "Suggest captain and vice-captain"
        process_input()

# Display chat history
with chat_container:
    if st.session_state['generated']:
        for i in range(len(st.session_state['generated'])):
            if i < len(st.session_state['past']):
                message(st.session_state['past'][i], is_user=True, key=f"user_{i}")
            message(st.session_state['generated'][i], key=f"bot_{i}")

# Footer
st.markdown("---")
st.markdown("*This assistant provides recommendations based on historical data and current form. Always use your own judgment when making fantasy cricket decisions.*")
