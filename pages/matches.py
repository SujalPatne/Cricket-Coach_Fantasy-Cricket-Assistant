"""
Matches page - Shows upcoming and live cricket matches
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from parent directory
from cricket_data_adapter import get_live_cricket_matches, get_upcoming_matches
from logger import get_logger, ErrorHandler

# Set up logging
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Cricket Matches | Fantasy Cricket Assistant",
    page_icon="🏏",
    layout="wide"
)

# Page title
st.title("🏏 Cricket Matches")
st.markdown("View live and upcoming cricket matches to plan your fantasy team")

# Add refresh button
refresh_col1, refresh_col2 = st.columns([6, 1])
with refresh_col2:
    if st.button("🔄 Refresh", key="refresh_matches_page"):
        st.session_state['matches_refresh_timestamp'] = datetime.now().strftime("%H:%M:%S")
        st.rerun()

# Display last refresh time if available
if 'matches_refresh_timestamp' in st.session_state:
    st.caption(f"Last updated: {st.session_state['matches_refresh_timestamp']}")

# Create tabs for different match categories
tab1, tab2 = st.tabs(["📺 Live Matches", "🗓️ Upcoming Matches"])

with tab1:
    st.header("Live Matches")
    
    try:
        with ErrorHandler(context="fetch_live_matches_page"):
            live_matches = get_live_cricket_matches()
            
            if live_matches:
                # Create a card for each live match
                for i, match in enumerate(live_matches):
                    if isinstance(match, dict) and 'teams' in match:
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.subheader(match.get('teams', 'Match'))
                            st.markdown(f"**Status:** *{match.get('status', '')}*")
                            st.markdown(f"**Venue:** {match.get('venue', 'Unknown')}")
                            
                            # Add match type if available
                            if 'match_type' in match:
                                st.markdown(f"**Format:** {match.get('match_type', 'Unknown')}")
                        
                        with col2:
                            # Add pitch conditions if available
                            if 'pitch_conditions' in match:
                                conditions = match['pitch_conditions']
                                st.markdown("**Pitch Conditions:**")
                                st.metric("Batting", f"{conditions.get('batting_friendly', 5)}/10")
                                st.metric("Pace", f"{conditions.get('pace_friendly', 5)}/10")
                                st.metric("Spin", f"{conditions.get('spin_friendly', 5)}/10")
                        
                        # Add a divider between matches
                        if i < len(live_matches) - 1:
                            st.markdown("---")
            else:
                st.info("No live matches at the moment.")
    except Exception as e:
        st.error("Unable to load live matches at the moment.")
        logger.error(f"Error loading live matches: {str(e)}")

with tab2:
    st.header("Upcoming Matches")
    
    try:
        with ErrorHandler(context="fetch_upcoming_matches_page"):
            upcoming_matches = get_upcoming_matches()
            
            if upcoming_matches:
                # Group matches by date
                matches_by_date = {}
                for match in upcoming_matches:
                    date = match.get('date', 'Unknown')
                    if date not in matches_by_date:
                        matches_by_date[date] = []
                    matches_by_date[date].append(match)
                
                # Create a section for each date
                for date, matches in sorted(matches_by_date.items()):
                    st.subheader(f"📅 {date}")
                    
                    # Create a table of matches for this date
                    match_data = []
                    for match in matches:
                        match_data.append({
                            "Teams": match.get('teams', 'Unknown vs Unknown'),
                            "Format": match.get('match_type', 'Unknown'),
                            "Venue": match.get('venue', 'Unknown')
                        })
                    
                    if match_data:
                        st.table(pd.DataFrame(match_data))
                    
                    st.markdown("---")
            else:
                st.info("No upcoming matches found.")
    except Exception as e:
        st.error("Unable to load upcoming matches at the moment.")
        logger.error(f"Error loading upcoming matches: {str(e)}")

# Add a section for fantasy tips based on upcoming matches
st.header("Fantasy Tips for Upcoming Matches")
st.markdown("""
Here are some general tips for your fantasy cricket team:

1. **Check pitch conditions** - Different venues favor different types of players
2. **Monitor player form** - Recent performance is a good indicator of future success
3. **Consider head-to-head records** - Some players perform better against specific teams
4. **Balance your team** - Include a mix of batsmen, bowlers, all-rounders, and wicketkeepers
5. **Stay updated on team news** - Last-minute changes can affect your fantasy team

For personalized recommendations, return to the main chat and ask the Fantasy Cricket Assistant!
""")

# Footer
st.markdown("---")
st.markdown("*Data is refreshed automatically. Click the refresh button for the latest updates.*")
