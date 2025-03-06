import pytesseract
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import io
import re
import logging
from fastapi import UploadFile

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flashstudy.log"),
        logging.StreamHandler()  # Output to console
    ]
)

# Define common placeholder patterns
PLACEHOLDER_PATTERNS = [
    r'^RMIT Classification:.*$',  # Matches "RMIT Classification: Trusted"
    r'^\s*Page\s+\d+\s*$',       # Matches "Page 1", "Page 2", etc.
    r'^\s*Confidential\s*$',     # Matches "Confidential"
    r'^\s*Draft\s*$',            # Matches "Draft"
    r'^\s*[A-Za-z]+\s+Classification:.*$',  # Generic classification pattern
    r'^\s*Dr\s+[A-Za-z]+\s+[A-Za-z]+$',     # Matches "Dr Hayham Fayek"
    r'^\s*What\'s next\.\.\.$',             # Matches "What's next..."
    r'^\s*\d+\s*$',                        # Matches standalone numbers like "14"
]

def is_placeholder(line: str) -> bool:
    """Check if a line is a placeholder based on predefined patterns."""
    line = line.strip()
    is_placeholder = any(re.match(pattern, line, re.IGNORECASE) for pattern in PLACEHOLDER_PATTERNS)
    logging.debug(f"Checking line '{line}' for placeholder: {is_placeholder}")
    return is_placeholder

async def process_document(file: UploadFile):
    logging.info(f"Processing file: {file.filename}")
    file_bytes = await file.read()
    file_type = file.filename.split(".")[-1].lower()

    if file_type == "pdf":
        logging.info("Parsing PDF file")
        pdf = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page_num, page in enumerate(pdf.pages, 1):
            logging.debug(f"Processing page {page_num}")
            page_text = page.extract_text()
            logging.debug(f"Raw page text: {page_text[:200]}...")  # Log first 200 chars
            # Remove XML-like tags and split into lines
            page_text = re.sub(r'</?PAGE\d+>|</?CONTENT_FROM_OCR>', '', page_text)
            lines = page_text.split("\n")
            filtered_text = [line for line in lines if not is_placeholder(line)]
            logging.debug(f"Filtered lines: {filtered_text}")
            text += "\n".join(filtered_text) + "\n"
        result = text.strip()
        logging.info(f"Processed PDF text: {result[:200]}...")
        return result
    elif file_type == "docx":
        logging.info("Parsing DOCX file")
        doc = Document(io.BytesIO(file_bytes))
        text = ""
        for para in doc.paragraphs:
            line = para.text.strip()
            if not is_placeholder(line):
                text += line + "\n"
        result = text.strip()
        logging.info(f"Processed DOCX text: {result[:200]}...")
        return result
    elif file_type in ["jpg", "png"]:
        logging.info("Parsing image file with OCR")
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        logging.debug(f"Raw OCR text: {text[:200]}...")
        # Remove XML-like tags and split into lines
        text = re.sub(r'</?PAGE\d+>|</?CONTENT_FROM_OCR>', '', text)
        lines = text.split("\n")
        filtered_text = [line for line in lines if not is_placeholder(line)]
        result = "\n".join(filtered_text).strip()
        logging.info(f"Processed image text: {result[:200]}...")
        return result
    else:
        logging.error(f"Unsupported file type: {file_type}")
        raise ValueError("Unsupported file type")