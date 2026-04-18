from supabase import create_client
import json

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

form_id = "9a9a4e62-606"
admin_email = "ic.jamil.mariano@cvsu.edu.ph"

# Get the response with all columns
responses = client.table("form_responses").select("*").eq("form_id", form_id).eq("admin_email", admin_email).execute()

if responses.data:
    resp = responses.data[0]
    print("All columns in response:")
    for col_name, value in resp.items():
        value_type = type(value).__name__
        value_preview = str(value)[:80] if value else "NULL"
        print(f"  {col_name:30} ({value_type:10}): {value_preview}...")
