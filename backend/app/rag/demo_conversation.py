# Throwaway demo: follow-up questions. 
import time

from app.rag.pipeline import answer_question
from app.rag.query_rewrite import rewrite_question

HISTORY = [
    ("user", "When did we visit Hawassa?"),
    ("bot", "You visited Hawassa with Grandma in December 2023."),
]
FOLLOW_UPS = [
    "Who was with us?",
    "Show me the pictures from that trip",
    "What did we do on January 15, 2022?",  
]
PAUSE_SECONDS = 12  

if __name__ == "__main__":
    for index, question in enumerate(FOLLOW_UPS):
        print(f"\nFollow-up: {question}")
        answer = answer_question(question, HISTORY)
        print(f"Rewritten: {answer.standalone_question}")
        print(f"Answer:    {answer.text}")
        print(f"           found={answer.found}  photo_ids={answer.photo_ids}")
        if index < len(FOLLOW_UPS) - 1:
            time.sleep(PAUSE_SECONDS)