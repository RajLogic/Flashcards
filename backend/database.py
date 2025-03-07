import sqlite3
from typing import List
from .models import Flashcard
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../flashstudy.log"),
        logging.StreamHandler()
    ]
)

def init_db():
    logging.info("Initializing database")
    conn = sqlite3.connect("../flashcards.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            front TEXT,
            back TEXT,
            category TEXT
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Database initialized successfully")

def save_flashcards(flashcards: List[Flashcard]):
    logging.info("Saving flashcards to database")
    conn = sqlite3.connect("../flashcards.db")
    cursor = conn.cursor()
    for card in flashcards:
        cursor.execute(
            "INSERT INTO flashcards (front, back, category) VALUES (?, ?, ?)",
            (card.front, card.back, card.category)
        )
    conn.commit()
    conn.close()
    logging.info(f"Saved {len(flashcards)} flashcards to database")

def get_flashcards() -> List[Flashcard]:
    logging.info("Retrieving flashcards from database")
    conn = sqlite3.connect("../flashcards.db")
    cursor = conn.cursor()
    cursor.execute("SELECT front, back, category FROM flashcards")
    rows = cursor.fetchall()
    conn.close()
    flashcards = [Flashcard(front=row[0], back=row[1], category=row[2]) for row in rows]
    logging.info(f"Retrieved {len(flashcards)} flashcards from database")
    return flashcards