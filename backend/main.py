from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .parsing import process_document
from .flashcards import generate_flashcards
from .database import save_flashcards, get_flashcards, init_db
import logging

# Logging is already configured in parsing.py, so no need to repeat

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logging.info("Application starting up")
    init_db()
    logging.info("Database initialized")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    logging.info(f"Received upload request for file: {file.filename}")
    content = await process_document(file)
    logging.debug(f"Processed content: {content[:200]}...")
    flashcards = generate_flashcards(content)
    logging.info(f"Generated {len(flashcards)} flashcards")
    save_flashcards(flashcards)
    logging.info("Flashcards saved to database")
    return {"flashcards": flashcards}

@app.post("/text/")
async def process_text(request: dict):  # Accept JSON body
    logging.info("Received text input request")
    text = request.get("text", "").strip()
    if not text:
        logging.warning("Empty or invalid text input")
        return {"flashcards": []}
    logging.debug(f"Processing text input: {text[:200]}...")
    flashcards = generate_flashcards(text)
    logging.info(f"Generated {len(flashcards)} flashcards from text")
    save_flashcards(flashcards)
    logging.info("Flashcards saved to database")
    return {"flashcards": flashcards}

@app.get("/flashcards/")
async def list_flashcards():
    logging.info("Fetching all flashcards")
    return get_flashcards()