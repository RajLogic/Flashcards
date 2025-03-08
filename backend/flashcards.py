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
        logging.FileHandler("flashstudy.log"),
        logging.StreamHandler()
    ]
)

# Load pre-trained model and vectorizer
try:
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "..", "ml", "ml_model.joblib")
    vectorizer_path = os.path.join(script_dir, "..", "ml", "tfidf_vectorizer.joblib")
    logging.info(f"Attempting to load model from: {model_path}")
    logging.info(f"Attempting to load vectorizer from: {vectorizer_path}")
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    logging.info("Loaded ML model and vectorizer successfully")
except FileNotFoundError as e:
    logging.error(f"ML model or vectorizer not found at {model_path} or {vectorizer_path}. Falling back to default logic. Error: {str(e)}")
    model = None
    vectorizer = None

def is_important_line(line: str, lines: List[str], line_index: int) -> bool:
    """Determine if a line contains a key point to be made."""
    line = line.strip()
    if not line:
        logging.debug(f"Line is empty, returning False")
        return False

    score = 0

    # Positive indicators
    if re.search(r'\b(is a|refers to|means|defined as|represents|emulate|ability|based on|used to|coined|introduced|recognized|focus on)\b', line.lower()):
        score += 6
        logging.debug(f"Line '{line}' contains definition keywords, score += 6")
    if re.search(r'\b(difference|contrast|compare|unlike|whereas|instead)\b', line.lower()):
        score += 5
        logging.debug(f"Line '{line}' contains comparison keywords, score += 5")
    if any(keyword in line.lower() for keyword in ["artificial intelligence", "machine learning", "deep learning", "symbolic reasoning", "neural networks"]):
        score += 5
        logging.debug(f"Line '{line}' contains key domain terms, score += 5")
    if re.search(r'\b\d+\b', line) and any(unit in line.lower() for unit in ["loc", "months", "person-month", "%", "accuracy"]):
        score += 5
        logging.debug(f"Line '{line}' contains quantitative data, score += 5")
    # Boost score if this line follows a transitional phrase
    if line_index > 0 and re.match(r'^(let us|now let|consider|for example|suppose|ask any|pose the same)\b', lines[line_index - 1].lower()):
        score += 4
        logging.debug(f"Line '{line}' follows a transitional phrase, score += 4")

    # Negative indicators
    if re.match(r'^(what|why|how|where|when|who)\b', line.lower()) and line.endswith("?"):
        score -= 7
        logging.debug(f"Line '{line}' is a rhetorical question, score -= 7")
    if re.match(r'^(let us|now let|consider|for example|suppose|ask any|pose the same)\b', line.lower()):
        score -= 6
        logging.debug(f"Line '{line}' is a transitional/setup phrase, score -= 6")
    if len(line.split()) < 6:
        score -= 4
        logging.debug(f"Line '{line}' is too short, score -= 4")
    if line in ["Introduction", "Conclusion"] or re.match(r'^\w+:$', line) or line.startswith("#"):
        score -= 8
        logging.debug(f"Line '{line}' is a section header or heading, score -= 8")

    # Contextual boost
    for i in range(max(0, line_index - 5), line_index):
        prev_line = lines[i].strip()
        if prev_line.startswith("#") or prev_line in ["Artificial Intelligence"]:
            score += 2
            logging.debug(f"Line '{line}' is under heading '{prev_line}', score += 2")
            break

    if model and vectorizer:
        line_tfidf = vectorizer.transform([line])
        prediction = model.predict(line_tfidf)[0]
        logging.debug(f"ML prediction for '{line}': {prediction}")
        if score <= 0:
            logging.debug(f"Rule-based score {score} overrides ML prediction")
            return False
        return bool(prediction)

    is_important = score > 3
    logging.debug(f"Final score for '{line}': {score}, is_important: {is_important}")
    return is_important

