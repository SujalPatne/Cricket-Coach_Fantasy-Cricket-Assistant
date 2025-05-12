"""
Players page for the Fantasy Cricket Assistant
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
    get_player_stats,
    get_player_form,
    get_recommended_players
)
from auth import initialize_session_state, render_login_ui
from logger import get_logger, log_access, log_error, ErrorHandler
from visualizations import player_performance_chart, fantasy_points_projection
from db_manager import DatabaseManager

# Set up logging
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Players - Fantasy Cricket Assistant",
    page_icon="👤",
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
    endpoint="players_page",
    method="GET"
)

# Page header
st.title("👤 Cricket Players")
st.markdown("""
Analyze player statistics, compare performances, and get recommendations for your fantasy cricket team.
""")

# Render authentication UI
render_login_ui()

# Create tabs for different player views
tab1, tab2, tab3 = st.tabs(["🔍 Player Search", "📊 Player Analysis", "🏆 Recommendations"])

# Player Search Tab
with tab1:
    st.header("Player Search")
    
    # Search box
    search_query = st.text_input("Search for a player", key="player_search")
    
    if search_query:
        # Search for player
        with ErrorHandler(context="player_search"):
            player = get_player_stats(search_query)
            
            if player:
                # Display player info
                st.markdown(f"## {player.get('name', 'Unknown Player')}")
                
                # Create columns for player details
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Display player basic info
                    st.markdown(f"**Team:** {player.get('team', 'Unknown')}")
                    st.markdown(f"**Role:** {player.get('role', 'Unknown')}")
                    
                    # Display fantasy info
                    st.markdown("### Fantasy Cricket Info")
                    st.markdown(f"**Price:** {player.get('price', 'Unknown')}")
                    st.markdown(f"**Ownership:** {player.get('ownership', 'Unknown')}%")
                    st.markdown(f"**Fantasy Points Avg:** {player.get('fantasy_points_avg', 'Unknown')}")
                    
                    # Get player form
                    form = get_player_form(player.get('name', ''))
                    st.markdown(f"**Current Form:** {form.capitalize() if form else 'Unknown'}")
                
                with col2:
                    # Display player performance chart
                    player_performance_chart(player.get('name', ''))
                
                # Display detailed stats based on role
                st.markdown("### Detailed Statistics")
                
                role = player.get('role', '').lower()
                
                if 'batsman' in role or 'all-rounder' in role or 'wicketkeeper' in role:
                    # Batting stats
                    st.markdown("#### Batting Statistics")
                    batting_stats = {
                        "Batting Average": player.get('batting_avg', 'Unknown'),
                        "Strike Rate": player.get('strike_rate', 'Unknown'),
                        "Recent Form": ", ".join(map(str, player.get('recent_form', []))) if player.get('recent_form') else 'Unknown'
                    }
                    
                    # Create a DataFrame for better display
                    batting_df = pd.DataFrame(list(batting_stats.items()), columns=["Metric", "Value"])
                    st.table(batting_df)
                
                if 'bowler' in role or 'all-rounder' in role:
                    # Bowling stats
                    st.markdown("#### Bowling Statistics")
                    bowling_stats = {
                        "Bowling Average": player.get('bowling_avg', 'Unknown'),
                        "Economy Rate": player.get('economy', 'Unknown'),
                        "Recent Wickets": ", ".join(map(str, player.get('recent_wickets', []))) if player.get('recent_wickets') else 'Unknown'
                    }
                    
                    # Create a DataFrame for better display
                    bowling_df = pd.DataFrame(list(bowling_stats.items()), columns=["Metric", "Value"])
                    st.table(bowling_df)
                
                # Add to favorites button (if user is authenticated)
                if st.session_state.get('authenticated', False):
                    if st.button("Add to Favorites", key="add_favorite"):
                        try:
                            db = DatabaseManager()
                            user = db.get_user_by_id(st.session_state['db_user_id'])
                            
                            if user:
                                # Check if player exists in database
                                db_player = db.get_player_by_name(player.get('name', ''))
                                
                                if not db_player:
                                    # Save player to database
                                    db_player = db.save_player(player)
                                
                                # Add to user's favorites
                                if db_player:
                                    # This would require additional methods in DatabaseManager
                                    # For now, just show a success message
                                    st.success(f"Added {player.get('name', 'Player')} to your favorites!")
                                else:
                                    st.error("Unable to add player to favorites.")
                        except Exception as e:
                            log_error(e, context="add_player_favorite")
                            st.error(f"Error adding player to favorites: {str(e)}")
            else:
                st.warning(f"No player found matching '{search_query}'. Try a different name or check spelling.")

# Player Analysis Tab
with tab2:
    st.header("Player Analysis")
    
    # Player selection for analysis
    st.markdown("### Select Players to Analyze")
    
    # Get a list of common players
    common_players = [
        "Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "MS Dhoni", 
        "Kane Williamson", "Babar Azam", "Ben Stokes", "Steve Smith",
        "Jos Buttler", "Rashid Khan", "Kagiso Rabada", "Shakib Al Hasan"
    ]
    
    # Multi-select for players
    selected_players = st.multiselect(
        "Select players to analyze",
        options=common_players,
        default=common_players[:2]
    )
    
    if selected_players:
        # Show fantasy points projection
        st.markdown("### Fantasy Points Projection")
        fantasy_points_projection(selected_players)
        
        # Individual player analysis
        st.markdown("### Individual Player Analysis")
        
        for player_name in selected_players:
            with st.expander(f"**{player_name}**", expanded=len(selected_players) <= 2):
                player_performance_chart(player_name)

# Recommendations Tab
with tab3:
    st.header("Player Recommendations")
    
    # Filters for recommendations
    st.markdown("### Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        role_filter = st.selectbox(
            "Player Role",
            options=["All", "Batsman", "Bowler", "All-rounder", "Wicketkeeper"]
        )
    
    with col2:
        team_filter = st.selectbox(
            "Team",
            options=["All", "India", "Australia", "England", "New Zealand", "South Africa", "Pakistan", "West Indies", "Bangladesh", "Sri Lanka", "Afghanistan"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort By",
            options=["Fantasy Points", "Form", "Price", "Value"]
        )
    
    # Get recommendations
    if st.button("Get Recommendations", key="get_recommendations"):
        with ErrorHandler(context="get_player_recommendations"):
            # Convert "All" to None for the API
            role = None if role_filter == "All" else role_filter
            team = None if team_filter == "All" else team_filter
            
            # Get recommended players
            recommended_players = get_recommended_players(role=role, team=team)
            
            if recommended_players:
                # Sort players based on selected criteria
                if sort_by == "Fantasy Points":
                    recommended_players.sort(key=lambda p: p.get('fantasy_points_avg', 0), reverse=True)
                elif sort_by == "Form":
                    # This would require a numerical form rating
                    # For now, just use fantasy points as a proxy
                    recommended_players.sort(key=lambda p: p.get('fantasy_points_avg', 0), reverse=True)
                elif sort_by == "Price":
                    recommended_players.sort(key=lambda p: p.get('price', 0))
                elif sort_by == "Value":
                    # Calculate value as fantasy points / price
                    for player in recommended_players:
                        if player.get('price', 0) > 0:
                            player['value'] = player.get('fantasy_points_avg', 0) / player.get('price', 1)
                        else:
                            player['value'] = 0
                    recommended_players.sort(key=lambda p: p.get('value', 0), reverse=True)
                
                # Create a dataframe for better display
                player_data = []
                for player in recommended_players:
                    form = get_player_form(player.get('name', ''))
                    
                    # Calculate value
                    value = player.get('fantasy_points_avg', 0) / player.get('price', 1) if player.get('price', 0) > 0 else 0
                    
                    player_data.append({
                        "Name": player.get('name', 'Unknown'),
                        "Team": player.get('team', 'Unknown'),
                        "Role": player.get('role', 'Unknown'),
                        "Form": form.capitalize() if form else 'Unknown',
                        "Fantasy Pts": f"{player.get('fantasy_points_avg', 0):.1f}",
                        "Price": f"{player.get('price', 0):.1f}",
                        "Value": f"{value:.2f}"
                    })
                
                df = pd.DataFrame(player_data)
                st.dataframe(df, use_container_width=True)
                
                # Create detailed cards for top players
                st.markdown("### Top Recommended Players")
                
                for i, player in enumerate(recommended_players[:5]):
                    with st.expander(f"**{player.get('name', 'Player')}**", expanded=i==0):
                        # Create columns for player details
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            # Display player basic info
                            st.markdown(f"**Team:** {player.get('team', 'Unknown')}")
                            st.markdown(f"**Role:** {player.get('role', 'Unknown')}")
                            
                            # Display fantasy info
                            st.markdown("### Fantasy Cricket Info")
                            st.markdown(f"**Price:** {player.get('price', 'Unknown')}")
                            st.markdown(f"**Ownership:** {player.get('ownership', 'Unknown')}%")
                            st.markdown(f"**Fantasy Points Avg:** {player.get('fantasy_points_avg', 'Unknown')}")
                            
                            # Get player form
                            form = get_player_form(player.get('name', ''))
                            st.markdown(f"**Current Form:** {form.capitalize() if form else 'Unknown'}")
                        
                        with col2:
                            # Display player performance chart
                            player_performance_chart(player.get('name', ''))
            else:
                st.warning("No players found matching your criteria. Try different filters.")

# Footer
st.markdown("---")
st.markdown("*This page provides player statistics and recommendations to help with your fantasy cricket decisions. Data is sourced from various cricket APIs and may not be real-time.*")
