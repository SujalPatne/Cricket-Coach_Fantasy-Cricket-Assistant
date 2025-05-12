from cricket_data_adapter import get_player_stats, get_recommended_players, get_upcoming_matches, get_pitch_conditions, get_player_form
from fantasy_rules import get_fantasy_rule_explanation
import re

# Greeting message
GREETING_MESSAGE = """
👋 Hello! I'm your Fantasy Cricket Assistant. I can help you make informed decisions for your fantasy cricket team.

Here's what I can assist you with:
- Player recommendations based on form and match conditions
- Detailed player statistics and analysis
- Fantasy cricket rules and scoring systems
- Match insights and pitch reports

What would you like to know today?
"""

# Patterns for matching user queries
PATTERNS = {
    'player_stats': r'(stats|statistics|info|information) (about|for|on) ([A-Za-z ]+)',
    'player_form': r'(form|performance) (of|for) ([A-Za-z ]+)|how is ([A-Za-z ]+) playing',
    'recommend_players': r'recommend|suggest|best|top|pick (.+)',
    'fantasy_rules': r'rules|scoring|points|how (to|do) (play|score)|fantasy (rules|points|scoring)',
    'pitch_report': r'pitch|ground|stadium|venue|condition(s)? (in|at|of) (.+)',
    'captain_picks': r'captain|vice(\s|-)captain|vc|c|who should (be|i pick as) (my)? captain',
    'upcoming_matches': r'matches|schedule|fixture|upcoming|next match',
    'recent_matches': r'recent|last|previous|completed|finished|results',
    'match_details': r'(match|game|scorecard|details|score) (of|for|about|id) ([A-Za-z0-9]+)',
    'live_matches': r'live|current|ongoing|today|now|playing',
    'greet': r'hi|hello|hey|greetings|sup|what\'s up',
    'thank': r'thanks|thank you|thx|ty',
    'compare': r'compare|versus|vs|difference between (.+) and (.+)',
}

def create_player_card(player):
    """Create a textual player card with stats"""
    card = f"📊 **{player['name']} ({player['team']})** - {player['role']}\n"
    card += f"💰 Price: {player['price']} | 👥 Ownership: {player['ownership']}%\n"

    if player['role'] == 'Batsman' or player['role'] == 'Wicketkeeper':
        card += f"🏏 Batting Avg: {player['batting_avg']} | ⚡ Strike Rate: {player['strike_rate']}\n"
        card += f"Recent Form: {', '.join(map(str, player['recent_form']))}\n"
    elif player['role'] == 'Bowler':
        card += f"🎯 Bowling Avg: {player['bowling_avg']} | 📈 Economy: {player['economy']}\n"
        card += f"Recent Wickets: {', '.join(map(str, player['recent_wickets']))}\n"
    elif player['role'] == 'All-rounder':
        card += f"🏏 Batting Avg: {player['batting_avg']} | 🎯 Bowling Avg: {player['bowling_avg']}\n"
        card += f"Recent Form: {', '.join(map(str, player['recent_form']))}\n"
        card += f"Recent Wickets: {', '.join(map(str, player['recent_wickets']))}\n"

    card += f"Fantasy Points Avg: {player['fantasy_points_avg']}\n"

    return card

def handle_player_stats_query(query):
    """Handle queries about player statistics"""
    # Extract player name from query using regex
    match = re.search(PATTERNS['player_stats'], query.lower())

    # If we found a match in the pattern
    if match:
        player_name = match.group(3).strip()
        player = get_player_stats(player_name)

        if player:
            return create_player_card(player)
        else:
            return f"I couldn't find statistics for {player_name}. Could you check the spelling or try another player?"

    # If no match in pattern, check for common player names
    common_players = ["Kohli", "Rohit", "Bumrah", "Dhoni", "Williamson", "Babar", "Stokes", "Smith"]
    for player_name in common_players:
        if player_name.lower() in query.lower():
            player = get_player_stats(player_name)
            if player:
                return create_player_card(player)

    # Extract any name-like words from the query
    words = query.split()
    for word in words:
        if len(word) > 3 and word.lower() not in ["show", "stats", "statistics", "about", "info", "player", "for", "me"]:
            player = get_player_stats(word)
            if player:
                return create_player_card(player)

    return "I need a player name to provide statistics. Could you specify which player you're interested in?"

