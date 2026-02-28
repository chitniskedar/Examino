"""
llm_question_gen.py — LLM-based MCQ generation from text sections.

Calls the Anthropic API (Claude) to generate structured MCQs.
Falls back to a simple heuristic extractor if the API is unavailable.
"""

import os
import re
import uuid
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Difficulty heuristic ──────────────────────────────────────────────────────

def infer_difficulty(section_text: str, section_index: int, total_sections: int) -> str:
    """
    Heuristic: later sections + longer sentences + technical jargon = harder.
    """
    text  = section_text.lower()
    words = section_text.split()

    # Complexity signals
    hard_signals   = ["derive","prove","calculate","determine","analyse","evaluate","compare","synthesis"]
    medium_signals = ["explain","describe","state","define","identify","list","what is"]

    hard_hits   = sum(1 for s in hard_signals   if s in text)
    medium_hits = sum(1 for s in medium_signals if s in text)

    # Position: later = harder
    position_ratio = section_index / max(total_sections - 1, 1)

    # Avg sentence length
    sentences = re.split(r'[.!?]+', section_text)
    avg_len   = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

    score = hard_hits * 2 + (1 if position_ratio > 0.6 else 0) + (1 if avg_len > 20 else 0)

    if score >= 3 or hard_hits >= 2:
        return "hard"
    elif score >= 1 or medium_hits >= 2 or avg_len > 15:
        return "medium"
    else:
        return "easy"


# ── LLM generation ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert academic question setter. Given a passage of study material, generate multiple-choice questions (MCQs).

Output ONLY a valid JSON array. Each element must have:
{
  "question_text": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_answer": "A. ...",   // must match one of the options exactly
  "question_type": "mcq"
}

Rules:
- Options must be labelled A. B. C. D.
- correct_answer must be the FULL option string (e.g. "A. Ohm's Law")
- Questions must be directly answerable from the passage
- Do not include explanations or extra keys
- Output ONLY the JSON array, no markdown, no preamble"""


async def generate_mcqs_from_section(
    section_text: str,
    num_questions: int = 3,
    difficulty: str = "medium",
    subject: str = "General",
    topic: str = "General",
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Generate MCQs from a text section using Claude API.
    Falls back to heuristic generation if API call fails.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    if key:
        try:
            return await _call_claude(section_text, num_questions, difficulty, key)
        except Exception as e:
            logger.warning(f"LLM generation failed, using fallback: {e}")

    # Fallback
    return _heuristic_generate(section_text, num_questions, difficulty, subject, topic)


async def _call_claude(
    text: str,
    num_q: int,
    difficulty: str,
    api_key: str,
) -> list[dict]:
    """Call Anthropic Claude API asynchronously."""
    import httpx

    user_prompt = (
        f"Generate exactly {num_q} MCQ questions at {difficulty} difficulty "
        f"based on the following study material:\n\n{text[:3000]}"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-3-haiku-20240307",
                "max_tokens": 2048,
                "system":     SYSTEM_PROMPT,
                "messages":   [{"role": "user", "content": user_prompt}],
            },
        )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"]

    return _parse_llm_response(content)


def _parse_llm_response(raw: str) -> list[dict]:
    """Parse JSON array from LLM output, tolerating minor formatting issues."""
    # Strip markdown code fences
    cleaned = re.sub(r'```(?:json)?\s*', '', raw).strip().strip('`')

    # Find the JSON array
    match = re.search(r'\[[\s\S]*\]', cleaned)
    if not match:
        raise ValueError("No JSON array found in LLM response")

    data = json.loads(match.group())
    result = []

    for item in data:
        qt  = item.get("question_text", "").strip()
        opts = item.get("options", [])
        ans  = item.get("correct_answer", "").strip()

        if not qt or not opts or not ans:
            continue
        if ans not in opts:
            # Try to match by prefix
            matched = next((o for o in opts if o.startswith(ans[:4])), None)
            if matched:
                ans = matched
            else:
                continue

        result.append({
            "question_text":  qt,
            "options":        opts,
            "correct_answer": ans,
            "question_type":  item.get("question_type", "mcq"),
        })

    return result


# ── Heuristic fallback ────────────────────────────────────────────────────────

def _heuristic_generate(
    text: str,
    num_q: int,
    difficulty: str,
    subject: str,
    topic: str,
) -> list[dict]:
    """
    Fallback: extract true/false and definition questions from the text.
    This ensures the system works even without an API key.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.split()) >= 8]
    questions = []

    # True/False from declarative sentences
    for sent in sentences[:num_q * 2]:
        if not re.search(r'\b(is|are|was|were|has|have|can|will|does)\b', sent, re.I):
            continue
        # Make a distractor by negating
        neg = re.sub(r'\b(is|are)\b', lambda m: "is not" if m.group() == "is" else "are not", sent, count=1, flags=re.I)
        if neg == sent:
            neg = sent.replace("has", "does not have", 1) if "has" in sent else sent + " (false)"

        questions.append({
            "question_text":  f"True or False: {sent}",
            "options":        ["A. True", "B. False", "C. Partially True", "D. Not mentioned"],
            "correct_answer": "A. True",
            "question_type":  "true_false",
        })

        if len(questions) >= num_q:
            break

    # Definition questions: "What is X?"
    defs = re.findall(r'([A-Z][a-z]{2,30})\s+(?:is|are|refers to|means)\s+(.{20,120})', text)
    for term, defn in defs[:num_q]:
        wrong = [f"B. A type of measurement", f"C. An electrical component", f"D. A mathematical function"]
        questions.append({
            "question_text":  f"What is {term}?",
            "options":        [f"A. {defn[:80].strip('.,')}", *wrong],
            "correct_answer": f"A. {defn[:80].strip('.,')}", 
            "question_type":  "mcq",
        })
        if len(questions) >= num_q:
            break

    return questions[:num_q]


# ── Assembler: add IDs and metadata ──────────────────────────────────────────

def assemble_questions(
    raw_questions: list[dict],
    subject: str,
    unit: str,
    topic: str,
    difficulty: str,
    source_file: str,
) -> list[dict]:
    """Attach metadata and generate stable IDs."""
    out = []
    for q in raw_questions:
        out.append({
            "question_id":     str(uuid.uuid4()),
            "question_type":   q.get("question_type", "mcq"),
            "question_text":   q["question_text"],
            "options":         q.get("options"),
            "correct_answer":  q["correct_answer"],
            "topic":           topic,
            "subject":         subject,
            "unit":            unit,
            "difficulty_level": difficulty,
            "source_file":     source_file,
            "source_type":     "PDF_UPLOAD",
            "question_format": "MCQ",
        })
    return out