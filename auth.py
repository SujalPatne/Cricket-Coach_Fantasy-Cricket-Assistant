import streamlit as st
import bcrypt
import uuid
from typing import Optional, Dict, Any, Tuple
import logging
from db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables for authentication"""
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = str(uuid.uuid4())
    
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    
    if 'db_user_id' not in st.session_state:
        st.session_state['db_user_id'] = None

def login_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate a user with username and password
    
    Parameters:
    - username: User's username
    - password: User's password
    
    Returns:
    - Tuple of (success, message)
    """
    try:
        db = DatabaseManager()
        user = db.authenticate_user(username, password)
        
        if user:
            # Set session state
            st.session_state['authenticated'] = True
            st.session_state['username'] = user.username
            st.session_state['db_user_id'] = user.id
            
            logger.info(f"User {username} logged in successfully")
            return True, "Login successful!"
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return False, "Invalid username or password."
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return False, f"An error occurred during login: {str(e)}"
    finally:
        db.close()

def register_user(username: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
    """
    Register a new user
    
    Parameters:
    - username: User's username
    - email: User's email
    - password: User's password
    - confirm_password: Password confirmation
    
    Returns:
    - Tuple of (success, message)
    """
    # Validate inputs
    if not username or not email or not password:
        return False, "All fields are required."
    
    if password != confirm_password:
        return False, "Passwords do not match."
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    try:
        db = DatabaseManager()
        
        # Check if username exists
        if db.get_user_by_username(username):
            return False, "Username already exists."
        
        # Create user
        user = db.create_user(username, email, password)
        
        # Set session state
        st.session_state['authenticated'] = True
        st.session_state['username'] = user.username
        st.session_state['db_user_id'] = user.id
        
        logger.info(f"User {username} registered successfully")
        return True, "Registration successful!"
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return False, f"An error occurred during registration: {str(e)}"
    finally:
        db.close()

def logout_user():
    """Log out the current user"""
    # Keep the session ID but reset authentication
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    st.session_state['db_user_id'] = None
    
    logger.info("User logged out")

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user
    
    Returns:
    - User information dictionary or None if not authenticated
    """
    if not st.session_state.get('authenticated', False):
        return None
    
    try:
        db = DatabaseManager()
        user = db.get_user_by_id(st.session_state['db_user_id'])
        
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
        return None
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None
    finally:
        db.close()

def render_login_ui():
    """Render the login/registration UI"""
    st.sidebar.markdown("## 👤 User Account")
    
    if st.session_state.get('authenticated', False):
        # Show logged in user info
        st.sidebar.success(f"Logged in as {st.session_state['username']}")
        
        if st.sidebar.button("Log Out"):
            logout_user()
            st.rerun()
    else:
        # Show login/register tabs
        tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit = st.form_submit_button("Register")
                
                if submit:
                    success, message = register_user(new_username, email, new_password, confirm_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
