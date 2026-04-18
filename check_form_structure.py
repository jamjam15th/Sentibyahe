from supabase import create_client

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

form_id = "9a9a4e62-606"
admin_email = "ic.jamil.mariano@cvsu.edu.ph"

# Get all questions
questions = client.table("form_questions").select("sort_order, q_type, prompt, servqual_dimension").eq("form_id", form_id).eq("admin_email", admin_email).order("sort_order").execute()

print(f"Total questions in form: {len(questions.data or [])}\n")

demo_count = 0
servqual_count = 0
other_count = 0

for q in (questions.data or []):
    sort = q.get('sort_order')
    qtype = q.get('q_type')
    prompt = q.get('prompt', '')[:50]
    dim = q.get('servqual_dimension', 'None')
    
    if "Age" in str(prompt) or "Gender" in str(prompt) or "Occupation" in str(prompt):
        demo_count += 1
        label = "DEMOGRAPHIC"
    elif dim and dim != "None":
        servqual_count += 1
        label = "SERVQUAL"
    else:
        other_count += 1
        label = "OTHER"
    
    print(f"Q{sort}: [{label}] {qtype} - {prompt}...")
    if dim and dim != "None":
        print(f"         Dimension: {dim}")

print(f"\n\nSummary:")
print(f"  Demographic questions: {demo_count}")
print(f"  SERVQUAL questions: {servqual_count}")
print(f"  Other questions: {other_count}")
