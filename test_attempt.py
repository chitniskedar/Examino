import requests
import sys

API_BASE = "http://localhost:8000"

def test_attempt():
    try:
        # 1. Get a question ID first
        print("Fetching a question...")
        res = requests.get(f"{API_BASE}/questions?limit=1")
        if res.status_code != 200:
            print(f"Failed to fetch questions: {res.status_code}")
            return
        
        questions = res.json()
        if not questions:
            print("No questions found in database.")
            return
        
        q = questions[0]
        qid = q["question_id"]
        correct_ans = q["correct_answer"]
        
        print(f"Attempting question {qid} with correct answer...")
        
        # 2. Submit an attempt
        payload = {
            "question_id": qid,
            "user_answer": correct_ans
        }
        
        res = requests.post(f"{API_BASE}/attempt", json=payload)
        
        if res.status_code == 200:
            print("Success! /attempt returned 200 OK")
            print("Response:", res.json())
        else:
            print(f"Error! /attempt returned {res.status_code}")
            print("Response:", res.text)
            
    except Exception as e:
        print(f"Connection error: {e}")
        print("Make sure the backend is running at http://localhost:8000")

if __name__ == "__main__":
    test_attempt()
