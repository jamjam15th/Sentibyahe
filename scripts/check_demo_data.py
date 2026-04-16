#!/usr/bin/env python3
from supabase import create_client
import os

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
client = create_client(url, key)

# Check questions
print('=== QUESTIONS ===')
q_result = client.table('form_questions').select('prompt, servqual_dimension').eq('form_id', 'demo-form-001').execute()
for q in q_result.data:
    print(f"  {q['prompt']} → {q['servqual_dimension']}")

print(f"\nTotal questions: {len(q_result.data)}")

# Check one response
print('\n=== SAMPLE RESPONSE ===')
r_result = client.table('form_responses').select('answers').eq('form_id', 'demo-form-001').limit(1).execute()
if r_result.data:
    answers = r_result.data[0].get('answers', {})
    print(f'Total answer fields: {len(answers)}')
    for key in answers.keys():
        print(f"  {key}")
