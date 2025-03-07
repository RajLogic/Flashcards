from typing import List, Dict
from .models import Flashcard
import re
import logging
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../flashstudy.log"),
        logging.StreamHandler()
    ]
)

# Load pre-trained model and vectorizer
try:
    model = joblib.load("../ml/ml_model.joblib")
    vectorizer = joblib.load("../ml/tfidf_vectorizer.joblib")
    logging.info("Loaded ML model and vectorizer successfully")
except FileNotFoundError:
    logging.error("ML model or vectorizer not found. Falling back to default logic.")
    model = None
    vectorizer = None

def is_important_line(line: str) -> bool:
    """Determine if a line contains important information using ML or fallback logic."""
    line = line.strip()
    if not line:
        logging.debug(f"Line is empty, returning False")
        return False

    if model and vectorizer:
        line_tfidf = vectorizer.transform([line])
        prediction = model.predict(line_tfidf)[0]
        logging.debug(f"ML prediction for '{line}': {prediction}")
        return bool(prediction)
    else:
        is_important = bool(
            re.search(r'\b(is a|refers to|means|defined as|represents|emulate|ability|based on|used to)\b', line.lower()) or
            re.match(r'^(what|how|define|explain|describe)', line.lower()) or
            any(keyword in line.lower() for keyword in ["ai", "symbolic", "expert", "machine", "deep", "learning", "reasoning", "neural", "algorithms"])
        )
        logging.debug(f"Fallback rule-based check for '{line}': {is_important}")
        return is_important

def extract_key_terms(text: str) -> List[str]:
    """Extract key terms from a line of text, prioritizing capitalized phrases."""
    text = text.strip()
    terms = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
    if not terms:
        terms = [term for term in re.findall(r'\w{3,}', text.lower()) if len(term) > 2]
    logging.debug(f"Extracted key terms from '{text}': {terms}")
    return terms

def detect_category(lines: List[str], term: str) -> str:
    """Detect the category from preceding headings or context based on the term."""
    logging.debug(f"Detecting category for term: {term}")
    term = term.lower().strip()
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith("#"):
            return line.strip("#").strip() or "General"
        if term in line.lower():
            for j in range(i - 1, -1, -1):
                prev_line = lines[j].strip()
                if prev_line.startswith("#"):
                    return prev_line.strip("#").strip() or "General"
    return "General"

def generate_questions_and_answers(content: str) -> Dict[str, List[str]]:
    """Generate questions and associate answers based on context."""
    lines = content.split("\n")
    questions_answers = {}
    current_term = None
    answer_lines = []

    logging.debug(f"Processing {len(lines)} lines of content")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            logging.debug(f"Skipping empty line at index {i}")
            continue

        if is_important_line(line):
            logging.debug(f"Line '{line}' identified as important")
            terms = extract_key_terms(line)
            if not terms:
                logging.debug(f"No key terms found in line: '{line}'")
                continue
            for term in terms:
                if re.search(rf'\b{re.escape(term)}\b', line, re.IGNORECASE):
                    if current_term and answer_lines:
                        questions_answers[f"What is {current_term}?"] = answer_lines[:]
                        logging.debug(f"Added question: What is {current_term}? with answer: {' '.join(answer_lines)}")
                        answer_lines = []
                    current_term = term
                answer_lines.append(line)
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].strip()
                if is_important_line(next_line) and not next_line.startswith("-"):
                    logging.debug(f"Stopping look-ahead at line '{next_line}' as it's important")
                    break
                if next_line and not next_line.startswith("#"):
                    answer_lines.append(next_line)
                    logging.debug(f"Added to answer: '{next_line}'")
            if current_term and answer_lines:
                questions_answers[f"What is {current_term}?"] = answer_lines[:]
                logging.debug(f"Added question: What is {current_term}? with answer: {' '.join(answer_lines)}")
                answer_lines = []
        elif line.startswith("-") and is_important_line(line):
            subtopic = line.strip("-").strip()
            terms = extract_key_terms(subtopic)
            if terms:
                current_term = terms[0]
                answer_lines = [subtopic]
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if is_important_line(next_line) and not next_line.startswith("-"):
                        break
                    if next_line and not next_line.startswith("#"):
                        answer_lines.append(next_line)
                if current_term and answer_lines:
                    questions_answers[f"How does {current_term} work?"] = answer_lines[:]
                    logging.debug(f"Added question: How does {current_term} work? with answer: {' '.join(answer_lines)}")
                    answer_lines = []

    if current_term and answer_lines:
        questions_answers[f"What is {current_term}?"] = answer_lines[:]
        logging.debug(f"Added final question: What is {current_term}? with answer: {' '.join(answer_lines)}")

    return questions_answers

def generate_flashcards(content: str) -> List[Flashcard]:
    logging.info("Starting flashcard generation process")
    logging.debug(f"Input content: {content[:500]}...")
    flashcards = []
    term_to_front = {}

    logging.info("Generating questions and answers from content")
    questions_answers = generate_questions_and_answers(content)
    logging.debug(f"Generated {len(questions_answers)} question-answer pairs")

    for question, answer_lines in questions_answers.items():
        if question not in term_to_front:
            term = question.split("What is ")[1].split("?")[0] if "What is" in question else question.split("How does ")[1].split("?")[0]
            category = detect_category(content.split("\n"), term)
            answer = " ".join(answer_lines).strip()
            answer_sentences = re.split(r'(?<=[.!?])\s+', answer)
            clean_answer = " ".join(answer_sentences[:3]) if answer_sentences else "No specific definition available."
            card = Flashcard(front=question, back=clean_answer, category=category)
            flashcards.append(card)
            term_to_front[question] = question
            logging.debug(f"Added flashcard: {card.front} -> {card.back} [Category: {card.category}]")

    if len(flashcards) > 20:
        flashcards = flashcards[:20]
        logging.info("Capped flashcards at 20")

    if not flashcards:
        logging.warning(f"No flashcards generated. Content processed: {content[:500]}... Consider adding more descriptive text or checking input.")
    else:
        logging.info(f"Successfully generated {len(flashcards)} flashcards")
        for i, card in enumerate(flashcards):
            logging.debug(f"Flashcard {i+1}: {card.front} -> {card.back} [Category: {card.category}]")
    return flashcards