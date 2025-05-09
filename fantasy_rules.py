def get_fantasy_rule_explanation(rule_type):
    """Return explanations for different fantasy cricket rules"""
    
    rules = {
        "general": """
📘 **Fantasy Cricket Rules Overview**

Fantasy Cricket is a game where you create a virtual team of real cricket players and score points based on how your players perform in real-life matches. Here's a quick overview:

1. **Team Creation**:
   - Select 11 players within a fixed budget (typically 100 credits)
   - Your team must include 1-4 wicketkeepers, 3-6 batsmen, 1-4 all-rounders, and 3-6 bowlers
   - You must select a Captain (2x points) and Vice-Captain (1.5x points)

2. **Scoring System**:
   - Batting points: Runs, boundaries, strike rate, milestones (50s/100s)
   - Bowling points: Wickets, economy rate, maiden overs, milestone (3+ wickets)
   - Fielding points: Catches, stumpings, run-outs
   - Bonus points for Player of the Match

3. **Contest Types**:
   - Head-to-Head: Compete directly against another player
   - Leagues: Join competitions with multiple participants
   - Mega Contests: Large tournaments with thousands of participants and big prizes

Ask me about specific aspects like "batting points" or "team composition" for more details!
""",
        
        "batting_points": """
🏏 **Fantasy Cricket Batting Points**

Here's how players earn points for batting performances:

**Basic Scoring**:
- 1 point per run scored
- 4 additional points for boundaries (fours)
- 6 additional points for sixes

**Milestones**:
- 50-99 runs: 20 bonus points
- 100+ runs: 40 bonus points

**Strike Rate Bonuses** (T20 matches):
- Strike Rate 150-174.99: 4 bonus points
- Strike Rate 175-199.99: 6 bonus points
- Strike Rate 200+: 8 bonus points

**Dismissals**:
- Duck (0 runs) by batsman: -2 points (only for batsmen, all-rounders, and wicket-keepers)

**Note**: Remember that your captain gets 2x points and vice-captain gets 1.5x points on all batting points earned!
""",
        
        "bowling_points": """
🎯 **Fantasy Cricket Bowling Points**

Here's how players earn points for bowling performances:

**Basic Scoring**:
- 25 points per wicket taken
- 12 points per maiden over (no runs scored)

**Milestones**:
- 3 wickets: 15 bonus points
- 4 wickets: 25 bonus points
- 5+ wickets: 40 bonus points

**Economy Rate Bonuses** (T20 matches):
- Economy Rate between 5-5.99: 4 points
- Economy Rate between 4-4.99: 7 points
- Economy Rate below 4: 10 points

**Economy Rate Penalties** (T20 matches):
- Economy Rate between 10-11: -2 points
- Economy Rate between 11.01-12: -4 points
- Economy Rate above 12: -6 points

**Note**: These points are adjusted for other formats (ODI, Test). Remember that your captain gets 2x points and vice-captain gets 1.5x points on all bowling points earned!
""",
        
        "fielding_points": """
🧤 **Fantasy Cricket Fielding Points**

Here's how players earn points for fielding performances:

**Basic Scoring**:
- Catch: 10 points per catch
- Stumping: 15 points per stumping
- Run Out (direct hit): 15 points
- Run Out (throwing or collecting): 10 points

**Wicketkeeping Bonuses**:
- 3+ dismissals (catches/stumpings) in a match: 5 bonus points
- 5+ dismissals in a match: 15 bonus points

**Fielding Bonuses**:
- 3+ catches in a match: 5 bonus points

**Note**: Remember that your captain gets 2x points and vice-captain gets 1.5x points on all fielding points earned!
""",
        
        "captain_points": """
👑 **Fantasy Cricket Captain & Vice-Captain Rules**

In fantasy cricket, selecting the right captain and vice-captain is crucial:

**Captain**:
- Your captain earns 2x (double) points for all their actions in the match
- For example, if a player scores 50 runs (50 points) as captain, you'll get 100 points

**Vice-Captain**:
- Your vice-captain earns 1.5x points for all their actions
- For example, if a player takes 3 wickets (75 points) as vice-captain, you'll get 112.5 points

**Strategy Tips**:
- Select in-form players for these roles
- All-rounders make great captains as they can earn points from both batting and bowling
- Consider the pitch conditions and match situation
- Look at the player's history at the venue
- For T20s, consider picking explosive batsmen or death-over specialists
- For test matches and ODIs, consistent performers are usually safer choices

Remember: Your captain and vice-captain selections often make the difference between winning and losing in fantasy cricket!
""",
        
        "team_composition": """
🏏 **Fantasy Cricket Team Composition Rules**

When creating your fantasy cricket team, you must follow these composition rules:

**Team Size**:
- Total of 11 players

**Budget Constraints**:
- 100 credit maximum (varies by platform)
- Each player has a price based on their real-world performance and popularity

**Player Categories**:
1. **Wicketkeepers**: 1-4 players
2. **Batsmen**: 3-6 players
3. **All-rounders**: 1-4 players
4. **Bowlers**: 3-6 players

**Team Selection Limits**:
- Maximum 7 players from any single team in the match

**Additional Requirements**:
- Must select 1 Captain (2x points)
- Must select 1 Vice-Captain (1.5x points)

**Strategy Tips**:
- Balance your team based on pitch conditions
- On batting-friendly pitches, invest more in top-order batsmen
- On bowling-friendly pitches, invest more in quality bowlers
- Always include players who bat in top order and bowl a few overs (dual value)
- Consider the recent form and matchups (e.g., specific batsmen's performance against left-arm bowlers)
""",
        
        "substitutions": """
🔄 **Fantasy Cricket Substitution Rules**

Different fantasy cricket platforms have different substitution rules, but here are the general guidelines:

**Before Match Deadline**:
- You can make unlimited changes to your team until the match deadline
- Once the match/tournament starts, your team gets locked

**Multi-Match Tournaments**:
- In tournaments like IPL, World Cup, etc., many platforms offer:
  - A set number of free substitutions for the entire tournament (e.g., 75-100 changes)
  - Ability to make team changes between matches
  - Opportunity to change captain and vice-captain between matches

**Injury Replacements**:
- If a selected player is declared unfit before the match and doesn't play, you don't get points
- Some platforms offer "auto-substitution" where bench players automatically replace non-playing selections

**Last-Minute Changes**:
- Always check team news before deadline to ensure your players are in the playing XI
- Pay attention to toss results as they can impact team selections and pitch conditions

Remember to use your substitutions wisely throughout a tournament to maximize your points potential!
"""
    }
    
    return rules.get(rule_type, rules["general"])
