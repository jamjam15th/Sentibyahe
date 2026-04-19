from supabase import create_client

url = "https://hwjuvnaphrwikooaqkkr.supabase.co"
key = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"
client = create_client(url, key)

email = "marianojamil15@gmail.com"
form_id = "8ec52a1a-dfd"

# Get all questions for your form
result = client.table("form_questions").select("id, prompt, q_type, is_demographic").eq("admin_email", email).eq("form_id", form_id).order("sort_order").execute()

print("DEMOGRAPHIC QUESTIONS IN DATABASE:")
print("=" * 80)
for q in result.data:
    if q.get("is_demographic"):
        print(f"\nPrompt: {q.get('prompt')}")
        print(f"Type: {q.get('q_type')}")
        print(f"Is Demographic: {q.get('is_demographic')}")

print("\n\nALL QUESTIONS:")
print("=" * 80)
for i, q in enumerate(result.data, 1):
    print(f"{i}. {q.get('prompt')[:60]}... | Type: {q.get('q_type')} | Demographic: {q.get('is_demographic')}")
