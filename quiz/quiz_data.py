import json
import random
from pathlib import Path

QUIZ_FILE = Path("C:/Users/Hrithik/OneDrive/Documents/AI/Fnite/trivia_quiz_project/quiz_data.json")

def load_quiz_data(path: Path = QUIZ_FILE) -> list[dict]:
    """
    Load quiz questions from a JSON file.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def get_random_questions(count: int = 3) -> list[dict]:
    """
    Return a random subset of questions from the quiz data.
    """
    all_questions = load_quiz_data()
    available = len(all_questions)
    if count <= 0:
        raise ValueError(f"Question count must be positive, got {count}.")
    if available == 0:
        raise ValueError("No quiz questions available in quiz_data.json.")
    if count >= available:
        # shuffle and return all if count exceeds availability
        random.shuffle(all_questions)
        return all_questions
    return random.sample(all_questions, k=count)