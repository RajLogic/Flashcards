import sqlite3
import logging
from typing import List
from .models import Flashcard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("database.log"),
        logging.StreamHandler()
    ]
)

class Database:
    """A class to manage the SQLite database for FlashStudy."""

    _instance = None

    def __new__(cls, db_path: str = "flashstudy.db"):
        """Ensure a singleton instance of the database."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance._create_tables()
        return cls._instance

    def _connect(self):
        """Create a connection to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {str(e)}")
            raise

    def _create_tables(self):
        """Create the necessary tables if they don't exist."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS flashcards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        front TEXT NOT NULL,
                        back TEXT NOT NULL,
                        category TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logging.info("Database tables created successfully")
        except sqlite3.Error as e:
            logging.error(f"Error creating tables: {str(e)}")
            raise

    def insert_flashcard(self, flashcard: Flashcard) -> int:
        """Insert a flashcard into the database and return its ID."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO flashcards (front, back, category)
                    VALUES (?, ?, ?)
                ''', (flashcard.front, flashcard.back, flashcard.category))
                conn.commit()
                flashcard_id = cursor.lastrowid
                logging.info(f"Inserted flashcard with ID {flashcard_id}: {flashcard.front}")
                return flashcard_id
        except sqlite3.Error as e:
            logging.error(f"Error inserting flashcard: {str(e)}")
            raise

    def insert_flashcards(self, flashcards: List[Flashcard]) -> List[int]:
        """Insert multiple flashcards into the database and return their IDs."""
        try:
            flashcard_ids = []
            with self._connect() as conn:
                cursor = conn.cursor()
                for flashcard in flashcards:
                    cursor.execute('''
                        INSERT INTO flashcards (front, back, category)
                        VALUES (?, ?, ?)
                    ''', (flashcard.front, flashcard.back, flashcard.category))
                    flashcard_ids.append(cursor.lastrowid)
                conn.commit()
                logging.info(f"Inserted {len(flashcard_ids)} flashcards")
                return flashcard_ids
        except sqlite3.Error as e:
            logging.error(f"Error inserting flashcards: {str(e)}")
            raise

    def get_all_flashcards(self) -> List[Flashcard]:
        """Retrieve all flashcards from the database."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT front, back, category FROM flashcards')
                rows = cursor.fetchall()
                flashcards = [Flashcard(front=row[0], back=row[1], category=row[2]) for row in rows]
                logging.info(f"Retrieved {len(flashcards)} flashcards")
                return flashcards
        except sqlite3.Error as e:
            logging.error(f"Error retrieving flashcards: {str(e)}")
            raise

    def get_flashcards_by_category(self, category: str) -> List[Flashcard]:
        """Retrieve flashcards by category."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT front, back, category FROM flashcards WHERE category = ?', (category,))
                rows = cursor.fetchall()
                flashcards = [Flashcard(front=row[0], back=row[1], category=row[2]) for row in rows]
                logging.info(f"Retrieved {len(flashcards)} flashcards for category '{category}'")
                return flashcards
        except sqlite3.Error as e:
            logging.error(f"Error retrieving flashcards by category: {str(e)}")
            raise

    def delete_flashcard(self, flashcard_id: int) -> bool:
        """Delete a flashcard by ID."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM flashcards WHERE id = ?', (flashcard_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.warning(f"No flashcard found with ID {flashcard_id}")
                    return False
                logging.info(f"Deleted flashcard with ID {flashcard_id}")
                return True
        except sqlite3.Error as e:
            logging.error(f"Error deleting flashcard: {str(e)}")
            raise

    def clear_flashcards(self) -> None:
        """Clear all flashcards from the database."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM flashcards')
                conn.commit()
                logging.info("Cleared all flashcards from the database")
        except sqlite3.Error as e:
            logging.error(f"Error clearing flashcards: {str(e)}")
            raise

# Global functions to match expected imports
def init_db(db_path: str = "flashstudy.db") -> None:
    """Initialize the database (create tables if not exist)."""
    global db
    db = Database(db_path)
    logging.info("Database initialized")

def save_flashcards(flashcards: List[Flashcard]) -> List[int]:
    """Save a list of flashcards to the database."""
    return db.insert_flashcards(flashcards)

def get_flashcards(category: str = None) -> List[Flashcard]:
    """Retrieve flashcards from the database, optionally filtered by category."""
    if category:
        return db.get_flashcards_by_category(category)
    return db.get_all_flashcards()

# Initialize the database instance
db = None

if __name__ == "__main__":
    # Test the database functionality
    init_db()
    flashcards = [
        Flashcard(front="What is Deep learning?", back="Deep learning, using neural networks, has revolutionized image recognition, achieving accuracies above 95% in some cases.", category="Artificial Intelligence"),
        Flashcard(front="What is Machine learning?", back="Machine learning, a subset of AI, allows systems to learn from data and improve over time.", category="Artificial Intelligence"),
    ]
    flashcard_ids = save_flashcards(flashcards)
    print(f"Inserted flashcards with IDs: {flashcard_ids}")
    all_flashcards = get_flashcards()
    print(f"All flashcards: {[vars(fc) for fc in all_flashcards]}")
    ai_flashcards = get_flashcards("Artificial Intelligence")
    print(f"AI flashcards: {[vars(fc) for fc in ai_flashcards]}")
    if flashcard_ids:
        db.delete_flashcard(flashcard_ids[0])
        print(f"Deleted flashcard with ID {flashcard_ids[0]}")
    db.clear_flashcards()
    print("Cleared all flashcards")