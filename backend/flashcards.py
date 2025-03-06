from typing import List
from .models import Flashcard
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flashstudy.log"),
        logging.StreamHandler()  # Output to console
    ]
)

def is_important_line(line: str) -> bool:
    """Determine if a line contains important information."""
    line = line.lower().strip()
    if not line:
        return False
    is_important = bool(
        re.search(r'\b(is a|refers to|means|defined as|concerned with|represents|emulate|ability)\b', line) or
        re.match(r'^(what|why|how|define|explain|list|describe|what are|who is)', line) or
        any(keyword in line for keyword in ["ai", "symbolic", "expert", "machine", "deep", "learning", "reasoning"])
    )
    logging.debug(f"Checking importance of '{line}': {is_important}")
    return is_important

def extract_key_terms(text: str) -> List[str]:
    """Extract key terms from a line of text."""
    text = text.lower()
    stopwords = {"what", "is", "a", "the", "an", "are", "who", "how", "define", "explain", "list", "describe"}
    terms = re.sub(r'^(what|why|how|define|explain|list|describe|what are|who is)\s+', '', text).strip()
    terms = re.sub(r'\?', '', terms)
    key_terms = [term for term in re.findall(r'\w{3,}', terms) if term not in stopwords and len(term) > 2]
    logging.debug(f"Extracted key terms from '{text}': {key_terms}")
    return key_terms

def generate_questions_from_headings(lines: List[str], current_category: str) -> List[Flashcard]:
    """Generate questions from headings, subheadings, and important lines."""
    flashcards = []
    for i, line in enumerate(lines):
        line = line.strip()
        # Consider headings, standalone important lines, and lines with key terms
        if line.startswith("#") or (line and is_important_line(line) and not line.startswith("-")):
            topic = line.strip().strip("#")
            if topic and len(extract_key_terms(topic)) > 0:
                question = f"What is {topic}?"  # Ensure "What is X?" format
                logging.debug(f"Generating question from heading: {question}")
                answer_lines = []
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith("#") and not re.match(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)', next_line, re.IGNORECASE):
                        if is_important_line(next_line):
                            answer_lines.append(next_line)
                        else:
                            break
                    else:
                        break
                answer = " ".join(answer_lines).strip() if answer_lines else "No specific definition available."
                logging.debug(f"Answer for {question}: {answer}")
                if answer:
                    flashcards.append(Flashcard(front=question, back=answer, category=current_category))
        # Generate questions from list items or subpoints
        elif line.startswith("-"):
            subtopic = line.strip("-").strip()
            if subtopic and is_important_line(subtopic):
                question = f"What is {subtopic}?"  # Ensure "What is X?" format
                logging.debug(f"Generating question from subpoint: {question}")
                answer_lines = []
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith("#") and not next_line.startswith("-"):
                        if is_important_line(next_line):
                            answer_lines.append(next_line)
                        else:
                            break
                    else:
                        break
                answer = " ".join(answer_lines).strip() if answer_lines else "No specific definition available."
                logging.debug(f"Answer for {question}: {answer}")
                if answer:
                    flashcards.append(Flashcard(front=question, back=answer, category=current_category))
    return flashcards

