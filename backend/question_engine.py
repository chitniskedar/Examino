"""
question_engine.py - Generates structured CS questions from parsed text
Question types: MCQ, True/False, Fill-in-the-Blank, Code Analysis, Time Complexity
"""

import re
import random
import uuid
from typing import Optional
from parser import extract_sections, extract_key_terms


# ─── Question Templates ───────────────────────────────────────────────────────

MCQ_TEMPLATES = [
    "What is the primary purpose of {term} in computer science?",
    "Which of the following best describes {term}?",
    "What is the time complexity of {term} in the average case?",
    "Which statement about {term} is CORRECT?",
    "In the context of the provided material, {term} refers to:",
]

TF_TEMPLATES = [
    "{statement}",
]

FITB_TEMPLATES = [
    "A ________ is used to store elements in LIFO order.",
    "The process of calling a function within itself is known as ________.",
    "________ search divides the search space in half each iteration.",
    "The worst-case time complexity of bubble sort is O(________).",
    "________ is a data structure where each node points to the next.",
    "In OOP, ________ allows a class to inherit properties from another class.",
    "A ________ traversal visits left subtree, root, then right subtree.",
    "________ programming solves problems by breaking them into overlapping subproblems.",
    "The ________ data structure follows FIFO order.",
    "________ is the maximum number of times an algorithm's steps execute.",
]

CODE_SNIPPETS = {
    "Python": [
        {
            "code": "def mystery(n):\n    if n <= 1:\n        return n\n    return mystery(n-1) + mystery(n-2)",
            "question": "What does this Python function compute?",
            "options": ["Factorial of n", "Fibonacci sequence", "Sum of 1 to n", "Power of 2"],
            "answer": "Fibonacci sequence",
            "topic": "recursion"
        },
        {
            "code": "lst = [3, 1, 4, 1, 5]\nresult = sorted(set(lst))",
            "question": "What is the value of `result` after this code executes?",
            "options": ["[1, 3, 4, 5]", "[3, 1, 4, 1, 5]", "[1, 1, 3, 4, 5]", "[5, 4, 3, 1]"],
            "answer": "[1, 3, 4, 5]",
            "topic": "data structures"
        },
        {
            "code": "stack = []\nfor i in range(3):\n    stack.append(i)\nprint(stack.pop())",
            "question": "What does this code print?",
            "options": ["0", "1", "2", "3"],
            "answer": "2",
            "topic": "stack"
        },
    ],
    "C++": [
        {
            "code": "int arr[] = {5, 3, 8, 1};\nstd::sort(arr, arr+4);\ncout << arr[0];",
            "question": "What is the output of this C++ code?",
            "options": ["5", "3", "8", "1"],
            "answer": "1",
            "topic": "sorting"
        },
    ],
    "general": [
        {
            "code": "function binarySearch(arr, target) {\n  let lo = 0, hi = arr.length - 1;\n  while (lo <= hi) {\n    let mid = Math.floor((lo + hi) / 2);\n    if (arr[mid] === target) return mid;\n    else if (arr[mid] < target) lo = mid + 1;\n    else hi = mid - 1;\n  }\n  return -1;\n}",
            "question": "What algorithm does this JavaScript function implement?",
            "options": ["Linear search", "Binary search", "Jump search", "Interpolation search"],
            "answer": "Binary search",
            "topic": "searching"
        }
    ]
}

COMPLEXITY_QUESTIONS = [
    {
        "question": "What is the time complexity of accessing an element in an array by index?",
        "options": ["O(n)", "O(log n)", "O(1)", "O(n²)"],
        "answer": "O(1)",
        "topic": "complexity"
    },
    {
        "question": "What is the worst-case time complexity of QuickSort?",
        "options": ["O(n log n)", "O(n)", "O(n²)", "O(log n)"],
        "answer": "O(n²)",
        "topic": "complexity"
    },
    {
        "question": "What is the space complexity of Merge Sort?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"],
        "answer": "O(n)",
        "topic": "complexity"
    },
    {
        "question": "What is the average-case time complexity of searching in a Hash Table?",
        "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "answer": "O(1)",
        "topic": "complexity"
    },
    {
        "question": "Which sorting algorithm has the best worst-case time complexity?",
        "options": ["Bubble Sort", "Insertion Sort", "Merge Sort", "Selection Sort"],
        "answer": "Merge Sort",
        "topic": "complexity"
    },
]

CS_FACTS = [
    ("A stack is a LIFO (Last In, First Out) data structure.", True, "stack"),
    ("Binary search requires the array to be sorted.", True, "searching"),
    ("A linked list provides O(1) random access.", False, "linked list"),
    ("The time complexity of bubble sort is O(n log n) in the worst case.", False, "sorting"),
    ("Recursion always uses more memory than iteration.", False, "recursion"),
    ("Dynamic programming solves overlapping subproblems by memoization.", True, "dynamic programming"),
    ("A binary tree can have at most 3 children per node.", False, "tree"),
    ("Hash tables use a hash function to map keys to indices.", True, "hash"),
    ("DFS uses a queue as its primary data structure.", False, "graph"),
    ("The Fibonacci sequence can be computed with O(n) space using DP.", True, "dynamic programming"),
    ("In Python, lists are implemented as dynamic arrays.", True, "data structures"),
    ("Inheritance is not a feature of Object-Oriented Programming.", False, "OOP"),
    ("Quick sort is an in-place sorting algorithm.", True, "sorting"),
    ("A graph with no cycles is called a tree.", True, "graph"),
    ("O(log n) is faster than O(n) for large inputs.", True, "complexity"),
]