def handle_player_form_query(query):
    """Handle queries about player current form"""
    match = re.search(PATTERNS['player_form'], query.lower())
    if match:
        # Check which pattern matched
        if match.group(3):  # (form|performance) (of|for) ([A-Za-z ]+)
            player_name = match.group(3).strip()
        else:  # how is ([A-Za-z ]+) playing
            player_name = match.group(4).strip()

        form = get_player_form(player_name)
        player = get_player_stats(player_name)

        if form and player:
            response = f"📈 **{player['name']}'s Current Form:** {form.capitalize()}\n\n"

            if player['role'] in ['Batsman', 'Wicketkeeper', 'All-rounder']:
                last_5_scores = player['recent_form']
                avg_last_5 = sum(last_5_scores) / len(last_5_scores)
                response += f"Last 5 innings: {', '.join(map(str, last_5_scores))}\n"
                response += f"Average in last 5 innings: {avg_last_5:.1f}\n"

            if player['role'] in ['Bowler', 'All-rounder']:
                last_5_wickets = player['recent_wickets']
                avg_wickets = sum(last_5_wickets) / len(last_5_wickets)
                response += f"Wickets in last 5 matches: {', '.join(map(str, last_5_wickets))}\n"
                response += f"Average wickets per match: {avg_wickets:.1f}\n"

            # Add recommendation based on form
            if form in ["excellent", "good"]:
                response += f"\n✅ Recommendation: {player['name']} is in {form} form and would be a good pick for your fantasy team."
            elif form == "average":
                response += f"\n⚠️ Recommendation: {player['name']} is in average form. Consider other factors like pitch conditions before selecting."
            else:
                response += f"\n❌ Recommendation: {player['name']} is not in great form recently. You might want to consider alternatives."

            return response
        else:
            return f"I couldn't find form information for {player_name}. Could you check the spelling or try another player?"

    # If no match in pattern, check for common player names
    common_players = ["Kohli", "Rohit", "Bumrah", "Dhoni", "Williamson", "Babar", "Stokes", "Smith"]
    for player_name in common_players:
        if player_name.lower() in query.lower():
            form = get_player_form(player_name)
            player = get_player_stats(player_name)
            if form and player:
                response = f"📈 **{player['name']}'s Current Form:** {form.capitalize()}\n\n"

                # Add more details as above...
                if player['role'] in ['Batsman', 'Wicketkeeper', 'All-rounder']:
                    last_5_scores = player['recent_form']
                    avg_last_5 = sum(last_5_scores) / len(last_5_scores)
                    response += f"Last 5 innings: {', '.join(map(str, last_5_scores))}\n"
                    response += f"Average in last 5 innings: {avg_last_5:.1f}\n"

                if player['role'] in ['Bowler', 'All-rounder']:
                    last_5_wickets = player['recent_wickets']
                    avg_wickets = sum(last_5_wickets) / len(last_5_wickets)
                    response += f"Wickets in last 5 matches: {', '.join(map(str, last_5_wickets))}\n"
                    response += f"Average wickets per match: {avg_wickets:.1f}\n"

                # Add recommendation
                if form in ["excellent", "good"]:
                    response += f"\n✅ Recommendation: {player['name']} is in {form} form and would be a good pick for your fantasy team."
                elif form == "average":
                    response += f"\n⚠️ Recommendation: {player['name']} is in average form. Consider other factors like pitch conditions before selecting."
                else:
                    response += f"\n❌ Recommendation: {player['name']} is not in great form recently. You might want to consider alternatives."

                return response

    return "I need a player name to provide form information. Could you specify which player you're interested in?"

