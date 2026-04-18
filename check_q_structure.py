from supabase import create_client
import json

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

form_id = "9a9a4e62-606"
admin_email = "ic.jamil.mariano@cvsu.edu.ph"

# Get the response
responses = client.table("form_responses").select("question_sentiments").eq("form_id", form_id).eq("admin_email", admin_email).execute()

if responses.data:
    q_sent = responses.data[0].get("question_sentiments", {})
    
    # Check first question's structure
    first_q = list(q_sent.items())[0]
    print(f"First question key: {first_q[0][:50]}...")
    print(f"\nFirst question data structure:")
    print(json.dumps(first_q[1], indent=2))
    
    print(f"\n\nAll fields in question data: {list(first_q[1].keys())}")
    print(f"Has 'dimension' field? {'dimension' in first_q[1]}")
