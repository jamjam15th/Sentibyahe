from supabase import create_client

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

form_id = "9a9a4e62-606"
admin_email = "ic.jamil.mariano@cvsu.edu.ph"

# Step 1: Get all form questions with their dimensions
questions = client.table("form_questions").select("prompt, servqual_dimension, sort_order").eq("form_id", form_id).eq("admin_email", admin_email).order("sort_order").execute()

# Create a mapping from prompt to dimension
prompt_to_dimension = {}
for q in (questions.data or []):
    prompt = q.get("prompt", "")
    dimension = q.get("servqual_dimension")
    prompt_to_dimension[prompt] = dimension
    print(f"Q{q.get('sort_order')}: {prompt[:50]:50} -> {dimension}")

print(f"\n\nTotal questions mapped: {len(prompt_to_dimension)}\n")

# Step 2: Get the response
responses = client.table("form_responses").select("id, question_sentiments").eq("form_id", form_id).eq("admin_email", admin_email).execute()

if responses.data:
    resp = responses.data[0]
    response_id = resp.get("id")
    q_sent = resp.get("question_sentiments", {})
    
    print(f"Updating {len(q_sent)} questions in response...\n")
    
    # Step 3: Update each question_sentiment with its dimension
    updated_count = 0
    for q_key, q_data in q_sent.items():
        # Try to find matching question by looking at the key and mapping
        # The key might be the full prompt or part of it
        matching_dimension = None
        
        # Try exact match first
        if q_key in prompt_to_dimension:
            matching_dimension = prompt_to_dimension[q_key]
        else:
            # Try partial match - look for prompt that contains this key phrase
            for prompt, dimension in prompt_to_dimension.items():
                if q_key in prompt or prompt in q_key:
                    matching_dimension = dimension
                    break
        
        if matching_dimension:
            q_data["dimension"] = matching_dimension
            updated_count += 1
            print(f"✅ {q_key[:50]:50} -> {matching_dimension}")
        else:
            print(f"⚠️ {q_key[:50]:50} -> NO MATCH")
    
    # Step 4: Save the updated response
    if updated_count > 0:
        client.table("form_responses").update({
            "question_sentiments": q_sent
        }).eq("id", response_id).execute()
        print(f"\n✅ Updated {updated_count} questions with dimensions!")
    else:
        print(f"\n❌ No dimensions were matched!")
