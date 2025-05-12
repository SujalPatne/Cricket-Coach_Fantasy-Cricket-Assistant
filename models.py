from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

# Create base class for declarative models
Base = declarative_base()

# Define association tables for many-to-many relationships
user_favorite_players = Table(
    'user_favorite_players',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('player_id', Integer, ForeignKey('players.id'))
)

user_favorite_teams = Table(
    'user_favorite_teams',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)

class User(Base):
    """User model for authentication and personalization"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    chats = relationship("ChatHistory", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    favorite_players = relationship("Player", secondary=user_favorite_players)
    favorite_teams = relationship("Team", secondary=user_favorite_teams)

    def __repr__(self):
        return f"<User {self.username}>"

class UserPreference(Base):
    """User preferences for app settings"""
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    theme = Column(String(20), default='light')
    use_ai = Column(Boolean, default=True)
    preferred_ai_model = Column(String(20), default='gemini')  # 'gemini', 'openai', or 'rule-based'
    notification_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference for {self.user_id}>"

class ChatHistory(Base):
    """Chat history between users and the assistant"""
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_message = Column(String(1000), nullable=False)
    assistant_response = Column(String(5000), nullable=False)
    ai_model_used = Column(String(20))  # Which AI model generated this response

    # Relationships
    user = relationship("User", back_populates="chats")

    def __repr__(self):
        return f"<ChatHistory {self.id} for user {self.user_id}>"

class Player(Base):
    """Cricket player data"""
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(String(20))  # Batsman, Bowler, All-rounder, Wicketkeeper
    team_id = Column(Integer, ForeignKey('teams.id'))
    batting_avg = Column(Float)
    bowling_avg = Column(Float)
    strike_rate = Column(Float)
    economy = Column(Float)
    recent_form = Column(JSON)  # Store as JSON array
    recent_wickets = Column(JSON)  # Store as JSON array
    fantasy_points_avg = Column(Float)
    ownership = Column(Float)  # Percentage of fantasy teams with this player
    price = Column(Float)  # Fantasy cricket price
    matches_played = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="players")
    match_performances = relationship("PlayerPerformance", back_populates="player")

    def __repr__(self):
        return f"<Player {self.name}>"

class Team(Base):
    """Cricket team data"""
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    country = Column(String(50))
    logo_url = Column(String(200))
    home_ground = Column(String(100))

    # Relationships
    players = relationship("Player", back_populates="team")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")

    def __repr__(self):
        return f"<Team {self.name}>"

class Match(Base):
    """Cricket match data"""
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))
    venue = Column(String(100))
    match_date = Column(DateTime)
    match_type = Column(String(20))  # T20, ODI, Test
    status = Column(String(50))  # Upcoming, Live, Completed
    result = Column(String(200))
    pitch_conditions = Column(String(100))
    weather = Column(String(100))

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    performances = relationship("PlayerPerformance", back_populates="match")

    def __repr__(self):
        return f"<Match {self.home_team.name} vs {self.away_team.name} on {self.match_date}>"

class PlayerPerformance(Base):
    """Player performance in a specific match"""
    __tablename__ = 'player_performances'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    runs_scored = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    overs_bowled = Column(Float, default=0)
    runs_conceded = Column(Integer, default=0)
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    fantasy_points = Column(Float, default=0)

    # Relationships
    player = relationship("Player", back_populates="match_performances")
    match = relationship("Match", back_populates="performances")

    def __repr__(self):
        return f"<Performance by {self.player.name} in match {self.match_id}>"

# Database connection setup
def get_database_url():
    """Get database URL from environment or use SQLite as fallback"""
    # Import here to avoid circular imports
    from config import DATABASE_URL

    db_url = DATABASE_URL
    if not db_url:
        # Use SQLite for development
        db_url = 'sqlite:///cricket_assistant.db'
    return db_url

def setup_database():
    """Set up database connection and create tables"""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# Create a session factory
def get_session():
    """Get a new database session"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()
