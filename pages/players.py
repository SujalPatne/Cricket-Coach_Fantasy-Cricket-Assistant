"""
Players page - Shows player statistics and analysis
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from parent directory
from cricket_data_adapter import get_player_stats, get_player_form, get_recommended_players
from visualizations import player_performance_chart
from logger import get_logger, ErrorHandler

# Set up logging
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Player Stats | Fantasy Cricket Assistant",
    page_icon="🏏",
    layout="wide"
)

# Page title
st.title("🏏 Player Statistics")
st.markdown("Analyze player performance and get fantasy cricket insights")

# Create tabs for different player analysis options
tab1, tab2, tab3 = st.tabs(["🔍 Player Search", "📊 Performance Analysis", "🌟 Top Performers"])

with tab1:
    st.header("Player Search")
    
    # Player search form
    with st.form("player_search_form"):
        player_name = st.text_input("Enter player name", placeholder="e.g., Virat Kohli")
        submit_button = st.form_submit_button("Search")
    
    # Process player search
    if submit_button and player_name:
        try:
            with ErrorHandler(context="player_search"):
                with st.spinner(f"Searching for {player_name}..."):
                    player_data = get_player_stats(player_name)
                
                if player_data and player_data.get('name') != 'Unknown':
                    st.success(f"Found player: {player_data.get('name')}")
                    
                    # Display player info in columns
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("Player Information")
                        
                        # Create a table with player details
                        info_data = {
                            "Attribute": ["Team", "Role", "Matches Played", "Current Form"],
                            "Value": [
                                player_data.get('team', 'Unknown'),
                                player_data.get('role', 'Unknown'),
                                player_data.get('matches_played', 'Unknown'),
                                get_player_form(player_name).capitalize()
                            ]
                        }
                        st.table(pd.DataFrame(info_data))
                        
                        # Display batting stats if available
                        if player_data.get('batting_avg') or player_data.get('strike_rate'):
                            st.subheader("Batting Statistics")
                            batting_data = {
                                "Statistic": ["Batting Average", "Strike Rate"],
                                "Value": [
                                    f"{player_data.get('batting_avg', 0):.2f}" if player_data.get('batting_avg') else "N/A",
                                    f"{player_data.get('strike_rate', 0):.2f}" if player_data.get('strike_rate') else "N/A"
                                ]
                            }
                            st.table(pd.DataFrame(batting_data))
                        
                        # Display bowling stats if available
                        if player_data.get('bowling_avg') or player_data.get('economy'):
                            st.subheader("Bowling Statistics")
                            bowling_data = {
                                "Statistic": ["Bowling Average", "Economy Rate"],
                                "Value": [
                                    f"{player_data.get('bowling_avg', 0):.2f}" if player_data.get('bowling_avg') else "N/A",
                                    f"{player_data.get('economy', 0):.2f}" if player_data.get('economy') else "N/A"
                                ]
                            }
                            st.table(pd.DataFrame(bowling_data))
                    
                    with col2:
                        st.subheader("Fantasy Value")
                        
                        # Display fantasy stats
                        st.metric("Fantasy Points Avg", f"{player_data.get('fantasy_points_avg', 0):.1f}")
                        st.metric("Ownership", f"{player_data.get('ownership', 0):.1f}%")
                        st.metric("Price", f"{player_data.get('price', 0):.1f}")
                        
                        # Calculate value (points per unit price)
                        if player_data.get('fantasy_points_avg') and player_data.get('price'):
                            value = player_data.get('fantasy_points_avg') / player_data.get('price')
                            st.metric("Value Rating", f"{value:.2f}")
                    
                    # Show performance chart
                    st.subheader("Recent Performance")
                    player_performance_chart(player_name)
                    
                else:
                    st.error(f"Could not find detailed stats for player: {player_name}")
        
        except Exception as e:
            st.error(f"Error searching for player: {str(e)}")
            logger.error(f"Error in player search: {str(e)}")

with tab2:
    st.header("Performance Analysis")
    
    # Player selection for analysis
    player_name_analysis = st.text_input("Enter player name for analysis", placeholder="e.g., Rohit Sharma", key="analysis_player")
    
    if player_name_analysis:
        try:
            with ErrorHandler(context="player_analysis"):
                with st.spinner(f"Analyzing {player_name_analysis}..."):
                    player_data = get_player_stats(player_name_analysis)
                
                if player_data and player_data.get('name') != 'Unknown':
                    st.success(f"Analyzing: {player_data.get('name')}")
                    
                    # Show performance chart
                    player_performance_chart(player_name_analysis)
                    
                    # Add more detailed analysis
                    st.subheader("Performance Insights")
                    
                    # Get player form
                    form = get_player_form(player_name_analysis)
                    
                    # Generate insights based on player data
                    insights = []
                    
                    if form == "excellent":
                        insights.append("🔥 Player is in excellent form - strongly consider for your fantasy team")
                    elif form == "good":
                        insights.append("👍 Player is in good form - a solid pick for your fantasy team")
                    elif form == "average":
                        insights.append("⚠️ Player is in average form - consider other options if available")
                    elif form == "poor":
                        insights.append("⛔ Player is in poor form - avoid unless you expect a turnaround")
                    
                    # Role-specific insights
                    role = player_data.get('role', 'Unknown')
                    if role == "Batsman":
                        if player_data.get('strike_rate', 0) > 140:
                            insights.append("⚡ High strike rate makes this player excellent for T20 formats")
                        if player_data.get('batting_avg', 0) > 45:
                            insights.append("📊 High batting average indicates consistency")
                    elif role == "Bowler":
                        if player_data.get('economy', 0) < 7:
                            insights.append("🎯 Good economy rate makes this bowler valuable in all formats")
                        if player_data.get('bowling_avg', 0) < 25:
                            insights.append("🔝 Excellent bowling average indicates wicket-taking ability")
                    elif role == "All-rounder":
                        insights.append("🌟 All-rounders often provide excellent value in fantasy cricket")
                    elif role == "Wicketkeeper":
                        insights.append("🧤 Wicketkeepers who bat well are premium fantasy assets")
                    
                    # Value assessment
                    if player_data.get('fantasy_points_avg') and player_data.get('price'):
                        value = player_data.get('fantasy_points_avg') / player_data.get('price')
                        if value > 10:
                            insights.append("💰 Excellent value for price - strongly recommended")
                        elif value > 8:
                            insights.append("💸 Good value for price - recommended pick")
                        elif value < 6:
                            insights.append("💱 Poor value for price - consider alternatives")
                    
                    # Display insights
                    for insight in insights:
                        st.markdown(f"- {insight}")
                    
                else:
                    st.error(f"Could not find detailed stats for player: {player_name_analysis}")
        
        except Exception as e:
            st.error(f"Error analyzing player: {str(e)}")
            logger.error(f"Error in player analysis: {str(e)}")

with tab3:
    st.header("Top Performers")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        role_filter = st.selectbox(
            "Filter by role",
            ["All Roles", "Batsman", "Bowler", "All-rounder", "Wicketkeeper"]
        )
    
    with col2:
        team_filter = st.text_input("Filter by team (optional)", placeholder="e.g., India")
    
    # Convert role filter to API parameter
    role_param = None if role_filter == "All Roles" else role_filter
    team_param = None if not team_filter else team_filter
    
    try:
        with ErrorHandler(context="top_performers"):
            with st.spinner("Loading top performers..."):
                # Get recommended players based on filters
                players = get_recommended_players(role=role_param, team=team_param)
                
                if players:
                    # Create a dataframe for display
                    player_data = []
                    for player in players[:10]:  # Show top 10
                        player_data.append({
                            "Name": player.get('name', 'Unknown'),
                            "Team": player.get('team', 'Unknown'),
                            "Role": player.get('role', 'Unknown'),
                            "Fantasy Pts": f"{player.get('fantasy_points_avg', 0):.1f}",
                            "Form": get_player_form(player.get('name', '')).capitalize(),
                            "Price": f"{player.get('price', 0):.1f}"
                        })
                    
                    # Display as a table
                    if player_data:
                        st.dataframe(pd.DataFrame(player_data), use_container_width=True)
                    else:
                        st.info("No players found matching your criteria.")
                else:
                    st.info("No players found matching your criteria.")
    
    except Exception as e:
        st.error(f"Error loading top performers: {str(e)}")
        logger.error(f"Error in top performers: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*For personalized recommendations, return to the main chat and ask the Fantasy Cricket Assistant!*")