def handle_recommend_players_query(query):
    """Handle queries for player recommendations"""
    role = None
    venue = None
    team = None
    budget = None

    # Extract role
    if "batsman" in query.lower() or "batsmen" in query.lower() or "batting" in query.lower():
        role = "Batsman"
    elif "bowler" in query.lower() or "bowling" in query.lower():
        role = "Bowler"
    elif "all-rounder" in query.lower() or "all rounder" in query.lower() or "allrounder" in query.lower():
        role = "All-rounder"
    elif "wicket keeper" in query.lower() or "wicketkeeper" in query.lower() or "keeper" in query.lower():
        role = "Wicketkeeper"

    # Extract venue
    venues = ["Mumbai", "Chennai", "Delhi", "Bangalore", "Kolkata", "Hyderabad"]
    for venue_name in venues:
        if venue_name.lower() in query.lower():
            venue = venue_name
            break

    # Extract team
    teams = ["India", "Australia", "England", "New Zealand", "South Africa", "Pakistan", "Bangladesh", "Afghanistan"]
    for team_name in teams:
        if team_name.lower() in query.lower():
            team = team_name
            break

    # Extract budget
    budget_match = re.search(r'budget (\d+\.?\d*)', query.lower())
    if budget_match:
        budget = float(budget_match.group(1))

    # Get recommendations
    recommendations = get_recommended_players(role, venue, team, budget)

    if not recommendations:
        return "I couldn't find any players matching your criteria. Try broadening your search parameters."

    # Build response
    response = "🏆 **Recommended Players:**\n\n"

    for i, player in enumerate(recommendations, 1):
        response += f"{i}. {player['name']} ({player['team']}) - {player['role']}\n"

        # Add reasoning
        if role == "Batsman" and venue:
            conditions = PITCH_CONDITIONS.get(venue, {})
            if conditions.get("batting_friendly", 0) > 7:
                response += f"   ✓ Great pick for batting-friendly {venue} pitch\n"
        elif role == "Bowler" and venue:
            conditions = PITCH_CONDITIONS.get(venue, {})
            if conditions.get("pace_friendly", 0) > 7 or conditions.get("spin_friendly", 0) > 7:
                response += f"   ✓ Well-suited for the {venue} pitch conditions\n"

        # Add form-based reasoning
        form = get_player_form(player['name'])
        if form in ["excellent", "good"]:
            response += f"   ✓ In {form} form recently\n"

        response += f"   💰 Price: {player['price']} | Fantasy Pts Avg: {player['fantasy_points_avg']}\n\n"

    return response

def handle_fantasy_rules_query(query):
    """Handle queries about fantasy cricket rules"""
    # Look for specific rule queries
    if "batting" in query.lower() and "points" in query.lower():
        return get_fantasy_rule_explanation("batting_points")
    elif "bowling" in query.lower() and "points" in query.lower():
        return get_fantasy_rule_explanation("bowling_points")
    elif "fielding" in query.lower() and "points" in query.lower():
        return get_fantasy_rule_explanation("fielding_points")
    elif "captain" in query.lower() or "vice-captain" in query.lower() or "vc" in query.lower():
        return get_fantasy_rule_explanation("captain_points")
    elif "substitute" in query.lower() or "replace" in query.lower():
        return get_fantasy_rule_explanation("substitutions")
    elif "lineup" in query.lower() or "team composition" in query.lower() or "selection" in query.lower():
        return get_fantasy_rule_explanation("team_composition")
    else:
        # General overview
        return get_fantasy_rule_explanation("general")

