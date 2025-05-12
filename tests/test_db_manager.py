import unittest
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import DatabaseManager
from models import User, Player, Team, Match, setup_database, Base
from sqlalchemy import create_engine

class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Use in-memory SQLite for testing
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        # Create tables
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)

        # Create a session factory
        from sqlalchemy.orm import sessionmaker
        cls.SessionFactory = sessionmaker(bind=engine)

    def setUp(self):
        """Set up test case"""
        # Create a custom DatabaseManager that uses our test session
        self.db = DatabaseManager()
        # Replace the session with our test session
        self.db.session.close()
        self.db.session = self.SessionFactory()

    def tearDown(self):
        """Clean up after test case"""
        self.db.close()

    def test_create_user(self):
        """Test creating a user"""
        user = self.db.create_user("testuser", "test@example.com", "password123")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertIsNotNone(user.password_hash)

    def test_authenticate_user(self):
        """Test authenticating a user"""
        # Create a user first
        self.db.create_user("authuser", "auth@example.com", "password123")

        # Test authentication
        user = self.db.authenticate_user("authuser", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "authuser")

        # Test wrong password
        user = self.db.authenticate_user("authuser", "wrongpassword")
        self.assertIsNone(user)

        # Test non-existent user
        user = self.db.authenticate_user("nonexistent", "password123")
        self.assertIsNone(user)

    def test_save_player(self):
        """Test saving a player"""
        player_data = {
            "name": "Test Player",
            "role": "Batsman",
            "team": "Test Team",
            "batting_avg": 45.5,
            "strike_rate": 85.2,
            "recent_form": [34, 67, 12, 89, 45],
            "fantasy_points_avg": 75.3,
            "ownership": 45.6,
            "price": 9.5,
            "matches_played": 120
        }

        player = self.db.save_player(player_data)

        self.assertIsNotNone(player)
        self.assertEqual(player.name, "Test Player")
        self.assertEqual(player.role, "Batsman")
        self.assertEqual(player.team.name, "Test Team")
        self.assertEqual(player.batting_avg, 45.5)
        self.assertEqual(player.fantasy_points_avg, 75.3)

    def test_get_player_by_name(self):
        """Test getting a player by name"""
        # Create a player first
        player_data = {
            "name": "Get Player Test",
            "role": "Bowler",
            "team": "Test Team",
            "bowling_avg": 22.5,
            "economy": 4.5,
            "recent_wickets": [2, 3, 1, 4, 2],
            "fantasy_points_avg": 65.3,
            "price": 8.5
        }

        self.db.save_player(player_data)

        # Test getting the player
        player = self.db.get_player_by_name("Get Player Test")
        self.assertIsNotNone(player)
        self.assertEqual(player.name, "Get Player Test")
        self.assertEqual(player.role, "Bowler")

        # Test getting non-existent player
        player = self.db.get_player_by_name("Non-existent Player")
        self.assertIsNone(player)

    def test_save_chat(self):
        """Test saving a chat"""
        # Create a user first
        user = self.db.create_user("chatuser", "chat@example.com", "password123")

        # Save a chat
        chat = self.db.save_chat(
            user.id,
            "Test query",
            "Test response",
            "gemini"
        )

        self.assertIsNotNone(chat)
        self.assertEqual(chat.user_id, user.id)
        self.assertEqual(chat.user_message, "Test query")
        self.assertEqual(chat.assistant_response, "Test response")
        self.assertEqual(chat.ai_model_used, "gemini")

    def test_get_user_chats(self):
        """Test getting user chats"""
        # Create a user first
        user = self.db.create_user("chathistoryuser", "chathistory@example.com", "password123")

        # Save multiple chats
        self.db.save_chat(user.id, "Query 1", "Response 1", "gemini")
        self.db.save_chat(user.id, "Query 2", "Response 2", "openai")
        self.db.save_chat(user.id, "Query 3", "Response 3", "rule-based")

        # Get chats
        chats = self.db.get_user_chats(user.id)

        self.assertEqual(len(chats), 3)
        self.assertEqual(chats[0].user_message, "Query 3")  # Most recent first
        self.assertEqual(chats[1].user_message, "Query 2")
        self.assertEqual(chats[2].user_message, "Query 1")

    def test_save_match(self):
        """Test saving a match"""
        match_data = {
            "home_team": "Home Team",
            "away_team": "Away Team",
            "venue": "Test Stadium",
            "match_date": datetime.utcnow(),
            "match_type": "T20",
            "status": "Upcoming",
            "pitch_conditions": "Batting friendly"
        }

        match = self.db.save_match(match_data)

        self.assertIsNotNone(match)
        self.assertEqual(match.home_team.name, "Home Team")
        self.assertEqual(match.away_team.name, "Away Team")
        self.assertEqual(match.venue, "Test Stadium")
        self.assertEqual(match.match_type, "T20")
        self.assertEqual(match.status, "Upcoming")

    def test_get_upcoming_matches(self):
        """Test getting upcoming matches"""
        # Save multiple matches
        self.db.save_match({
            "home_team": "Team A",
            "away_team": "Team B",
            "venue": "Stadium A",
            "match_date": datetime.utcnow(),
            "match_type": "T20",
            "status": "Upcoming"
        })

        self.db.save_match({
            "home_team": "Team C",
            "away_team": "Team D",
            "venue": "Stadium B",
            "match_date": datetime.utcnow(),
            "match_type": "ODI",
            "status": "Upcoming"
        })

        self.db.save_match({
            "home_team": "Team E",
            "away_team": "Team F",
            "venue": "Stadium C",
            "match_date": datetime.utcnow(),
            "match_type": "Test",
            "status": "Live"  # Not upcoming
        })

        # Get upcoming matches
        matches = self.db.get_upcoming_matches()

        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].status, "Upcoming")
        self.assertEqual(matches[1].status, "Upcoming")

if __name__ == '__main__':
    unittest.main()
