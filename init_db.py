from models import Base, setup_database
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database by creating all tables"""
    try:
        logger.info("Initializing database...")
        session = setup_database()
        logger.info("Database initialized successfully")
        session.close()
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_database()
