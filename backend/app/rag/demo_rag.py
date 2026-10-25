import sys
import time

from app.rag.pipeline import answer_question

DEFAULT_QUESTIONS = [
    "When did we visit Hawassa?",
    "What was the weather like on the Hawassa trip?",
    "What did we do on January 15, 2022?",
    "Show me something about a wedding in Paris",
]

PAUSE_SECONDS = 12  # keeps us under free-tier requests-per-minute limits

if __name__ == "__main__":
    questions = sys.argv[1:] or DEFAULT_QUESTIONS
    for index, question in enumerate(questions):
        print(f"\nQ: {question}")
        answer = answer_question(question)
        print(f"A: {answer.text}")
        print(f"   found={answer.found}  photo_ids={answer.photo_ids}")
        print("   retrieved:", [(hit.photo_id, round(hit.score, 2)) for hit in answer.hits])
        if index < len(questions) - 1:
            time.sleep(PAUSE_SECONDS)