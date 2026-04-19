#!/usr/bin/env python3
"""Check which questions are marked as demographic for the form with responses."""

from supabase import create_client
import json

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# The form with responses
form_id = "9d8366d6-b25"
admin_email = "marianojamil15@gmail.com"

print(f"=== QUESTIONS IN FORM {form_id} ===")
q_result = (supabase.table("form_questions")
            .select("id, prompt, is_demographic, q_type")
            .eq("admin_email", admin_email)
            .eq("form_id", form_id)
            .execute())

print(f"Found {len(q_result.data)} questions:")
for q in q_result.data:
    is_demo = q.get('is_demographic')
    prompt = q.get('prompt', '')
    q_type = q.get('q_type', '')
    
    # Show the first 60 chars of the prompt
    prompt_preview = (prompt[:60] + '...') if len(prompt) > 60 else prompt
    
    marker = "✓ DEMOGRAPHIC" if is_demo else "  regular"
    print(f"{marker:20} | {q_type:20} | {prompt_preview}")

# Check which questions appear in the responses
print("\n=== QUESTIONS IN RESPONSE ANSWERS (sample) ===")
resp_result = supabase.table("form_responses").select("answers").eq("form_id", form_id).limit(1).execute()
if resp_result.data:
    answers = resp_result.data[0].get('answers', {})
    if isinstance(answers, str):
        answers = json.loads(answers)
    
    print(f"Found {len(answers)} questions in response:")
    for key in list(answers.keys())[:6]:
        print(f"  - {key[:70]}")

# Check which answer keys match demographic questions
print("\n=== MATCHING ANSWERS TO DEMOGRAPHIC QUESTIONS ===")
demographic_qs = [q for q in q_result.data if q.get('is_demographic')]
print(f"Demographic questions in form_questions: {len(demographic_qs)}")
for q in demographic_qs:
    print(f"  - {q['prompt'][:70]}")

if resp_result.data:
    answers = resp_result.data[0].get('answers', {})
    if isinstance(answers, str):
        answers = json.loads(answers)
    
    print(f"\nMatches found:")
    for q in demographic_qs:
        q_prompt = q.get('prompt')
        if q_prompt in answers:
            print(f"  ✓ {q_prompt[:50]} -> {answers[q_prompt]}")
        else:
            print(f"  ✗ {q_prompt[:50]} -> NOT FOUND in answers")
