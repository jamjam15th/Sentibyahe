from supabase import create_client
import json

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

form_id = "9a9a4e62-606"
admin_email = "ic.jamil.mariano@cvsu.edu.ph"

# Get the response
responses = client.table("form_responses").select("*").eq("form_id", form_id).eq("admin_email", admin_email).execute()

print(f"Total responses: {len(responses.data or [])}\n")

if responses.data:
    resp = responses.data[0]
    print(f"Response ID: {resp.get('response_id')}")
    print(f"Submitted: {resp.get('created_at')}")
    print(f"Status: {resp.get('status')}\n")
    
    # Check the answers column
    answers = resp.get('answers', {})
    print(f"Type of answers: {type(answers)}")
    print(f"Answers keys: {list(answers.keys()) if isinstance(answers, dict) else 'Not a dict'}\n")
    
    # Print all answers
    if isinstance(answers, dict):
        for q_num, answer in sorted(answers.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
            print(f"Q{q_num}: {answer}")
    else:
        print(f"Answers value: {answers}")
    
    # Check other sentiment-related columns
    print(f"\n\nOther columns:")
    print(f"  likert_answers: {resp.get('likert_answers')}")
    print(f"  sentiment_scores: {resp.get('sentiment_scores')}")
    print(f"  paragraph_answers: {resp.get('paragraph_answers')}")