def extract_key_terms(text: str) -> List[str]:
    """Extract key terms from a line of text, prioritizing nouns and key concepts."""
    text = text.strip()
    terms = re.findall(r'(?:[A-Z][a-z]*\s+[A-Z]?[a-z]*|[A-Z][a-z]{3,})', text)
    if not terms:
        stop_words = [
            'the', 'and', 'in', 'with', 'as', 'is', 'are', 'was', 'were', 'now', 'though',
            'introduction', 'example', 'consider', 'ask', 'what', 'why', 'how', 'where', 'when',
            'who', 'however', 'this', 'approach', 'proper', 'significantly', 'limited', 'foundational'
        ]
        terms = [term for term in re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()) if term not in stop_words and any(k in text.lower() for k in ["artificial", "machine", "deep", "symbolic", "neural"])]
    terms = [t for t in terms if len(t.split()) <= 2 and any(k in t.lower() for k in ["intelligence", "learning", "reasoning", "networks"])]
    logging.debug(f"Extracted key terms from '{text}': {terms}")
    return terms

def detect_category(lines: List[str], term: str) -> str:
    """Detect the category from the full context based on the term."""
    logging.debug(f"Detecting category for term: {term}")
    term = term.lower().strip()
    full_text = " ".join(lines).lower()
    if any(keyword in full_text for keyword in ["artificial intelligence", "machine learning", "deep learning", "symbolic reasoning", "neural networks", "ai"]):
        return "Artificial Intelligence"
    for line in lines:
        if line.startswith("#"):
            return line.strip("#").strip() or "General"
    return "General"

def generate_questions_and_answers(content: str) -> Dict[str, List[str]]:
    """Generate questions and associate answers based on context."""
    # Split content into lines and then into sentences
    lines = content.split("\n")
    sentences = []
    for line in lines:
        line = line.strip()
        if line:
            sentences.extend(re.split(r'(?<=[.!?])\s+', line))
    questions_answers = {}
    current_term = None
    answer_sentences = []

    logging.debug(f"Processing {len(sentences)} sentences from content")
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            logging.debug(f"Skipping empty sentence at index {i}")
            continue

        terms = extract_key_terms(sentence)
        if terms and not is_important_line(sentence, sentences, i):
            # If the sentence contains a term but is not important, look ahead for the definition
            for term in terms:
                if re.search(rf'\b{re.escape(term)}\b', sentence, re.IGNORECASE):
                    question = f"What is {term}?"
                    logging.debug(f"Generated question: {question} for term: {term}")
                    if current_term and answer_sentences:
                        questions_answers[f"What is {current_term}?"] = answer_sentences[:]
                        logging.debug(f"Added question: What is {current_term}? with answer: {' '.join(answer_sentences)}")
                    current_term = term
                    answer_sentences = []  # Start with empty to allow replacement
                    # Look ahead for the defining sentence
                    for j in range(i + 1, min(i + 4, len(sentences))):
                        next_sentence = sentences[j].strip()
                        if next_sentence and (re.search(rf'\b{re.escape(term)}\b', next_sentence, re.IGNORECASE) or any(k in next_sentence.lower() for k in ["neural", "accuracy"])):
                            answer_sentences = [next_sentence]  # Replace with the defining sentence
                            logging.debug(f"Set answer to defining sentence: '{next_sentence}' based on term or keyword match")
                            break
                        elif next_sentence and not re.match(r'^(let us|now let|consider|for example|suppose|ask any|pose the same)\b', next_sentence.lower()):
                            answer_sentences.append(next_sentence)
                            logging.debug(f"Added supporting sentence: '{next_sentence}'")
                    if current_term and answer_sentences:
                        questions_answers[question] = answer_sentences[:]
                        logging.debug(f"Added question: {question} with answer: {' '.join(answer_sentences)}")
        elif is_important_line(sentence, sentences, i):
            logging.debug(f"Sentence '{sentence}' identified as important")
            terms = extract_key_terms(sentence)
            if not terms:
                logging.debug(f"No key terms found in sentence: '{sentence}'")
                continue
            for term in terms:
                if re.search(rf'\b{re.escape(term)}\b', sentence, re.IGNORECASE):
                    question = f"What is {term}?"
                    logging.debug(f"Generated question: {question} for term: {term}")
                    if current_term and answer_sentences:
                        questions_answers[f"What is {current_term}?"] = answer_sentences[:]
                        logging.debug(f"Added question: What is {current_term}? with answer: {' '.join(answer_sentences)}")
                    current_term = term
                    answer_sentences = [sentence]  # Start with the current important sentence
                    # Look ahead for additional supporting sentences
                    for j in range(i + 1, min(i + 4, len(sentences))):
                        next_sentence = sentences[j].strip()
                        if is_important_line(next_sentence, sentences, j) and not next_sentence.startswith("-"):
                            logging.debug(f"Stopping look-ahead at sentence '{next_sentence}' as it's important")
                            break
                        if next_sentence and not next_sentence.startswith("#") and not re.match(r'^(what|why|how|where|when|who)\b', next_sentence.lower()) and not re.match(r'^(let us|now let|consider|for example|suppose|ask any|pose the same)\b', next_sentence.lower()):
                            answer_sentences.append(next_sentence)
                            logging.debug(f"Added to answer: '{next_sentence}'")
                    if current_term and answer_sentences:
                        questions_answers[question] = answer_sentences[:]
                        logging.debug(f"Added question: {question} with answer: {' '.join(answer_sentences)}")
        elif sentence.startswith("-") and is_important_line(sentence, sentences, i):
            subtopic = sentence.strip("-").strip()
            terms = extract_key_terms(subtopic)
            if terms:
                current_term = terms[0]
                answer_sentences = [subtopic]
                for j in range(i + 1, min(i + 4, len(sentences))):
                    next_sentence = sentences[j].strip()
                    if is_important_line(next_sentence, sentences, j) and not next_sentence.startswith("-"):
                        break
                    if next_sentence and not next_sentence.startswith("#") and not re.match(r'^(what|why|how|where|when|who)\b', next_sentence.lower()) and not re.match(r'^(let us|now let|consider|for example|suppose|ask any|pose the same)\b', next_sentence.lower()):
                        answer_sentences.append(next_sentence)
                if current_term and answer_sentences:
                    questions_answers[f"How does {current_term} work?"] = answer_sentences[:]
                    logging.debug(f"Added question: How does {current_term} work? with answer: {' '.join(answer_sentences)}")
                    answer_sentences = []

    if current_term and answer_sentences:
        questions_answers[f"What is {current_term}?"] = answer_sentences[:]
        logging.debug(f"Added final question: What is {current_term}? with answer: {' '.join(answer_sentences)}")

    return questions_answers

