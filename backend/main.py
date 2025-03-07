from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from .models import Flashcard, TextInput
from .flashcards import generate_flashcards
from .database import init_db, save_flashcards, get_flashcards
from .parsing import parse_pdf, parse_docx, parse_image
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../flashstudy.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI()

# Enable CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

@app.on_event("startup")
async def startup_event():
    logging.info("Application starting up")
    init_db()

@app.post("/upload/", response_model=List[Flashcard])
async def upload_file(file: UploadFile = File(...)):
    logging.info(f"Received upload request for file: {file.filename}")
    if file.filename.endswith(".pdf"):
        content = parse_pdf(file.file)
    elif file.filename.endswith(".docx"):
        content = parse_docx(file.file)
    elif file.filename.endswith((".jpg", ".png")):
        content = parse_image(file.file)
    else:
        content = await file.read()
        content = content.decode("utf-8")
    
    logging.debug(f"Processed content: {content[:500]}...")
    flashcards = generate_flashcards(content)
    save_flashcards(flashcards)
    logging.info(f"Returning {len(flashcards)} flashcards: {json.dumps([flashcard.dict() for flashcard in flashcards], ensure_ascii=False)[:500]}...")
    return JSONResponse(content=[flashcard.dict() for flashcard in flashcards])

@app.post("/text/", response_model=List[Flashcard])
async def process_text(request: Request, input: TextInput):
    logging.info(f"Received text input request with method: {request.method}")
    logging.debug(f"Processing text input: {input.text[:500]}...")
    flashcards = generate_flashcards(input.text)
    save_flashcards(flashcards)
    logging.info(f"Returning {len(flashcards)} flashcards: {json.dumps([flashcard.dict() for flashcard in flashcards], ensure_ascii=False)[:500]}...")
    return JSONResponse(content=[flashcard.dict() for flashcard in flashcards])

@app.get("/flashcards/", response_model=List[Flashcard])
async def fetch_flashcards():
    logging.info("Received request to fetch flashcards")
    flashcards = get_flashcards()
    logging.info(f"Returning {len(flashcards)} flashcards from database")
    return JSONResponse(content=[flashcard.dict() for flashcard in flashcards])