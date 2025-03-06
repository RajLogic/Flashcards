import sqlite3
import json

def init_db():
    conn = sqlite3.connect("flashcards.db")
    c = conn.cursor()
    
    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, front TEXT, back TEXT, category TEXT, interval REAL, ease REAL)''')
    
    # Check if the 'links' column exists, and add it if not
    c.execute("PRAGMA table_info(flashcards)")
    columns = [col[1] for col in c.fetchall()]
    if 'links' not in columns:
        c.execute('ALTER TABLE flashcards ADD COLUMN links TEXT DEFAULT "[]"')
    
    conn.commit()
    conn.close()

def save_flashcards(flashcards):
    conn = sqlite3.connect("flashcards.db")
    c = conn.cursor()
    # First, insert all flashcards to get their IDs
    for card in flashcards:
        c.execute("INSERT INTO flashcards (front, back, category, interval, ease, links) VALUES (?, ?, ?, ?, ?, ?)",
                  (card.front, card.back, card.category, 1.0, 2.5, json.dumps([])))  # Initial empty links
    conn.commit()
    
    # Retrieve the IDs of all flashcards
    c.execute("SELECT id, front FROM flashcards")
    id_map = {row[1]: row[0] for row in c.fetchall()}
    
    # Update links with actual IDs
    for card in flashcards:
        if card.links:
            card.links = [id_map.get(link, id_map[card.front]) for link in card.links if link in id_map]
            c.execute("UPDATE flashcards SET links = ? WHERE id = ?", (json.dumps(card.links), id_map[card.front]))
    conn.commit()
    conn.close()

def get_flashcards():
    conn = sqlite3.connect("flashcards.db")
    c = conn.cursor()
    c.execute("SELECT id, front, back, category, links FROM flashcards")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "front": r[1], "back": r[2], "category": r[3], "links": json.loads(r[4]) if r[4] else []} for r in rows]