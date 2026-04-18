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
    
    print("Looking for Tangibles questions:\n")
    for q_key, q_data in q_sent.items():
        if "DIMENSION 1: TANGIBLES" in q_key or "air ventilation" in q_key:
            print(f"Question: {q_key[:60]}...")
            print(json.dumps(q_data, indent=2))
            print()
