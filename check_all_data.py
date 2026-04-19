#!/usr/bin/env python3
"""Check what data exists in Supabase."""

from supabase import create_client
import json

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get all forms (no filter)
print("=== ALL FORMS ===")
forms_result = supabase.table("form_list").select("*").limit(5).execute()
print(f"Found {len(forms_result.data)} forms")
for form in forms_result.data[:3]:
    print(f"  {form.get('form_id', 'N/A')}: {form.get('title', 'N/A')} (admin: {form.get('admin_email', 'N/A')})")

# Get all responses
print("\n=== ALL RESPONSES ===")
resp_result = supabase.table("form_responses").select("*").limit(3).execute()
print(f"Found {len(resp_result.data)} responses")
for resp in resp_result.data[:3]:
    print(f"  Response {resp['id']} (Form: {resp.get('form_id', 'N/A')})")
    answers = resp.get('answers', {})
    if isinstance(answers, str):
        try:
            answers = json.loads(answers)
        except:
            pass
    
    if isinstance(answers, dict):
        print(f"    Keys: {list(answers.keys())}")
        for key in list(answers.keys())[:3]:
            val = answers[key]
            print(f"      '{key}' -> {repr(val)[:100]}")
    else:
        print(f"    answers type: {type(answers).__name__}")
