from supabase import create_client

SUPABASE_URL = "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

form_id = "9a9a4e62-606"
admin_email = "ic.jamil.mariano@cvsu.edu.ph"

# Step 1: Enable demographics in form_meta
client.table("form_meta").update({"include_demographics": True}).eq("form_id", form_id).eq("admin_email", admin_email).execute()
print("✅ Enabled demographics in form_meta")

# Step 2: Add demographic questions (Q1-Q6)
STANDARD_DEMO_QUESTIONS = [
    {
        "form_id": form_id,
        "admin_email": admin_email,
        "prompt": "1. Age / Edad",
        "q_type": "Multiple Choice",
        "options": ["Below / Mababa sa 18", "18-25", "26-35", "36-45", "46-55", "Above / Mataas sa 55"],
        "is_required": True,
        "is_demographic": True,
        "enable_sentiment": False,
        "servqual_dimension": "Commuter Profile",
        "sort_order": 1,
        "is_locked": True,
    },
    {
        "form_id": form_id,
        "admin_email": admin_email,
        "prompt": "2. Gender / Kasarian",
        "q_type": "Multiple Choice",
        "options": ["Male (Lalaki)", "Female (Babae)", "Prefer not to say (Mas pinipiling huwag sabihin)"],
        "is_required": True,
        "is_demographic": True,
        "enable_sentiment": False,
        "servqual_dimension": "Commuter Profile",
        "sort_order": 2,
        "is_locked": True,
    },
    {
        "form_id": form_id,
        "admin_email": admin_email,
        "prompt": "3. Occupational Status / Katayuan sa Trabaho",
        "q_type": "Multiple Choice",
        "options": ["Student (Estudyante)", "Employee / Self-employed (Empleyado / may sariling pinagkikitaan)", "Employer / Business-owner (May-ari ng Negosyo)", "Unemployed (Walang trabaho)"],
        "is_required": True,
        "is_demographic": True,
        "enable_sentiment": False,
        "servqual_dimension": "Commuter Profile",
        "sort_order": 3,
        "is_locked": True,
    },
    {
        "form_id": form_id,
        "admin_email": admin_email,
        "prompt": "4. Monthly Allowance or Salary / Buwanang Sahod o Allowance",
        "q_type": "Multiple Choice",
        "options": ["Below / Mababa sa Php 5,000", "Php 5,001 - 10,000", "Php 10,001 - 20,000", "Php 20,001 - 30,000", "Php 30,001 - 40,000", "Php 40,001 - 50,000", "Above / Mataas sa Php 50,001"],
        "is_required": True,
        "is_demographic": True,
        "enable_sentiment": False,
        "servqual_dimension": "Commuter Profile",
        "sort_order": 4,
        "is_locked": True,
    },
    {
        "form_id": form_id,
        "admin_email": admin_email,
        "prompt": "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?",
        "q_type": "Multiple Choice",
        "options": ["Once a week (Isang beses sa isang linggo)", "2-3 times a week (2-3 beses sa isang linggo)", "4-5 times a week (4-5 beses sa isang linggo)", "Everyday (Araw-araw)"],
        "is_required": True,
        "is_demographic": True,
        "enable_sentiment": False,
        "servqual_dimension": "Commuter Profile",
        "sort_order": 5,
        "is_locked": True,
    },
    {
        "form_id": form_id,
        "admin_email": admin_email,
        "prompt": "6. Most frequently used transport mode / Pinakamadalas na sinasakyan",
        "q_type": "Multiple Choice",
        "options": ["Traditional Jeepney (Tradisyunal na Jeepney)", "Modern Jeepney (Modernong Jeepney)", "Bus", "Taxi (Taksi)", "UV Express", "Ride-hailing services (e.g., Angkas, Grab, Move It)", "LRT-1", "LRT-2", "MRT-3", "Others"],
        "is_required": True,
        "is_demographic": True,
        "enable_sentiment": False,
        "servqual_dimension": "Commuter Profile",
        "sort_order": 6,
        "is_locked": True,
    },
]

try:
    result = client.table("form_questions").upsert(STANDARD_DEMO_QUESTIONS).execute()
    print(f"✅ Added {len(STANDARD_DEMO_QUESTIONS)} demographic questions (Q1-Q6)")
    print("\nForm now has:")
    print("  - Q1-Q6: Demographic questions (Multiple Choice)")
    print("  - Q7-Q17: SERVQUAL questions (Paragraph with sentiment analysis)")
except Exception as e:
    print(f"❌ Error: {e}")
