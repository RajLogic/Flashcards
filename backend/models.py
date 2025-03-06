from pydantic import BaseModel
from typing import List

class Flashcard(BaseModel):
    front: str
    back: str
    category: str = "General"
    links: List[int] = []  # List of IDs of related flashcards