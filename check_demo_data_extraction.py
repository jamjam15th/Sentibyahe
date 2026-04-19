#!/usr/bin/env python3
"""Check how demographic data is actually stored in responses."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "analytics.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get all form questions
c.execute("SELECT id, prompt, is_demographic FROM form_questions ORDER BY id")
all_questions = c.fetchall()
print("=== ALL QUESTIONS ===")
for qid, prompt, is_demo in all_questions:
    print(f"  Q{qid}: {prompt[:60]:<60} is_demographic={is_demo}")

print("\n=== RESPONSE DATA ===")
# Get all responses with their answers
c.execute("SELECT id, form_id, answers FROM form_responses LIMIT 10")
responses = c.fetchall()

for resp_id, form_id, answers_json in responses:
    print(f"\nResponse {resp_id} (Form {form_id}):")
    try:
        answers = json.loads(answers_json)
        print(f"  Raw answers dict keys: {list(answers.keys())}")
        for key, val in answers.items():
            print(f"    '{key}' -> {val}")
    except Exception as e:
        print(f"  ERROR parsing answers: {e}")
        print(f"  Raw: {answers_json[:200]}")

conn.close()
