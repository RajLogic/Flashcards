from pydantic import BaseModel
from typing import List

class Flashcard(BaseModel):
    front: str
    back: str
    category: str

    class Config:
        json_schema_extra = {  # Changed from schema_extra to json_schema_extra
            "example": {
                "front": "What is Symbolic Reasoning?",
                "back": "Symbolic Reasoning represents data as symbols...",
                "category": "General"
            }
        }

class TextInput(BaseModel):
    text: str

    class Config:
        json_schema_extra = {  # Changed from schema_extra to json_schema_extra
            "example": {
                "text": "There are many kinds of AI, some are described briefly below:\nSymbolic Reasoning represents data as symbols..."
            }
        }