def generate_flashcards(content: str) -> List[Flashcard]:
    logging.info("Starting flashcard generation process")
    logging.debug(f"Input content: {content[:500]}...")  # Log first 500 chars
    flashcards = []
    lines = content.split("\n")
    current_category = "General"
    current_answer_lines = []
    question = None
    term_to_front = {}

    # Step 1: Parse document for questions and answers
    logging.info("Parsing document for questions and answers")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        if line.startswith("#"):  # Category detection
            current_category = line.strip("#").strip()
            logging.debug(f"Detected category: {current_category}")
        elif re.match(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)', line, re.IGNORECASE) and is_important_line(line):
            logging.debug(f"Found question: {line}")
            # Save the previous flashcard if exists
            if current_answer_lines and question:
                answer = " ".join(current_answer_lines).strip()
                if answer and is_important_line(answer):
                    card = Flashcard(front=question, back=answer, category=current_category)
                    flashcards.append(card)
                    key_term = re.sub(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)\s+', '', question.lower()).strip()
                    term_to_front[key_term] = question
                    logging.debug(f"Added flashcard: {card.front} -> {card.back}")
                current_answer_lines = []

            # Set the current question (handle typos and ensure "What is X?" format)
            question = line.strip()
            if "what is at" in question.lower():
                question = "What is AI?"
                logging.debug("Corrected 'What is at?' to 'What is AI?'")
            # Ensure the question follows the "What is X?" format
            match = re.match(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)\s+(.*?)\?', line, re.IGNORECASE)
            if match:
                term = match.group(2).strip()
                question = f"What is {term}?"
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith("#") and not re.match(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)', next_line, re.IGNORECASE):
                    if is_important_line(next_line):
                        current_answer_lines.append(next_line)
                else:
                    break
            if not current_answer_lines:
                current_answer_lines = [""]
                logging.warning("No answer lines found for question")
        elif ":" in line:  # Term:definition format
            term, definition = line.split(":", 1)
            term = term.strip()
            definition = definition.strip()
            if is_important_line(definition):
                question = f"What is {term}?"  # Ensure "What is X?" format
                card = Flashcard(front=question, back=definition, category=current_category)
                flashcards.append(card)
                term_to_front[term.lower()] = question
                logging.debug(f"Added term:definition flashcard: {question} -> {definition}")

    # Save the last flashcard from the document
    if current_answer_lines and question:
        answer = " ".join(current_answer_lines).strip()
        if answer and is_important_line(answer):
            card = Flashcard(front=question, back=answer, category=current_category)
            flashcards.append(card)
            key_term = re.sub(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)\s+', '', question.lower()).strip()
            term_to_front[key_term] = question
            logging.debug(f"Added last flashcard: {card.front} -> {card.back}")

    # Step 2: Generate additional questions from headings and subpoints
    logging.info("Generating questions from headings and subpoints")
    heading_flashcards = generate_questions_from_headings(lines, current_category)
    flashcards.extend(heading_flashcards)
    logging.debug(f"Added {len(heading_flashcards)} flashcards from headings and subpoints")

    # Step 3: Link related flashcards based on shared key terms
    logging.info("Linking related flashcards")
    for i, card in enumerate(flashcards):
        card_terms = set(extract_key_terms(card.front) + extract_key_terms(card.back))
        for j, other_card in enumerate(flashcards):
            if i != j:  # Avoid self-linking
                other_terms = set(extract_key_terms(other_card.front) + extract_key_terms(other_card.back))
                if card_terms & other_terms:
                    card.links.append(other_card.front)
                    logging.debug(f"Linked {card.front} to {other_card.front}")

    # Step 4: Generate additional flashcards from key terms in the document
    logging.info("Extracting key terms for additional flashcards")
    key_terms = set()
    for line in lines:
        if ":" in line:
            term = line.split(":")[0].strip()
            if term and len(term.split()) <= 3 and is_important_line(line):
                key_terms.add(term)
        elif re.match(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)', line, re.IGNORECASE):
            match = re.match(r'^(What|Why|How|Define|Explain|List|Describe|What are|Who is)\s+(.*?)\?', line, re.IGNORECASE)
            if match:
                term = match.group(2).strip()
                if term and len(term.split()) <= 3:
                    key_terms.add(term)
        elif line.strip() and is_important_line(line) and not line.startswith("#"):
            # Extract terms like "Symbolic Reasoning", "Expert Systems", etc.
            terms = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line)
            for term in terms:
                if term and len(term.split()) <= 3 and is_important_line(term):
                    key_terms.add(term)
            # Fallback to extract_key_terms if no capitalized terms found
            if not terms:
                terms = extract_key_terms(line)
                key_terms.update(terms)

    # Generate flashcards from key terms if not already covered
    logging.info(f"Generating flashcards for {len(key_terms)} key terms from document")
    for term in key_terms:
        if term.lower() not in term_to_front:
            question = f"What is {term}?"  # Ensure "What is X?" format
            # Find an answer by looking for the term in the document
            answer_lines = []
            for line in lines:
                if term.lower() in line.lower() and is_important_line(line):
                    answer_lines.append(line)
            answer = " ".join(answer_lines).strip() if answer_lines else "No specific definition available."
            if answer and answer != "No specific definition available.":
                card = Flashcard(front=question, back=answer, category=current_category)
                flashcards.append(card)
                term_to_front[term.lower()] = question
                logging.debug(f"Added key term flashcard: {question} -> {answer}")

    # Combine and limit to 20 flashcards
    if len(flashcards) > 20:
        flashcards = flashcards[:20]  # Cap at 20
        logging.info("Capped flashcards at 20")

    # Final debugging output
    if not flashcards:
        logging.warning(f"No flashcards generated. Content processed: {content[:500]}...")
    else:
        logging.info(f"Successfully generated {len(flashcards)} flashcards")
        for i, card in enumerate(flashcards):
            logging.debug(f"Flashcard {i+1}: {card.front} -> {card.back} [Category: {card.category}, Links: {card.links}]")
    return flashcards