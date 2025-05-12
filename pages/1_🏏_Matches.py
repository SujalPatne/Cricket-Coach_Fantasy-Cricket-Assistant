"""
Matches page for the Fantasy Cricket Assistant
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom modules
from cricket_data_adapter import (
    get_live_cricket_matches,
    get_upcoming_matches,
    get_recent_matches,
    get_match_details,
    get_pitch_conditions
)
from auth import initialize_session_state, render_login_ui
from logger import get_logger, log_access, log_error, ErrorHandler
from visualizations import player_performance_chart, team_comparison_chart

# Set up logging
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Matches - Fantasy Cricket Assistant",
    page_icon="🏏",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/yourusername/fantasy-cricket-assistant',
        'Report a bug': 'https://github.com/yourusername/fantasy-cricket-assistant/issues',
        'About': 'Fantasy Cricket Assistant - Your AI-powered cricket fantasy league advisor'
    }
)

# Initialize session state
initialize_session_state()

# Log page access
log_access(
    user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
    endpoint="matches_page",
    method="GET"
)

# Page header
st.title("🏏 Cricket Matches")
st.markdown("""
View live, upcoming, and recent cricket matches. Get detailed match information and pitch conditions to help with your fantasy cricket decisions.
""")

# Render authentication UI
render_login_ui()

# Create tabs for different match types
tab1, tab2, tab3 = st.tabs(["📊 Live Matches", "🗓️ Upcoming Matches", "📜 Recent Matches"])

# Live Matches Tab
with tab1:
    st.header("Live Matches")
    
    # Add refresh button
    if st.button("🔄 Refresh Data", key="refresh_live"):
        st.session_state['refresh_timestamp'] = datetime.now().strftime("%H:%M:%S")
        st.rerun()
    
    # Display last refresh time if available
    if 'refresh_timestamp' in st.session_state:
        st.caption(f"Last updated: {st.session_state['refresh_timestamp']}")
    
    # Get live matches
    with ErrorHandler(context="fetch_live_matches_page"):
        live_matches = get_live_cricket_matches()
        
        if live_matches:
            # Create a card for each live match
            for i, match in enumerate(live_matches):
                with st.expander(f"**{match.get('teams', 'Match')}**", expanded=True):
                    # Create columns for match details
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Status:** *{match.get('status', 'Unknown')}*")
                        st.markdown(f"**Venue:** {match.get('venue', 'Unknown')}")
                        
                        # Add match type if available
                        if 'match_type' in match:
                            st.markdown(f"**Format:** {match.get('match_type', 'Unknown')}")
                        
                        # Add match ID if available
                        if 'match_id' in match:
                            st.markdown(f"**Match ID:** {match.get('match_id', 'Unknown')}")
                        
                        # Add data source if available
                        if 'source' in match:
                            st.markdown(f"**Data Source:** {match.get('source', 'Unknown')}")
                    
                    with col2:
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
                    
                    # Add button to view detailed match info
                    if 'match_id' in match:
                        if st.button("View Detailed Scorecard", key=f"view_match_{i}"):
                            match_details = get_match_details(match['match_id'])
                            
                            if match_details:
                                st.markdown(f"### Scorecard: {match_details.get('teams', 'Match')}")
                                
                                # Display scores
                                scores = match_details.get('scores', [])
                                if scores:
                                    for score in scores:
                                        st.markdown(f"**{score.get('score_str', 'Unknown')}**")
                                
                                # Display additional match details
                                st.markdown(f"**Match Date:** {match_details.get('date', 'Unknown')}")
                                st.markdown(f"**Match Type:** {match_details.get('match_type', 'Unknown')}")
                                st.markdown(f"**Status:** {match_details.get('status', 'Unknown')}")
                                st.markdown(f"**Data Source:** {match_details.get('source', 'Unknown')}")
                            else:
                                st.error("Unable to fetch detailed match information.")
        else:
            st.info("No live matches at the moment.")

# Upcoming Matches Tab
with tab2:
    st.header("Upcoming Matches")
    
    # Add refresh button
    if st.button("🔄 Refresh Data", key="refresh_upcoming"):
        st.rerun()
    
    # Get upcoming matches
    with ErrorHandler(context="fetch_upcoming_matches_page"):
        upcoming_matches = get_upcoming_matches()
        
        if upcoming_matches:
            # Create a dataframe for better display
            match_data = []
            for match in upcoming_matches:
                match_data.append({
                    "Teams": match.get('teams', 'Unknown vs Unknown'),
                    "Date": match.get('date', 'Unknown'),
                    "Venue": match.get('venue', 'Unknown'),
                    "Format": match.get('match_type', 'Unknown'),
                    "Source": match.get('source', 'Unknown')
                })
            
            df = pd.DataFrame(match_data)
            st.dataframe(df, use_container_width=True)
            
            # Create detailed cards for upcoming matches
            st.markdown("### Match Details")
            for i, match in enumerate(upcoming_matches):
                with st.expander(f"**{match.get('teams', 'Match')}**", expanded=i==0):
                    # Create columns for match details
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Date:** {match.get('date', 'Unknown')}")
                        st.markdown(f"**Venue:** {match.get('venue', 'Unknown')}")
                        
                        # Add match type if available
                        if 'match_type' in match:
                            st.markdown(f"**Format:** {match.get('match_type', 'Unknown')}")
                        
                        # Add data source if available
                        if 'source' in match:
                            st.markdown(f"**Data Source:** {match.get('source', 'Unknown')}")
                    
                    with col2:
                        # Add pitch conditions if available
                        if 'pitch_conditions' in match:
                            conditions = match['pitch_conditions']
                            st.markdown("**Expected Pitch Conditions:**")
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Batting", f"{conditions.get('batting_friendly', 5)}/10")
                            with cols[1]:
                                st.metric("Pace", f"{conditions.get('pace_friendly', 5)}/10")
                            with cols[2]:
                                st.metric("Spin", f"{conditions.get('spin_friendly', 5)}/10")
                        
                        # If no pitch conditions in match data, try to get from venue
                        elif 'venue' in match:
                            venue = match.get('venue', '')
                            conditions = get_pitch_conditions(venue)
                            
                            if conditions:
                                st.markdown("**Expected Pitch Conditions:**")
                                cols = st.columns(3)
                                with cols[0]:
                                    st.metric("Batting", f"{conditions.get('batting_friendly', 5)}/10")
                                with cols[1]:
                                    st.metric("Pace", f"{conditions.get('pace_friendly', 5)}/10")
                                with cols[2]:
                                    st.metric("Spin", f"{conditions.get('spin_friendly', 5)}/10")
        else:
            st.info("No upcoming matches found.")

# Recent Matches Tab
with tab3:
    st.header("Recent Matches")
    
    # Add refresh button
    if st.button("🔄 Refresh Data", key="refresh_recent"):
        st.rerun()
    
    # Get recent matches
    with ErrorHandler(context="fetch_recent_matches_page"):
        recent_matches = get_recent_matches()
        
        if recent_matches:
            # Create a dataframe for better display
            match_data = []
            for match in recent_matches:
                match_data.append({
                    "Teams": match.get('teams', 'Unknown vs Unknown'),
                    "Result": match.get('status', 'Unknown'),
                    "Date": match.get('date', 'Unknown'),
                    "Venue": match.get('venue', 'Unknown'),
                    "Format": match.get('match_type', 'Unknown'),
                    "Source": match.get('source', 'Unknown')
                })
            
            df = pd.DataFrame(match_data)
            st.dataframe(df, use_container_width=True)
            
            # Create detailed cards for recent matches
            st.markdown("### Match Details")
            for i, match in enumerate(recent_matches):
                with st.expander(f"**{match.get('teams', 'Match')}**", expanded=i==0):
                    # Create columns for match details
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Result:** {match.get('status', 'Unknown')}")
                        st.markdown(f"**Date:** {match.get('date', 'Unknown')}")
                        st.markdown(f"**Venue:** {match.get('venue', 'Unknown')}")
                        
                        # Add match type if available
                        if 'match_type' in match:
                            st.markdown(f"**Format:** {match.get('match_type', 'Unknown')}")
                        
                        # Add match ID if available
                        if 'match_id' in match:
                            st.markdown(f"**Match ID:** {match.get('match_id', 'Unknown')}")
                        
                        # Add data source if available
                        if 'source' in match:
                            st.markdown(f"**Data Source:** {match.get('source', 'Unknown')}")
                    
                    with col2:
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
                    
                    # Add button to view detailed match info
                    if 'match_id' in match:
                        if st.button("View Detailed Scorecard", key=f"view_recent_match_{i}"):
                            match_details = get_match_details(match['match_id'])
                            
                            if match_details:
                                st.markdown(f"### Scorecard: {match_details.get('teams', 'Match')}")
                                
                                # Display scores
                                scores = match_details.get('scores', [])
                                if scores:
                                    for score in scores:
                                        st.markdown(f"**{score.get('score_str', 'Unknown')}**")
                                
                                # Display additional match details
                                st.markdown(f"**Match Date:** {match_details.get('date', 'Unknown')}")
                                st.markdown(f"**Match Type:** {match_details.get('match_type', 'Unknown')}")
                                st.markdown(f"**Status:** {match_details.get('status', 'Unknown')}")
                                st.markdown(f"**Data Source:** {match_details.get('source', 'Unknown')}")
                            else:
                                st.error("Unable to fetch detailed match information.")
        else:
            st.info("No recent matches found.")

# Footer
st.markdown("---")
st.markdown("*This page provides match information to help with your fantasy cricket decisions. Data is sourced from various cricket APIs and may not be real-time.*")