FITB_ANSWERS = {
    "A ________ is used to store elements in LIFO order.": ("stack", "stack"),
    "The process of calling a function within itself is known as ________.": ("recursion", "recursion"),
    "________ search divides the search space in half each iteration.": ("Binary", "searching"),
    "The worst-case time complexity of bubble sort is O(________)." : ("n²", "complexity"),
    "________ is a data structure where each node points to the next.": ("Linked list", "linked list"),
    "In OOP, ________ allows a class to inherit properties from another class.": ("Inheritance", "OOP"),
    "A ________ traversal visits left subtree, root, then right subtree.": ("inorder", "tree"),
    "________ programming solves problems by breaking them into overlapping subproblems.": ("Dynamic", "dynamic programming"),
    "The ________ data structure follows FIFO order.": ("queue", "queue"),
    "________ is the maximum number of times an algorithm's steps execute.": ("Time complexity", "complexity"),
}

# ─── Main Generator ───────────────────────────────────────────────────────────

def generate_questions(text: str, num_questions: int = 10, difficulty: str = "medium") -> list[dict]:
    """
    Generate a mix of question types from the provided text.
    Returns list of question objects.
    """
    sections = extract_sections(text)
    key_terms = extract_key_terms(text)
    
    # Detect language
    lang = "general"
    if "[LANGUAGE: Python]" in text:
        lang = "Python"
    elif "[LANGUAGE: C++]" in text:
        lang = "C++"
    elif "[LANGUAGE: Java]" in text:
        lang = "Java"

    questions = []
    
    # Mix of question types
    type_weights = {
        "easy":   {"mcq": 3, "tf": 4, "fitb": 2, "code": 1, "complexity": 0},
        "medium": {"mcq": 3, "tf": 2, "fitb": 2, "code": 2, "complexity": 1},
        "hard":   {"mcq": 2, "tf": 1, "fitb": 1, "code": 3, "complexity": 3},
    }
    weights = type_weights.get(difficulty, type_weights["medium"])
    pool = []
    for qtype, count in weights.items():
        pool.extend([qtype] * count)

    random.shuffle(pool)
    
    generated_types = pool[:num_questions]
    # pad if needed
    while len(generated_types) < num_questions:
        generated_types.append(random.choice(["mcq", "tf", "fitb"]))

    for qtype in generated_types:
        q = None
        if qtype == "mcq":
            q = _gen_mcq(key_terms, sections, difficulty)
        elif qtype == "tf":
            q = _gen_tf(difficulty)
        elif qtype == "fitb":
            q = _gen_fitb(difficulty)
        elif qtype == "code":
            q = _gen_code(lang, difficulty)
        elif qtype == "complexity":
            q = _gen_complexity(difficulty)
        
        if q:
            questions.append(q)

    # Deduplicate by question_text
    seen = set()
    unique = []
    for q in questions:
        if q["question_text"] not in seen:
            seen.add(q["question_text"])
            unique.append(q)

    return unique[:num_questions]


def _make_q(qtype: str, text: str, options: Optional[list], answer: str, topic: str, difficulty: str) -> dict:
    return {
        "question_id": str(uuid.uuid4()),
        "question_type": qtype,
        "question_text": text,
        "options": options,
        "correct_answer": answer,
        "topic": topic,
        "difficulty_level": difficulty,
    }


def _gen_mcq(key_terms: list, sections: list, difficulty: str) -> dict:
    # Use complexity questions for hard, else generate from terms
    if difficulty == "hard" and random.random() < 0.5:
        return _gen_complexity(difficulty)
    
    term = random.choice(key_terms) if key_terms else "algorithm"
    template = random.choice(MCQ_TEMPLATES)
    question_text = template.replace("{term}", term)
    
    # Generate plausible distractors
    all_terms = list(set(key_terms) - {term})
    distractors = random.sample(all_terms, min(3, len(all_terms)))
    while len(distractors) < 3:
        distractors.append(random.choice(["a different concept", "none of the above", "all of the above"]))
    
    correct = f"A fundamental CS concept related to {term}"
    options = [correct] + [f"A concept related to {d}" for d in distractors]
    random.shuffle(options)
    
    return _make_q("mcq", question_text, options, correct, term, difficulty)


def _gen_tf(difficulty: str) -> dict:
    # Filter by difficulty proxy (harder = more tricky false statements)
    if difficulty == "easy":
        candidates = [(s, a, t) for s, a, t in CS_FACTS if a]  # only true ones for easy
    elif difficulty == "hard":
        candidates = [(s, a, t) for s, a, t in CS_FACTS if not a]  # tricky false ones
    else:
        candidates = CS_FACTS
    
    if not candidates:
        candidates = CS_FACTS
    
    fact, answer, topic = random.choice(candidates)
    return _make_q("true_false", fact, ["True", "False"], str(answer), topic, difficulty)


def _gen_fitb(difficulty: str) -> dict:
    template = random.choice(FITB_TEMPLATES)
    answer, topic = FITB_ANSWERS.get(template, ("unknown", "general"))
    return _make_q("fill_blank", template, None, answer, topic, difficulty)


def _gen_code(lang: str, difficulty: str) -> dict:
    snippets = CODE_SNIPPETS.get(lang, []) + CODE_SNIPPETS["general"]
    if not snippets:
        return _gen_tf(difficulty)
    
    snippet = random.choice(snippets)
    q_text = f"```\n{snippet['code']}\n```\n\n{snippet['question']}"
    return _make_q("code_analysis", q_text, snippet["options"], snippet["answer"], snippet["topic"], difficulty)


def _gen_complexity(difficulty: str) -> dict:
    q = random.choice(COMPLEXITY_QUESTIONS)
    return _make_q("complexity", q["question"], q["options"], q["answer"], q["topic"], difficulty)