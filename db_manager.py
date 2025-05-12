from sqlalchemy.orm import Session
from models import (
    User, UserPreference, ChatHistory, Player, Team, 
    Match, PlayerPerformance, get_session
)
from datetime import datetime
import json
import os
from typing import List, Dict, Any, Optional
import logging
import bcrypt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data file paths (for migration from JSON)
DATA_DIR = "data"
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")
USER_PREFERENCES_FILE = os.path.join(DATA_DIR, "user_preferences.json")
PLAYERS_DATA_FILE = os.path.join(DATA_DIR, "players_data.json")
MATCH_DATA_FILE = os.path.join(DATA_DIR, "match_data.json")

class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self):
        """Initialize database manager with a session"""
        self.session = get_session()
    
    def close(self):
        """Close the database session"""
        self.session.close()
    
    # User management methods
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user with hashed password"""
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            
            # Create default preferences
            preferences = UserPreference(user=user)
            
            # Add to session and commit
            self.session.add(user)
            self.session.add(preferences)
            self.session.commit()
            
            logger.info(f"Created user: {username}")
            return user
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        try:
            user = self.session.query(User).filter_by(username=username).first()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Update last login time
                user.last_login = datetime.utcnow()
                self.session.commit()
                return user
            
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return self.session.query(User).filter_by(id=user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        return self.session.query(User).filter_by(username=username).first()
    
    # Chat history methods
    def save_chat(self, user_id: int, user_message: str, assistant_response: str, ai_model_used: str = "unknown") -> ChatHistory:
        """Save a chat exchange to the database"""
        try:
            chat = ChatHistory(
                user_id=user_id,
                user_message=user_message,
                assistant_response=assistant_response,
                ai_model_used=ai_model_used,
                timestamp=datetime.utcnow()
            )
            
            self.session.add(chat)
            self.session.commit()
            return chat
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving chat: {str(e)}")
            raise
    
    def get_user_chats(self, user_id: int, limit: int = 10) -> List[ChatHistory]:
        """Get recent chats for a user"""
        return self.session.query(ChatHistory).filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
    
    # Player methods
    def save_player(self, player_data: Dict[str, Any]) -> Player:
        """Save a player to the database"""
        try:
            # Check if player exists by name
            player = self.session.query(Player).filter_by(name=player_data['name']).first()
            
            # Get or create team
            team = None
            if 'team' in player_data and player_data['team']:
                team = self.session.query(Team).filter_by(name=player_data['team']).first()
                if not team:
                    team = Team(name=player_data['team'])
                    self.session.add(team)
                    self.session.flush()
            
            if player:
                # Update existing player
                player.role = player_data.get('role', player.role)
                player.team_id = team.id if team else player.team_id
                player.batting_avg = player_data.get('batting_avg', player.batting_avg)
                player.bowling_avg = player_data.get('bowling_avg', player.bowling_avg)
                player.strike_rate = player_data.get('strike_rate', player.strike_rate)
                player.economy = player_data.get('economy', player.economy)
                player.recent_form = player_data.get('recent_form', player.recent_form)
                player.recent_wickets = player_data.get('recent_wickets', player.recent_wickets)
                player.fantasy_points_avg = player_data.get('fantasy_points_avg', player.fantasy_points_avg)
                player.ownership = player_data.get('ownership', player.ownership)
                player.price = player_data.get('price', player.price)
                player.matches_played = player_data.get('matches_played', player.matches_played)
                player.last_updated = datetime.utcnow()
            else:
                # Create new player
                player = Player(
                    name=player_data['name'],
                    role=player_data.get('role'),
                    team_id=team.id if team else None,
                    batting_avg=player_data.get('batting_avg'),
                    bowling_avg=player_data.get('bowling_avg'),
                    strike_rate=player_data.get('strike_rate'),
                    economy=player_data.get('economy'),
                    recent_form=player_data.get('recent_form'),
                    recent_wickets=player_data.get('recent_wickets'),
                    fantasy_points_avg=player_data.get('fantasy_points_avg'),
                    ownership=player_data.get('ownership'),
                    price=player_data.get('price'),
                    matches_played=player_data.get('matches_played'),
                    last_updated=datetime.utcnow()
                )
                self.session.add(player)
            
            self.session.commit()
            return player
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving player: {str(e)}")
            raise
    
    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get a player by name"""
        return self.session.query(Player).filter_by(name=name).first()
    
    def get_players_by_role(self, role: str) -> List[Player]:
        """Get players by role"""
        return self.session.query(Player).filter_by(role=role).all()
    
    def get_players_by_team(self, team_name: str) -> List[Player]:
        """Get players by team name"""
        team = self.session.query(Team).filter_by(name=team_name).first()
        if team:
            return self.session.query(Player).filter_by(team_id=team.id).all()
        return []
    
    # Match methods
    def save_match(self, match_data: Dict[str, Any]) -> Match:
        """Save a match to the database"""
        try:
            # Get or create teams
            home_team = None
            away_team = None
            
            if 'home_team' in match_data:
                home_team = self.session.query(Team).filter_by(name=match_data['home_team']).first()
                if not home_team:
                    home_team = Team(name=match_data['home_team'])
                    self.session.add(home_team)
                    self.session.flush()
            
            if 'away_team' in match_data:
                away_team = self.session.query(Team).filter_by(name=match_data['away_team']).first()
                if not away_team:
                    away_team = Team(name=match_data['away_team'])
                    self.session.add(away_team)
                    self.session.flush()
            
            # Create match
            match = Match(
                home_team_id=home_team.id if home_team else None,
                away_team_id=away_team.id if away_team else None,
                venue=match_data.get('venue'),
                match_date=match_data.get('match_date'),
                match_type=match_data.get('match_type'),
                status=match_data.get('status'),
                result=match_data.get('result'),
                pitch_conditions=match_data.get('pitch_conditions'),
                weather=match_data.get('weather')
            )
            
            self.session.add(match)
            self.session.commit()
            return match
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving match: {str(e)}")
            raise
    
    def get_upcoming_matches(self) -> List[Match]:
        """Get upcoming matches"""
        return self.session.query(Match).filter_by(status='Upcoming').order_by(Match.match_date).all()
    
    def get_live_matches(self) -> List[Match]:
        """Get live matches"""
        return self.session.query(Match).filter_by(status='Live').all()
    
    # Migration methods
    def migrate_from_json(self):
        """Migrate data from JSON files to database"""
        self._migrate_players()
        self._migrate_matches()
        self._migrate_chat_history()
        logger.info("Data migration completed")
    
    def _migrate_players(self):
        """Migrate player data from JSON"""
        try:
            if os.path.exists(PLAYERS_DATA_FILE):
                with open(PLAYERS_DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                for player_data in data.get('players', []):
                    self.save_player(player_data)
                
                logger.info(f"Migrated {len(data.get('players', []))} players from JSON")
        except Exception as e:
            logger.error(f"Error migrating players: {str(e)}")
    
    def _migrate_matches(self):
        """Migrate match data from JSON"""
        try:
            if os.path.exists(MATCH_DATA_FILE):
                with open(MATCH_DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                for match_data in data.get('matches', []):
                    # Process match data
                    if 'teams' in match_data:
                        teams = match_data['teams'].split(' vs ')
                        if len(teams) == 2:
                            match_data['home_team'] = teams[0]
                            match_data['away_team'] = teams[1]
                    
                    self.save_match(match_data)
                
                logger.info(f"Migrated {len(data.get('matches', []))} matches from JSON")
        except Exception as e:
            logger.error(f"Error migrating matches: {str(e)}")
    
    def _migrate_chat_history(self):
        """Migrate chat history from JSON"""
        try:
            if os.path.exists(CHAT_HISTORY_FILE):
                with open(CHAT_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                
                for chat in data.get('chats', []):
                    # Create anonymous user if needed
                    user_id = chat.get('user_id')
                    user = self.get_user_by_username(user_id)
                    
                    if not user:
                        user = User(
                            username=user_id,
                            email=f"{user_id}@example.com",
                            password_hash="migrated",
                            created_at=datetime.utcnow()
                        )
                        self.session.add(user)
                        self.session.flush()
                    
                    # Create chat entry
                    chat_entry = ChatHistory(
                        user_id=user.id,
                        user_message=chat.get('user_message', ''),
                        assistant_response=chat.get('assistant_response', ''),
                        timestamp=datetime.fromisoformat(chat.get('timestamp', datetime.utcnow().isoformat())),
                        ai_model_used='rule-based'
                    )
                    
                    self.session.add(chat_entry)
                
                self.session.commit()
                logger.info(f"Migrated {len(data.get('chats', []))} chat entries from JSON")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error migrating chat history: {str(e)}")
