import json
import os
import time
from datetime import datetime
import pandas as pd

# Define data directories and files
DATA_DIR = "data"
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")
USER_PREFERENCES_FILE = os.path.join(DATA_DIR, "user_preferences.json")
PLAYERS_DATA_FILE = os.path.join(DATA_DIR, "players_data.json")
MATCH_DATA_FILE = os.path.join(DATA_DIR, "match_data.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def initialize_json_file(filepath, default_data):
    """Initialize a JSON file with default data if it doesn't exist"""
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=2)
    return True

# Initialize data files
initialize_json_file(CHAT_HISTORY_FILE, {"chats": []})
initialize_json_file(USER_PREFERENCES_FILE, {"theme": "light", "use_ai": True, "favorites": []})
initialize_json_file(PLAYERS_DATA_FILE, {"last_updated": "", "players": []})
initialize_json_file(MATCH_DATA_FILE, {"last_updated": "", "matches": []})

def save_chat_history(user_id, user_message, assistant_response):
    """
    Save chat exchange to chat history file
    
    Parameters:
    - user_id: Identifier for the user (can be session ID)
    - user_message: Message from the user
    - assistant_response: Response from the assistant
    """
    try:
        # Load existing chat history
        with open(CHAT_HISTORY_FILE, 'r') as f:
            chat_data = json.load(f)
        
        # Add new chat exchange
        timestamp = datetime.now().isoformat()
        chat_data["chats"].append({
            "user_id": user_id,
            "timestamp": timestamp,
            "user_message": user_message,
            "assistant_response": assistant_response
        })
        
        # Save updated chat history
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(chat_data, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error saving chat history: {str(e)}")
        return False

def get_chat_history(user_id=None, limit=10):
    """
    Retrieve chat history
    
    Parameters:
    - user_id: Optional filter by user ID
    - limit: Number of recent chat exchanges to return
    
    Returns:
    - List of chat exchanges
    """
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            chat_data = json.load(f)
        
        chats = chat_data["chats"]
        
        # Filter by user_id if specified
        if user_id:
            chats = [chat for chat in chats if chat["user_id"] == user_id]
        
        # Return most recent chats based on limit
        return chats[-limit:] if chats else []
    except Exception as e:
        print(f"Error retrieving chat history: {str(e)}")
        return []

def save_user_preference(user_id, preference_name, preference_value):
    """
    Save a user preference
    
    Parameters:
    - user_id: Identifier for the user
    - preference_name: Name of the preference
    - preference_value: Value to save
    """
    try:
        with open(USER_PREFERENCES_FILE, 'r') as f:
            preferences = json.load(f)
        
        # Create user entry if it doesn't exist
        if user_id not in preferences:
            preferences[user_id] = {}
        
        # Update preference
        preferences[user_id][preference_name] = preference_value
        
        with open(USER_PREFERENCES_FILE, 'w') as f:
            json.dump(preferences, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error saving user preference: {str(e)}")
        return False

def get_user_preference(user_id, preference_name, default_value=None):
    """
    Get a user preference
    
    Parameters:
    - user_id: Identifier for the user
    - preference_name: Name of the preference
    - default_value: Default value if preference not found
    
    Returns:
    - Preference value or default
    """
    try:
        with open(USER_PREFERENCES_FILE, 'r') as f:
            preferences = json.load(f)
        
        # Return preference if it exists
        if user_id in preferences and preference_name in preferences[user_id]:
            return preferences[user_id][preference_name]
        
        # Otherwise return default
        return default_value
    except Exception as e:
        print(f"Error retrieving user preference: {str(e)}")
        return default_value

def save_cricket_players(players_data):
    """
    Save cricket player data
    
    Parameters:
    - players_data: List of player data dictionaries
    """
    try:
        player_data_obj = {
            "last_updated": datetime.now().isoformat(),
            "players": players_data
        }
        
        with open(PLAYERS_DATA_FILE, 'w') as f:
            json.dump(player_data_obj, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error saving player data: {str(e)}")
        return False

def get_cricket_players():
    """
    Get cricket player data
    
    Returns:
    - List of player data dictionaries
    """
    try:
        with open(PLAYERS_DATA_FILE, 'r') as f:
            player_data = json.load(f)
            
        return player_data["players"]
    except Exception as e:
        print(f"Error retrieving player data: {str(e)}")
        return []

def save_match_data(matches_data):
    """
    Save cricket match data
    
    Parameters:
    - matches_data: List of match data dictionaries
    """
    try:
        match_data_obj = {
            "last_updated": datetime.now().isoformat(),
            "matches": matches_data
        }
        
        with open(MATCH_DATA_FILE, 'w') as f:
            json.dump(match_data_obj, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error saving match data: {str(e)}")
        return False

def get_match_data():
    """
    Get cricket match data
    
    Returns:
    - List of match data dictionaries
    """
    try:
        with open(MATCH_DATA_FILE, 'r') as f:
            match_data = json.load(f)
            
        return match_data["matches"]
    except Exception as e:
        print(f"Error retrieving match data: {str(e)}")
        return []

def export_chat_history_to_csv(output_file="chat_history_export.csv"):
    """
    Export chat history to CSV file
    
    Parameters:
    - output_file: Path to the CSV output file
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            chat_data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(chat_data["chats"])
        
        # Export to CSV
        df.to_csv(output_file, index=False)
        
        return True
    except Exception as e:
        print(f"Error exporting chat history: {str(e)}")
        return False

def is_data_stale(data_file, max_age_seconds=3600):
    """
    Check if data is stale based on last updated timestamp
    
    Parameters:
    - data_file: Path to the data file
    - max_age_seconds: Maximum age in seconds before data is considered stale
    
    Returns:
    - True if data is stale or file doesn't exist, False otherwise
    """
    try:
        if not os.path.exists(data_file):
            return True
            
        with open(data_file, 'r') as f:
            data = json.load(f)
            
        if "last_updated" not in data:
            return True
            
        last_updated = datetime.fromisoformat(data["last_updated"])
        age = (datetime.now() - last_updated).total_seconds()
        
        return age > max_age_seconds
    except Exception as e:
        print(f"Error checking data staleness: {str(e)}")
        return True  # Assume stale on error