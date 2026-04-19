from supabase import create_client

# Setup Supabase credentials
url = "https://hwjuvnaphrwikooaqkkr.supabase.co"
key = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"
client = create_client(url, key)

# Fetch all questions for your form
email = "marianojamil15@gmail.com"
form_id = "8ec52a1a-dfd"

result = client.table("form_questions").select("id, prompt, q_type, servqual_dimension, enable_sentiment").eq("admin_email", email).eq("form_id", form_id).order("sort_order").execute()

print(f"Total questions: {len(result.data)}\n")

# Group by type
likert_questions = [q for q in result.data if q.get("q_type") in ("Rating (Likert)", "Rating (1-5)")]
other_questions = [q for q in result.data if q.get("q_type") not in ("Rating (Likert)", "Rating (1-5)")]

print(f"LIKERT QUESTIONS ({len(likert_questions)}):")
print("-" * 80)
for q in likert_questions:
    print(f"\n  Prompt: {q.get('prompt')}")
    print(f"  Type: {q.get('q_type')}")
    print(f"  Dimension: {q.get('servqual_dimension')}")
    print(f"  Enable Sentiment: {q.get('enable_sentiment')}")

print(f"\n\nOTHER QUESTIONS ({len(other_questions)}):")
print("-" * 80)
for q in other_questions:
    print(f"\n  Prompt: {q.get('prompt')[:70]}")
    print(f"  Type: {q.get('q_type')}")
