import json
from collections import defaultdict

INPUT_FILE = "question_bank_raw.json"
OUTPUT_FILE = "question_bank.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw_data = f.read()

# Split multiple JSON root objects
blocks = raw_data.strip().split("}\n\n{")

fixed_blocks = []

for i, block in enumerate(blocks):
    if not block.startswith("{"):
        block = "{" + block
    if not block.endswith("}"):
        block = block + "}"
    fixed_blocks.append(json.loads(block))

merged = defaultdict(list)

for block in fixed_blocks:
    for subject, questions in block.items():
        merged[subject].extend(questions)

# Remove duplicates
unique = defaultdict(list)
seen = set()

for subject, questions in merged.items():
    for q in questions:
        key = (subject, q["q"])
        if key not in seen:
            seen.add(key)
            unique[subject].append(q)

# Sort by Unit then Difficulty
difficulty_order = {"easy": 1, "medium": 2, "hard": 3}

for subject in unique:
    unique[subject] = sorted(
        unique[subject],
        key=lambda x: (
            x.get("unit", ""),
            difficulty_order.get(x.get("diff", "medium"), 2)
        )
    )

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(unique, f, indent=2, ensure_ascii=False)

print("Merged and cleaned successfully.")