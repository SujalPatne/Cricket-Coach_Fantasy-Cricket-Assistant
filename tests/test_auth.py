"""
Tests for the auth.py module
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import bcrypt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit
class MockSession:
    def __init__(self):
        self.session_state = {}

class MockSt:
    def __init__(self):
        self.session_state = {}
    
    def sidebar(self):
        return self
    
    def markdown(self, text):
        return None
    
    def success(self, text):
        return None
    
    def error(self, text):
        return None
    
    def form(self, key, clear_on_submit=False):
        class MockForm:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                return None
        
        return MockForm()
    
    def text_input(self, label, type=None):
        return ""
    
    def form_submit_button(self, label):
        return False
    
    def tabs(self, labels):
        return [self, self]
    
    def button(self, label):
        return False
    
    def rerun(self):
        return None

# Mock streamlit module
sys.modules['streamlit'] = MagicMock()
sys.modules['streamlit'].session_state = {}

# Import module to test
from auth import (
    initialize_session_state,
    login_user,
    register_user,
    logout_user,
    get_current_user
)

class TestAuth(unittest.TestCase):
    """Test cases for auth.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock user
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.email = "test@example.com"
        self.mock_user.password_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create mock database manager
        self.mock_db = MagicMock()
        self.mock_db.authenticate_user.return_value = self.mock_user
        self.mock_db.get_user_by_username.return_value = None  # User doesn't exist for registration
        self.mock_db.create_user.return_value = self.mock_user
        self.mock_db.get_user_by_id.return_value = self.mock_user
        
        # Mock streamlit session state
        sys.modules['streamlit'].session_state = {}
    
    def test_initialize_session_state(self):
        """Test initialize_session_state function"""
        # Call function
        initialize_session_state()
        
        # Assertions
        self.assertIn('user_id', sys.modules['streamlit'].session_state)
        self.assertIn('authenticated', sys.modules['streamlit'].session_state)
        self.assertIn('username', sys.modules['streamlit'].session_state)
        self.assertIn('db_user_id', sys.modules['streamlit'].session_state)
        
        self.assertFalse(sys.modules['streamlit'].session_state['authenticated'])
        self.assertIsNone(sys.modules['streamlit'].session_state['username'])
        self.assertIsNone(sys.modules['streamlit'].session_state['db_user_id'])
    
    @patch('auth.DatabaseManager')
    def test_login_user_success(self, mock_db_class):
        """Test login_user function with successful login"""
        # Configure mock
        mock_db_class.return_value = self.mock_db
        
        # Initialize session state
        initialize_session_state()
        
        # Call function
        success, message = login_user("testuser", "password")
        
        # Assertions
        self.assertTrue(success)
        self.assertEqual(message, "Login successful!")
        self.assertTrue(sys.modules['streamlit'].session_state['authenticated'])
        self.assertEqual(sys.modules['streamlit'].session_state['username'], "testuser")
        self.assertEqual(sys.modules['streamlit'].session_state['db_user_id'], 1)
        
        # Verify mock was called
        self.mock_db.authenticate_user.assert_called_once_with("testuser", "password")
        self.mock_db.close.assert_called_once()
    
    @patch('auth.DatabaseManager')
    def test_login_user_failure(self, mock_db_class):
        """Test login_user function with failed login"""
        # Configure mock
        self.mock_db.authenticate_user.return_value = None
        mock_db_class.return_value = self.mock_db
        
        # Initialize session state
        initialize_session_state()
        
        # Call function
        success, message = login_user("testuser", "wrongpassword")
        
        # Assertions
        self.assertFalse(success)
        self.assertEqual(message, "Invalid username or password.")
        self.assertFalse(sys.modules['streamlit'].session_state['authenticated'])
        self.assertIsNone(sys.modules['streamlit'].session_state['username'])
        self.assertIsNone(sys.modules['streamlit'].session_state['db_user_id'])
        
        # Verify mock was called
        self.mock_db.authenticate_user.assert_called_once_with("testuser", "wrongpassword")
        self.mock_db.close.assert_called_once()
    
    def test_logout_user(self):
        """Test logout_user function"""
        # Set up session state
        sys.modules['streamlit'].session_state['authenticated'] = True
        sys.modules['streamlit'].session_state['username'] = "testuser"
        sys.modules['streamlit'].session_state['db_user_id'] = 1
        
        # Call function
        logout_user()
        
        # Assertions
        self.assertFalse(sys.modules['streamlit'].session_state['authenticated'])
        self.assertIsNone(sys.modules['streamlit'].session_state['username'])
        self.assertIsNone(sys.modules['streamlit'].session_state['db_user_id'])

if __name__ == '__main__':
    unittest.main()