def handle_pitch_report_query(query):
    """Handle queries about pitch conditions"""
    match = re.search(r'(in|at|of) (.+)', query.lower())
    venue = None

    if match:
        venue_text = match.group(2).strip()
        venues = ["Mumbai", "Chennai", "Delhi", "Bangalore", "Kolkata", "Hyderabad"]
        for venue_name in venues:
            if venue_name.lower() in venue_text:
                venue = venue_name
                break

    if not venue:
        venues = ["Mumbai", "Chennai", "Delhi", "Bangalore", "Kolkata", "Hyderabad"]
        for venue_name in venues:
            if venue_name.lower() in query.lower():
                venue = venue_name
                break

    if venue:
        conditions = get_pitch_conditions(venue)

        response = f"🏟️ **Pitch Report: {venue} Stadium**\n\n"

        # Translate numerical values to descriptive text
        batting_desc = "Very batting friendly" if conditions["batting_friendly"] >= 8 else \
                       "Batting friendly" if conditions["batting_friendly"] >= 6 else \
                       "Balanced for batting" if conditions["batting_friendly"] >= 5 else \
                       "Challenging for batsmen"

        pace_desc = "Very pace friendly" if conditions["pace_friendly"] >= 8 else \
                   "Good for pace bowlers" if conditions["pace_friendly"] >= 6 else \
                   "Moderate assistance for pacers" if conditions["pace_friendly"] >= 5 else \
                   "Limited help for pace bowlers"

        spin_desc = "Very spin friendly" if conditions["spin_friendly"] >= 8 else \
                   "Good for spinners" if conditions["spin_friendly"] >= 6 else \
                   "Moderate assistance for spinners" if conditions["spin_friendly"] >= 5 else \
                   "Limited help for spin bowlers"

        response += f"• Batting Conditions: {batting_desc}\n"
        response += f"• Pace Bowling: {pace_desc}\n"
        response += f"• Spin Bowling: {spin_desc}\n\n"

        # Add recommendations based on conditions
        response += "**Recommendations:**\n"

        if conditions["batting_friendly"] >= 7:
            response += "✓ Consider picking top-order batsmen from both teams\n"

        if conditions["pace_friendly"] >= 7:
            response += "✓ Fast bowlers should do well on this pitch\n"

        if conditions["spin_friendly"] >= 7:
            response += "✓ Include quality spinners in your team\n"

        if conditions["batting_friendly"] <= 5:
            response += "✓ Pick batsmen with good technique rather than aggressive players\n"

        return response
    else:
        return "I couldn't find pitch information for that venue. Try specifying a different stadium like Mumbai, Chennai, Delhi, etc."

def handle_captain_picks_query(query):
    """Handle queries about captain and vice-captain picks"""
    # Get top performing players
    all_players = get_recommended_players()

    # Filter by role
    batsmen = [p for p in all_players if p.get("role") == "Batsman"]
    allrounders = [p for p in all_players if p.get("role") == "All-rounder"]

    # Limit to top 3 batsmen and top 2 all-rounders
    top_batsmen = batsmen[:3] if len(batsmen) >= 3 else batsmen
    top_allrounders = allrounders[:2] if len(allrounders) >= 2 else allrounders

    response = "👑 **Captain & Vice-Captain Recommendations**\n\n"

    # Captain picks (usually all-rounders or in-form batsmen)
    response += "**Captain Picks:**\n"
    captain_picks = top_allrounders + top_batsmen[:1]
    for i, player in enumerate(captain_picks, 1):
        form = get_player_form(player['name'])
        form_desc = f"in {form} form" if form else ""
        response += f"{i}. {player['name']} ({player['team']}) - {player['role']} {form_desc}\n"
        response += f"   Fantasy Pts Avg: {player['fantasy_points_avg']} | As captain: {player['fantasy_points_avg'] * 2}\n\n"

    # Vice-captain picks
    response += "**Vice-Captain Picks:**\n"
    vc_picks = top_batsmen[1:3] if len(top_batsmen) > 1 else top_batsmen
    for i, player in enumerate(vc_picks, 1):
        form = get_player_form(player['name'])
        form_desc = f"in {form} form" if form else ""
        response += f"{i}. {player['name']} ({player['team']}) - {player['role']} {form_desc}\n"
        response += f"   Fantasy Pts Avg: {player['fantasy_points_avg']} | As VC: {player['fantasy_points_avg'] * 1.5}\n\n"

    response += "Remember: Captain gets 2x points and Vice-Captain gets 1.5x points, so choose wisely!"

    return response

