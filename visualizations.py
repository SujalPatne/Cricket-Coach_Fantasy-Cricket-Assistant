import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional
import logging
from db_manager import DatabaseManager
from models import Player, Team, Match, PlayerPerformance

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set Seaborn style
sns.set_style("whitegrid")

def player_performance_chart(player_name: str):
    """
    Create a performance chart for a player
    
    Parameters:
    - player_name: Name of the player
    """
    try:
        db = DatabaseManager()
        player = db.get_player_by_name(player_name)
        
        if not player:
            st.warning(f"Player {player_name} not found in database")
            return
        
        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot recent form (batting)
        if player.recent_form and isinstance(player.recent_form, list):
            recent_form = player.recent_form
            matches = list(range(1, len(recent_form) + 1))
            
            axes[0].plot(matches, recent_form, marker='o', linestyle='-', color='#1A73E8')
            axes[0].set_title(f"{player.name} - Recent Batting Form")
            axes[0].set_xlabel("Recent Matches")
            axes[0].set_ylabel("Runs Scored")
            axes[0].grid(True, linestyle='--', alpha=0.7)
            
            # Add average line
            avg = sum(recent_form) / len(recent_form)
            axes[0].axhline(y=avg, color='#EA4335', linestyle='--', label=f'Average: {avg:.1f}')
            axes[0].legend()
        
        # Plot recent wickets (bowling) if available
        if hasattr(player, 'recent_wickets') and player.recent_wickets and isinstance(player.recent_wickets, list):
            recent_wickets = player.recent_wickets
            matches = list(range(1, len(recent_wickets) + 1))
            
            axes[1].plot(matches, recent_wickets, marker='o', linestyle='-', color='#34A853')
            axes[1].set_title(f"{player.name} - Recent Bowling Form")
            axes[1].set_xlabel("Recent Matches")
            axes[1].set_ylabel("Wickets Taken")
            axes[1].grid(True, linestyle='--', alpha=0.7)
            
            # Add average line
            avg = sum(recent_wickets) / len(recent_wickets)
            axes[1].axhline(y=avg, color='#EA4335', linestyle='--', label=f'Average: {avg:.1f}')
            axes[1].legend()
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Additional player stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Player Statistics")
            stats = {
                "Role": player.role,
                "Team": player.team.name if player.team else "Unknown",
                "Batting Average": f"{player.batting_avg:.1f}" if player.batting_avg else "N/A",
                "Strike Rate": f"{player.strike_rate:.1f}" if player.strike_rate else "N/A",
                "Fantasy Points Avg": f"{player.fantasy_points_avg:.1f}" if player.fantasy_points_avg else "N/A",
                "Matches Played": player.matches_played or "N/A"
            }
            
            # Create a DataFrame for better display
            stats_df = pd.DataFrame(list(stats.items()), columns=["Metric", "Value"])
            st.table(stats_df)
        
        with col2:
            st.subheader("Fantasy Cricket Value")
            if player.price and player.fantasy_points_avg:
                value = player.fantasy_points_avg / player.price
                
                # Create gauge chart for value
                fig, ax = plt.subplots(figsize=(4, 3))
                
                # Define value ranges
                poor = 5
                average = 7.5
                good = 10
                excellent = 12.5
                
                # Create gauge
                gauge_colors = ['#EA4335', '#FBBC05', '#34A853', '#1A73E8']
                bounds = [0, poor, average, good, excellent]
                norm = plt.Normalize(0, excellent)
                
                # Plot the gauge background
                for i in range(len(bounds)-1):
                    ax.axvspan(bounds[i], bounds[i+1], alpha=0.3, color=gauge_colors[i])
                
                # Plot the needle
                ax.arrow(0, 0, min(value, excellent), 0, head_width=0.3, head_length=0.8, fc='black', ec='black')
                
                # Set up the plot
                ax.set_xlim(0, excellent)
                ax.set_ylim(-1, 1)
                ax.set_yticks([])
                ax.set_xticks([poor, average, good, excellent])
                ax.set_xticklabels(['Poor', 'Average', 'Good', 'Excellent'])
                ax.set_title(f"Value Rating: {value:.2f}")
                
                st.pyplot(fig)
                
                # Ownership percentage
                if player.ownership:
                    st.metric("Ownership", f"{player.ownership:.1f}%")
                
                # Price
                st.metric("Price", f"{player.price:.1f}")
    
    except Exception as e:
        logger.error(f"Error creating player performance chart: {str(e)}")
        st.error(f"Error creating visualization: {str(e)}")
    finally:
        db.close()

