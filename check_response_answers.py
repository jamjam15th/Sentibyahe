from supabase import create_client

# Setup Supabase credentials
url = "https://hwjuvnaphrwikooaqkkr.supabase.co"
key = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"
client = create_client(url, key)

# Fetch the most recent responses for the form
email = "marianojamil15@gmail.com"
form_id = "8ec52a1a-dfd"

# Get recent responses
response = client.table("form_responses").select("*").eq("admin_email", email).eq("form_id", form_id).order("created_at", desc=True).limit(5).execute()

print(f"Found {len(response.data)} responses")

if response.data:
    print("\n" + "="*80)
    latest = response.data[0]
    print(f"Latest response ID: {latest.get('id')}")
    print(f"Created: {latest.get('created_at')}")
    
    # Print answers structure
    answers = latest.get("answers", {})
    print(f"\nTotal answers stored: {len(answers)}")
    
    print("\nANSWERS KEYS (first 10):")
    for key in list(answers.keys())[:10]:
        val = answers[key]
        print(f"  - {key[:60]}... = {val}")
    
    print("\n" + "="*80)
    print("\nLIKERT-LIKE ANSWERS:")
    for key, val in answers.items():
        if isinstance(val, str) and val.isdigit():
            print(f"  - {key[:60]}...")
            print(f"    Value: {val}")