def handle_upcoming_matches_query(query):
    """Handle queries about upcoming matches"""
    matches = get_upcoming_matches()

    if not matches:
        return "I couldn't find information about upcoming matches at the moment."

    response = "🗓️ **Upcoming Matches**\n\n"

    for i, match in enumerate(matches, 1):
        response += f"{i}. {match['teams']}\n"
        response += f"   Venue: {match['venue']} | Date: {match['date']}\n"

        # Add pitch insights if available
        venue = match['venue']
        conditions = get_pitch_conditions(venue)
        if conditions["batting_friendly"] >= 7:
            response += f"   Pitch Insight: Batting-friendly pitch at {match['venue']}\n"
        elif conditions["pace_friendly"] >= 7:
            response += f"   Pitch Insight: Good for pace bowlers at {match['venue']}\n"
        elif conditions["spin_friendly"] >= 7:
            response += f"   Pitch Insight: Spin-friendly conditions expected at {match['venue']}\n"

        response += "\n"

    return response

def handle_compare_players_query(query):
    """Handle queries comparing two players"""
    match = re.search(PATTERNS['compare'], query.lower())

    if match:
        player1_name = match.group(1).strip()
        player2_name = match.group(2).strip()

        player1 = get_player_stats(player1_name)
        player2 = get_player_stats(player2_name)

        if player1 and player2:
            response = f"🔄 **Comparing {player1['name']} vs {player2['name']}**\n\n"

            # Compare roles
            response += f"**Role:** {player1['role']} vs {player2['role']}\n"
            response += f"**Team:** {player1['team']} vs {player2['team']}\n\n"

            # Compare fantasy metrics
            response += f"**Fantasy Points Avg:** {player1['fantasy_points_avg']} vs {player2['fantasy_points_avg']}\n"
            response += f"**Price:** {player1['price']} vs {player2['price']}\n"
            response += f"**Ownership %:** {player1['ownership']}% vs {player2['ownership']}%\n\n"

            # Compare batting if applicable
            if 'batting_avg' in player1 and 'batting_avg' in player2:
                response += f"**Batting Avg:** {player1['batting_avg']} vs {player2['batting_avg']}\n"

            # Compare bowling if applicable
            if 'bowling_avg' in player1 and 'bowling_avg' in player2:
                response += f"**Bowling Avg:** {player1['bowling_avg']} vs {player2['bowling_avg']}\n"

            # Compare form
            form1 = get_player_form(player1['name'])
            form2 = get_player_form(player2['name'])
            response += f"**Current Form:** {form1.capitalize() if form1 else 'Unknown'} vs {form2.capitalize() if form2 else 'Unknown'}\n\n"

            # Recommendation
            if player1['fantasy_points_avg'] > player2['fantasy_points_avg'] * 1.1:  # At least 10% better
                response += f"✅ **Recommendation:** {player1['name']} appears to be the better fantasy pick overall."
            elif player2['fantasy_points_avg'] > player1['fantasy_points_avg'] * 1.1:
                response += f"✅ **Recommendation:** {player2['name']} appears to be the better fantasy pick overall."
            else:
                response += "✅ **Recommendation:** Both players are quite evenly matched. Consider other factors like match conditions and team combinations."

            return response
        elif not player1:
            return f"I couldn't find information for {player1_name}. Could you check the spelling or try another player?"
        elif not player2:
            return f"I couldn't find information for {player2_name}. Could you check the spelling or try another player?"

    return "To compare players, please specify two players like 'Compare Virat Kohli and Kane Williamson'."

