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
    print(f"question_sentiments keys: {list(q_sent.keys())}\n")
    
    print("Checking which ones are marked for sentiment and their status:")
    for q_key, q_data in q_sent.items():
        if isinstance(q_data, dict):
            enable_sent = q_data.get("enable_sentiment", False)
            sentiment = q_data.get("sentiment", "NOT_SET")
            text = q_data.get("text", "")[:30]
            print(f"  {q_key[:50]:50} -> enable_sentiment={enable_sent}, sentiment={sentiment}, text='{text}'")
