#!/usr/bin/env python3
"""Check the actual structure of answers in responses."""

from supabase import create_client
import json

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get all distinct form_ids to find the one with responses
admin_email = "abigail.cagacao@gmail.com"

# Get forms
forms = supabase.table("form_list").select("form_id, title").eq("admin_email", admin_email).execute()
print("=== FORMS ===")
for form in forms.data:
    print(f"  {form['form_id']}: {form['title']}")

# For each form, check questions marked as demographic
print("\n=== DEMOGRAPHIC QUESTIONS BY FORM ===")
for form in forms.data:
    form_id = form['form_id']
    print(f"\n{form['title']} ({form_id}):")
    
    q_result = (supabase.table("form_questions")
                .select("id, prompt, is_demographic, q_type")
                .eq("admin_email", admin_email)
                .eq("form_id", form_id)
                .execute())
    
    if q_result.data:
        for q in q_result.data:
            if q.get('is_demographic'):
                print(f"  ✓ DEMOGRAPHIC: {q['prompt'][:60]}")
            else:
                print(f"    {q['prompt'][:60]}")

# Get responses
print("\n=== RESPONSE ANSWERS STRUCTURE ===")
resp_result = (supabase.table("form_responses")
               .select("id, form_id, answers")
               .eq("admin_email", admin_email)
               .limit(3)
               .execute())

if resp_result.data:
    for resp in resp_result.data:
        print(f"\nResponse {resp['id']} (Form: {resp['form_id']}):")
        answers = resp.get('answers', {})
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except:
                pass
        
        if isinstance(answers, dict):
            print(f"  Keys in answers dict: {list(answers.keys())}")
            for key, val in answers.items():
                print(f"    '{key}' -> {repr(val)[:80]}")
        else:
            print(f"  answers is {type(answers).__name__}: {repr(answers)[:200]}")
else:
    print("No responses found")