def handle_recent_matches_query(query):
    """Handle queries about recent matches"""
    from cricket_data_adapter import get_recent_matches

    recent_matches = get_recent_matches()

    if not recent_matches:
        return "I couldn't find any recent matches. Please try again later."

    response = "🏏 **Recent Cricket Matches**\n\n"

    for match in recent_matches[:5]:  # Limit to 5 matches
        source = match.get('source', 'Unknown')
        match_info = f"• {match.get('teams', 'Unknown vs Unknown')}\n"
        match_info += f"  📍 {match.get('venue', 'Unknown')}\n"
        match_info += f"  📅 {match.get('date', 'Unknown')}\n"
        match_info += f"  🏆 {match.get('status', 'Unknown')}\n"
        match_info += f"  🔄 Source: {source}\n"

        if 'match_id' in match:
            match_info += f"  🆔 Match ID: {match.get('match_id')}\n"

        response += match_info + "\n"

    response += "You can get more details about a specific match by asking for 'match details for [Match ID]'."

    return response

def handle_live_matches_query(query):
    """Handle queries about live matches"""
    from cricket_data_adapter import get_live_cricket_matches

    live_matches = get_live_cricket_matches()

    if not live_matches:
        return "I couldn't find any live matches at the moment. Try checking for upcoming or recent matches instead."

    response = "🔴 **Live Cricket Matches**\n\n"

    for match in live_matches:
        source = match.get('source', 'Unknown')
        match_info = f"• {match.get('teams', 'Unknown vs Unknown')}\n"
        match_info += f"  📍 {match.get('venue', 'Unknown')}\n"
        match_info += f"  📊 {match.get('status', 'Unknown')}\n"
        match_info += f"  🔄 Source: {source}\n"

        if 'match_id' in match:
            match_info += f"  🆔 Match ID: {match.get('match_id')}\n"

        response += match_info + "\n"

    response += "You can get more details about a specific match by asking for 'match details for [Match ID]'."

    return response

def handle_match_details_query(query):
    """Handle queries about specific match details"""
    from cricket_data_adapter import get_match_details

    # Extract match ID from query
    match = re.search(PATTERNS['match_details'], query.lower())
    if match:
        match_id = match.group(3)
    else:
        # Try to find a match ID in the query
        match_id_pattern = r'([a-zA-Z0-9]+)'
        match_id_match = re.search(match_id_pattern, query)
        if match_id_match:
            match_id = match_id_match.group(1)
        else:
            return "I couldn't identify a match ID in your query. Please specify a match ID, for example: 'match details for 12345'."

    # Get match details
    match_details = get_match_details(match_id)

    if 'error' in match_details:
        return f"I couldn't find details for match ID {match_id}. Please check the ID and try again."

    # Format response
    response = f"🏏 **Match Details: {match_details.get('teams', 'Unknown vs Unknown')}**\n\n"
    response += f"📍 Venue: {match_details.get('venue', 'Unknown')}\n"
    response += f"📅 Date: {match_details.get('date', 'Unknown')}\n"
    response += f"🏆 Format: {match_details.get('match_type', 'Unknown')}\n"
    response += f"📊 Status: {match_details.get('status', 'Unknown')}\n"
    response += f"🔄 Source: {match_details.get('source', 'Unknown')}\n\n"

    # Add scores
    scores = match_details.get('scores', [])
    if scores:
        response += "**Scorecard:**\n"
        for score in scores:
            response += f"• {score.get('score_str', 'Unknown')}\n"

    # Add pitch conditions
    pitch_conditions = match_details.get('pitch_conditions', {})
    if pitch_conditions:
        response += "\n**Pitch Conditions:**\n"
        response += f"• Batting friendly: {pitch_conditions.get('batting_friendly', 'Unknown')}/10\n"
        response += f"• Pace friendly: {pitch_conditions.get('pace_friendly', 'Unknown')}/10\n"
        response += f"• Spin friendly: {pitch_conditions.get('spin_friendly', 'Unknown')}/10\n"

    return response