def generate_flashcards(content: str) -> List[Flashcard]:
    logging.info("Starting flashcard generation process")
    logging.debug(f"Input content: {content[:500]}...")
    flashcards = []
    term_to_front = {}

    logging.info("Generating questions and answers from content")
    questions_answers = generate_questions_and_answers(content)
    logging.debug(f"Generated {len(questions_answers)} question-answer pairs")

    for question, answer_sentences in questions_answers.items():
        logging.debug(f"Processing question: {question}")
        if question not in term_to_front:
            term = None
            if "What is " in question:
                parts = question.split("What is ")[1].split("?")
                if parts[0].strip():
                    term = parts[0].strip()
                else:
                    logging.warning(f"Invalid 'What is' question format: {question}")
                    continue
            elif "How does " in question:
                parts = question.split("How does ")[1].split(" work?")
                if parts[0].strip():
                    term = parts[0].strip()
                else:
                    logging.warning(f"Invalid 'How does' question format: {question}")
                    continue
            else:
                logging.warning(f"Unexpected question format: {question}")
                continue

            if term:
                category = detect_category(content.split("\n"), term)
                answer_text = " ".join(answer_sentences).strip()
                # Select the sentence containing the term or the first defining sentence
                answer_sentences_list = re.split(r'(?<=[.!?])\s+', answer_text)
                clean_answer = next((s for s in answer_sentences_list if term.lower() in s.lower()), next((s for s in answer_sentences_list if any(k in s.lower() for k in ["neural", "accuracy"])), answer_text if answer_sentences_list else "No definition available."))
                card = Flashcard(front=question, back=clean_answer, category=category)
                flashcards.append(card)
                term_to_front[question] = question
                logging.debug(f"Added flashcard: {card.front} -> {card.back} [Category: {card.category}]")
            else:
                logging.warning(f"Failed to extract term from question: {question}")

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