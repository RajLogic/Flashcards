import PyPDF2
from docx import Document
import pytesseract
from PIL import Image
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../flashstudy.log"),
        logging.StreamHandler()
    ]
)

def parse_pdf(file) -> str:
    logging.info("Parsing PDF file")
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    logging.debug(f"Extracted text from PDF: {text[:500]}...")
    return text

def parse_docx(file) -> str:
    logging.info("Parsing DOCX file")
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    logging.debug(f"Extracted text from DOCX: {text[:500]}...")
    return text

def parse_image(file) -> str:
    logging.info("Parsing image file")
    image = Image.open(file)
    text = pytesseract.image_to_string(image)
    logging.debug(f"Extracted text from image: {text[:500]}...")
    return text