def generate_response(query):
    """Generate a response based on the user's query"""
    # Check for greeting
    if re.search(PATTERNS['greet'], query.lower()):
        return "👋 Hello! How can I help with your fantasy cricket team today?"

    # Check for thanks
    if re.search(PATTERNS['thank'], query.lower()):
        return "You're welcome! Feel free to ask if you need more fantasy cricket advice."

    # Check for player stats query
    if re.search(PATTERNS['player_stats'], query.lower()):
        return handle_player_stats_query(query)

    # Check for player form query
    if re.search(PATTERNS['player_form'], query.lower()):
        return handle_player_form_query(query)

    # Check for recommendation query
    if re.search(PATTERNS['recommend_players'], query.lower()):
        return handle_recommend_players_query(query)

    # Check for fantasy rules query
    if re.search(PATTERNS['fantasy_rules'], query.lower()):
        return handle_fantasy_rules_query(query)

    # Check for pitch report query
    if re.search(PATTERNS['pitch_report'], query.lower()):
        return handle_pitch_report_query(query)

    # Check for captain picks query
    if re.search(PATTERNS['captain_picks'], query.lower()):
        return handle_captain_picks_query(query)

    # Check for upcoming matches query
    if re.search(PATTERNS['upcoming_matches'], query.lower()):
        return handle_upcoming_matches_query(query)

    # Check for recent matches query
    if re.search(PATTERNS['recent_matches'], query.lower()):
        return handle_recent_matches_query(query)

    # Check for live matches query
    if re.search(PATTERNS['live_matches'], query.lower()):
        return handle_live_matches_query(query)

    # Check for match details query
    if re.search(PATTERNS['match_details'], query.lower()):
        return handle_match_details_query(query)

    # Check for player comparison query
    if re.search(PATTERNS['compare'], query.lower()):
        return handle_compare_players_query(query)

    # General queries about players might not match the exact patterns
    player_names = {
        "kohli": "Virat Kohli",
        "virat": "Virat Kohli",
        "virat kohli": "Virat Kohli",
        "rohit": "Rohit Sharma",
        "sharma": "Rohit Sharma",
        "rohit sharma": "Rohit Sharma",
        "bumrah": "Jasprit Bumrah",
        "jasprit": "Jasprit Bumrah",
        "jasprit bumrah": "Jasprit Bumrah",
        "williamson": "Kane Williamson",
        "kane": "Kane Williamson",
        "kane williamson": "Kane Williamson",
        "rashid": "Rashid Khan",
        "rashid khan": "Rashid Khan",
        "stokes": "Ben Stokes",
        "ben": "Ben Stokes",
        "ben stokes": "Ben Stokes",
        "dhoni": "MS Dhoni",
        "ms": "MS Dhoni",
        "ms dhoni": "MS Dhoni"
    }

    # Check if any player name is in the query
    for key, full_name in player_names.items():
        if key in query.lower():
            # If the query is just the player name or very simple
            if len(query.split()) <= 3:
                return handle_player_stats_query(f"Statistics about {full_name}")
            # If query mentions form or performance
            elif "form" in query.lower() or "performance" in query.lower():
                return handle_player_form_query(f"How is {full_name} playing?")
            # If query mentions stats or statistics
            elif "stats" in query.lower() or "statistics" in query.lower() or "info" in query.lower():
                return handle_player_stats_query(f"Statistics about {full_name}")
            # Default to stats for any other query mentioning the player
            else:
                return handle_player_stats_query(f"Statistics about {full_name}")

    # If nothing matched, provide a general response
    return """I'm not sure what you're asking. I can help with:
- Player statistics (e.g., "Show me stats for Virat Kohli")
- Player form (e.g., "How is Bumrah playing?")
- Recommendations (e.g., "Suggest batsmen for today's match")
- Fantasy rules (e.g., "Explain fantasy cricket scoring")
- Pitch reports (e.g., "Pitch conditions in Mumbai")
- Captain picks (e.g., "Who should be my captain?")
- Upcoming matches (e.g., "Show upcoming matches")
- Recent matches (e.g., "Show recent match results")
- Live matches (e.g., "Show live matches")
- Match details (e.g., "Match details for 12345")
- Player comparisons (e.g., "Compare Rohit and Kohli")

How can I assist you?"""
