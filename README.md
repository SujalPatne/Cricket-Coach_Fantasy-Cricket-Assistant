# Fantasy Cricket Assistant

A conversational AI chatbot assistant designed to help cricket fans make informed decisions for Fantasy Cricket through natural language interactions.

## Features

- **Interactive Chat Interface**: Natural language conversations about fantasy cricket with detailed loading indicators
- **Player Recommendations**: Get player suggestions based on form, match conditions, and historical data
- **Data Visualization**: View player performance charts and team comparisons
- **Multiple AI Models**: Choose between Gemini, OpenAI, or rule-based responses
- **User Authentication**: Create an account to save your chat history and preferences
- **Educational Content**: Learn about fantasy cricket rules and scoring systems
- **Intelligent Cricket Data**: Smart combination of historical (Cricsheet) and real-time (Cricbuzz) data with efficient caching
- **Multi-page Interface**: Dedicated pages for matches and player analysis
- **Quick Actions**: One-click buttons for common fantasy cricket queries
- **Live Match Updates**: View live cricket matches with scores and status updates
- **Comprehensive Error Handling**: Graceful degradation with informative error messages

## Tech Stack

- **Frontend**: Streamlit for the web interface with streamlit-chat for message display
- **Database**: SQLAlchemy with SQLite/PostgreSQL for user data and chat history
- **AI Models**: Google Gemini (primary) and OpenAI integration with fallback options
- **Data Visualization**: Built-in charts for player performance and team comparisons
- **Web Scraping**: Integration with Cricbuzz API via RapidAPI for real-time data
- **Data Processing**: Cricsheet data parser for historical cricket statistics
- **Testing**: Pytest-based testing infrastructure with run_tests.py
- **Logging**: Comprehensive error tracking and monitoring system

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fantasy-cricket-assistant.git
   cd fantasy-cricket-assistant
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (or create a .env file):
   ```
   export GEMINI_API_KEY=your_gemini_api_key
   export OPENAI_API_KEY=your_openai_api_key  # Optional
   export RAPIDAPI_KEY=your_rapidapi_key  # For Cricbuzz API access
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

## Deployment

The application is designed to be deployed on Streamlit Cloud:

1. Push your code to a GitHub repository
2. Connect your repository to Streamlit Cloud
3. Set the main file as `app.py`
4. Configure your secrets in the Streamlit Cloud dashboard
5. Deploy the application

Note: The repository includes a minimal `streamlit_app.py` for initial deployment testing, but the full-featured `app.py` should be used for both local development and production deployment.

## Usage

1. **Chat Interface**: Ask questions about players, teams, or fantasy cricket strategy
2. **Quick Actions**: Use the buttons for common queries like "Best Batsmen" or "Captain Picks"
3. **Visualizations**: Request player statistics or team comparisons
4. **User Account**: Create an account to save your chat history
5. **AI Model Selection**: Choose your preferred AI model from the sidebar
6. **Matches Page**: View live, upcoming, and recent cricket matches with detailed information
7. **Players Page**: Search for players, analyze their performance, and get recommendations

### Example Queries

Try asking the assistant questions like:
- "What are Virat Kohli's batting statistics?"
- "Show me Jasprit Bumrah's bowling performance"
- "Who should I pick as captain for today's match?"
- "Compare Rohit Sharma and Kane Williamson"
- "Who's a good differential pick today?"
- "Should I pick Player A or Player B for today's match?"
- "Show me upcoming IPL matches"
- "What's the pitch report for Mumbai?"

### UI Features

- **Informative Loading Indicators**: The system shows detailed loading messages above the text input, indicating:
  - When it's fetching player statistics
  - Whether it's using cached data or downloading fresh data
  - Which data sources are being checked (Cricsheet, Cricbuzz)
  - Real-time updates on the data retrieval process

- **Formatted Player Statistics**: Player statistics are presented in a clean, organized format with:
  - Career overview
  - Batting/bowling statistics
  - Recent form and fantasy points
  - Data source and last updated timestamp

## Data Sources and Caching

The Fantasy Cricket Assistant uses multiple data sources to provide comprehensive cricket information:

### Cricsheet Data (Historical)
- **Purpose**: Provides detailed historical match and player data
- **Features**:
  - Selective downloading of only required data
  - Efficient caching system with configurable expiration times
  - Detailed player statistics extraction from ball-by-ball data
  - Cached in `cricsheet_data/cache` directory

### Cricbuzz API via RapidAPI (Real-time)
- **Purpose**: Provides real-time match scores and current player form
- **Features**:
  - Live match scores and status updates
  - Current player form and recent performances
  - Team and venue information

### Intelligent Data Integration
- **Smart Selection**: System intelligently chooses between data sources based on query type
- **Data Merging**: Combines historical data with real-time updates
- **Cache Management**:
  - Player data cached with timestamps
  - Automatic refresh of outdated cache
  - Transparent loading indicators showing data source and status

### Fallback System
- Reliable fallback data for when external APIs are unavailable
- Graceful degradation with informative error messages

## Development

### Running Tests

```
python run_tests.py
```

### Testing Player Statistics

You can test the player statistics functionality using the included test script:

```
python test_player_stats.py
```

This script tests:
1. Player name extraction from natural language queries
2. Player statistics retrieval from multiple data sources
3. Formatted output generation

### Project Structure

- `app.py`: Main Streamlit application with full features
- `streamlit_app.py`: Minimal version for deployment testing
- `models.py`: SQLAlchemy database models
- `db_manager.py`: Database operations
- `ai_manager.py`: AI model management
- `gemini_assistant.py`: Google Gemini integration
- `openai_assistant.py`: OpenAI integration
- `assistant.py`: Rule-based fallback system
- `visualizations.py`: Data visualization components
- `auth.py`: User authentication
- `logger.py`: Logging system
- `cricket_data_adapter.py`: Cricket data processing with multiple sources
- `cricsheet_parser.py`: Parser for Cricsheet data
- `cricbuzz_client.py`: Client for Cricbuzz API
- `config.py`: Configuration settings
- `fantasy_rules.py`: Fantasy cricket rules and scoring systems
- `fantasy_recommendations.py`: Fantasy cricket recommendation algorithms
- `pages/`: Multi-page Streamlit application
  - `1_🏏_Matches.py`: Matches page
  - `2_👤_Players.py`: Players page
- `tests/`: Unit and integration tests
- `test_player_stats.py`: Test script for player statistics functionality
- `.gitignore`: Configuration for excluding sensitive and temporary files
- `.replit`: Configuration for Replit environment

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Cricket data sources:
  - [Cricsheet](https://cricsheet.org/) - For comprehensive historical ball-by-ball data
  - [Cricbuzz](https://www.cricbuzz.com/) - For real-time match and player information via RapidAPI
  - [ESPNCricinfo](https://www.espncricinfo.com/) - For reference data
- Fantasy cricket platforms for scoring rules reference