def team_comparison_chart(team1_name: str, team2_name: str):
    """
    Create a comparison chart for two teams
    
    Parameters:
    - team1_name: Name of the first team
    - team2_name: Name of the second team
    """
    try:
        db = DatabaseManager()
        team1_players = db.get_players_by_team(team1_name)
        team2_players = db.get_players_by_team(team2_name)
        
        if not team1_players:
            st.warning(f"No players found for team {team1_name}")
            return
        
        if not team2_players:
            st.warning(f"No players found for team {team2_name}")
            return
        
        # Calculate team averages
        team1_batting_avg = sum(p.batting_avg for p in team1_players if p.batting_avg) / len([p for p in team1_players if p.batting_avg]) if any(p.batting_avg for p in team1_players) else 0
        team2_batting_avg = sum(p.batting_avg for p in team2_players if p.batting_avg) / len([p for p in team2_players if p.batting_avg]) if any(p.batting_avg for p in team2_players) else 0
        
        team1_bowling_avg = sum(p.bowling_avg for p in team1_players if p.bowling_avg) / len([p for p in team1_players if p.bowling_avg]) if any(p.bowling_avg for p in team1_players) else 0
        team2_bowling_avg = sum(p.bowling_avg for p in team2_players if p.bowling_avg) / len([p for p in team2_players if p.bowling_avg]) if any(p.bowling_avg for p in team2_players) else 0
        
        team1_fantasy_avg = sum(p.fantasy_points_avg for p in team1_players if p.fantasy_points_avg) / len([p for p in team1_players if p.fantasy_points_avg]) if any(p.fantasy_points_avg for p in team1_players) else 0
        team2_fantasy_avg = sum(p.fantasy_points_avg for p in team2_players if p.fantasy_points_avg) / len([p for p in team2_players if p.fantasy_points_avg]) if any(p.fantasy_points_avg for p in team2_players) else 0
        
        # Create comparison chart
        categories = ['Batting Average', 'Bowling Average', 'Fantasy Points']
        team1_values = [team1_batting_avg, team1_bowling_avg, team1_fantasy_avg]
        team2_values = [team2_batting_avg, team2_bowling_avg, team2_fantasy_avg]
        
        # Set up the radar chart
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]  # Close the loop
        
        team1_values += team1_values[:1]  # Close the loop
        team2_values += team2_values[:1]  # Close the loop
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        ax.plot(angles, team1_values, 'o-', linewidth=2, label=team1_name, color='#1A73E8')
        ax.fill(angles, team1_values, alpha=0.25, color='#1A73E8')
        
        ax.plot(angles, team2_values, 'o-', linewidth=2, label=team2_name, color='#EA4335')
        ax.fill(angles, team2_values, alpha=0.25, color='#EA4335')
        
        ax.set_thetagrids(np.degrees(angles[:-1]), categories)
        ax.set_title(f"Team Comparison: {team1_name} vs {team2_name}")
        ax.grid(True)
        ax.legend(loc='upper right')
        
        st.pyplot(fig)
        
        # Show top players from each team
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Top Players - {team1_name}")
            top_team1 = sorted(team1_players, key=lambda p: p.fantasy_points_avg if p.fantasy_points_avg else 0, reverse=True)[:5]
            
            data = []
            for player in top_team1:
                data.append({
                    "Name": player.name,
                    "Role": player.role,
                    "Fantasy Pts": f"{player.fantasy_points_avg:.1f}" if player.fantasy_points_avg else "N/A"
                })
            
            st.table(pd.DataFrame(data))
        
        with col2:
            st.subheader(f"Top Players - {team2_name}")
            top_team2 = sorted(team2_players, key=lambda p: p.fantasy_points_avg if p.fantasy_points_avg else 0, reverse=True)[:5]
            
            data = []
            for player in top_team2:
                data.append({
                    "Name": player.name,
                    "Role": player.role,
                    "Fantasy Pts": f"{player.fantasy_points_avg:.1f}" if player.fantasy_points_avg else "N/A"
                })
            
            st.table(pd.DataFrame(data))
    
    except Exception as e:
        logger.error(f"Error creating team comparison chart: {str(e)}")
        st.error(f"Error creating visualization: {str(e)}")
    finally:
        db.close()

def fantasy_points_projection(player_names: List[str]):
    """
    Create fantasy points projection for a list of players
    
    Parameters:
    - player_names: List of player names
    """
    try:
        db = DatabaseManager()
        players = []
        
        for name in player_names:
            player = db.get_player_by_name(name)
            if player:
                players.append(player)
        
        if not players:
            st.warning("No players found for projection")
            return
        
        # Create projection chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [p.name for p in players]
        points = [p.fantasy_points_avg for p in players if p.fantasy_points_avg]
        errors = [p.fantasy_points_avg * 0.2 for p in players if p.fantasy_points_avg]  # 20% error margin
        
        # Sort by points
        sorted_indices = np.argsort(points)
        names = [names[i] for i in sorted_indices]
        points = [points[i] for i in sorted_indices]
        errors = [errors[i] for i in sorted_indices]
        
        # Create horizontal bar chart with error bars
        y_pos = np.arange(len(names))
        ax.barh(y_pos, points, xerr=errors, align='center', color='#1A73E8', ecolor='black', capsize=5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()  # Labels read top-to-bottom
        ax.set_xlabel('Projected Fantasy Points')
        ax.set_title('Fantasy Points Projection with Uncertainty')
        
        st.pyplot(fig)
        
        # Show projection table
        st.subheader("Fantasy Points Projection Details")
        
        data = []
        for player in players:
            if player.fantasy_points_avg:
                # Calculate projection range
                lower = player.fantasy_points_avg * 0.8
                upper = player.fantasy_points_avg * 1.2
                
                data.append({
                    "Player": player.name,
                    "Role": player.role,
                    "Team": player.team.name if player.team else "Unknown",
                    "Projected Points": f"{player.fantasy_points_avg:.1f}",
                    "Range": f"{lower:.1f} - {upper:.1f}",
                    "Price": f"{player.price:.1f}" if player.price else "N/A",
                    "Value": f"{(player.fantasy_points_avg / player.price):.2f}" if player.price and player.fantasy_points_avg else "N/A"
                })
        
        st.table(pd.DataFrame(data))
    
    except Exception as e:
        logger.error(f"Error creating fantasy points projection: {str(e)}")
        st.error(f"Error creating visualization: {str(e)}")
    finally:
        db.close()
