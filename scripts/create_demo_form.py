#!/usr/bin/env python3
"""
Create a demo form with sample questions and responses.

Usage:
    python scripts/create_demo_form.py --email your-email@example.com
"""

import argparse
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client

def calculate_servqual_avgs(answers):
    """Calculate SERVQUAL dimension averages from individual question answers."""
    servqual_mapping = {
        "tangibles_avg": "How would you rate the cleanliness of the vehicle?",
        "reliability_avg": "How reliable was the schedule/timeliness?",
        "responsiveness_avg": "How responsive was the driver to your needs?",
        "assurance_avg": "How safe did you feel during the trip?",
        "empathy_avg": "How courteous was the driver?",
    }
    
    result = {}
    for col, question_key in servqual_mapping.items():
        value = answers.get(question_key)
        if value is not None:
            try:
                result[col] = float(value)
            except (ValueError, TypeError):
                result[col] = None
        else:
            result[col] = None
    
    return result

# Get credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://hwjuvnaphrwikooaqkkr.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "sb_publishable_m2K5AraHge-b_o1dqW0w0g_X5kaSdxH"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL environment variable")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_demo_form(admin_email: str):
    """Create a demo form with sample questions and responses."""
    
    print(f"\n✅ Creating demo form for {admin_email}...")
    
    # Step 1: Create form in form_list
    form_id = "demo-form-001"
    form_data = {
        "form_id": form_id,
        "admin_email": admin_email,
        "title": "Transport Experience Survey",
        "description": "Demo form to test the sentiment dashboard",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "is_archived": False,
    }
    
    try:
        result = client.table("form_list").upsert([form_data], on_conflict="form_id,admin_email").execute()
        print(f"✓ Form created: {form_data['title']}")
    except Exception as e:
        print(f"⚠️ Form creation warning: {e}")
    
    # Step 2: Create form_meta settings
    form_meta = {
        "admin_email": admin_email,
        "form_id": form_id,
        "public_id": form_id,
        "title": "How was your experience?",
        "description": "Please share your feedback on your recent transport experience.",
        "include_demographics": True,
        "allow_multiple_responses": True,
        "reach_out_contact": "Email: feedback@transport.local\nPhone: 555-0123",
    }
    
    try:
        result = client.table("form_meta").upsert([form_meta], on_conflict="admin_email,form_id").execute()
        print(f"✓ Form settings created")
    except Exception as e:
        print(f"⚠️ Form meta creation warning: {e}")
    
    # Step 3: Create sample questions (covering all 5 SERVQUAL dimensions)
    questions = [
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "How would you rate your overall experience?",
            "q_type": "Rating (Likert)",
            "options": [],
            "is_required": True,
            "is_demographic": False,
            "enable_sentiment": True,
            "scale_max": 5,
            "scale_label_low": "Very Unsatisfied",
            "scale_label_high": "Very Satisfied",
            "servqual_dimension": None,
            "sort_order": 1,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "How would you rate the cleanliness of the vehicle?",
            "q_type": "Rating (Likert)",
            "options": [],
            "is_required": True,
            "is_demographic": False,
            "enable_sentiment": True,
            "scale_max": 5,
            "scale_label_low": "Very Dirty",
            "scale_label_high": "Very Clean",
            "servqual_dimension": "Tangibles",
            "sort_order": 2,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "How reliable was the schedule/timeliness?",
            "q_type": "Rating (Likert)",
            "options": [],
            "is_required": True,
            "is_demographic": False,
            "enable_sentiment": True,
            "scale_max": 5,
            "scale_label_low": "Very Unreliable",
            "scale_label_high": "Very Reliable",
            "servqual_dimension": "Reliability",
            "sort_order": 3,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "How responsive was the driver to your needs?",
            "q_type": "Rating (Likert)",
            "options": [],
            "is_required": True,
            "is_demographic": False,
            "enable_sentiment": True,
            "scale_max": 5,
            "scale_label_low": "Not Responsive",
            "scale_label_high": "Very Responsive",
            "servqual_dimension": "Responsiveness",
            "sort_order": 4,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "How safe did you feel during the trip?",
            "q_type": "Rating (Likert)",
            "options": [],
            "is_required": True,
            "is_demographic": False,
            "enable_sentiment": True,
            "scale_max": 5,
            "scale_label_low": "Very Unsafe",
            "scale_label_high": "Very Safe",
            "servqual_dimension": "Assurance",
            "sort_order": 5,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "How courteous was the driver?",
            "q_type": "Rating (Likert)",
            "options": [],
            "is_required": True,
            "is_demographic": False,
            "enable_sentiment": True,
            "scale_max": 5,
            "scale_label_low": "Very Rude",
            "scale_label_high": "Very Courteous",
            "servqual_dimension": "Empathy",
            "sort_order": 6,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "What transport mode did you use?",
            "q_type": "Multiple Choice",
            "options": ["Bus", "Jeepney", "Tricycle", "E-trike", "Other"],
            "is_required": True,
            "is_demographic": True,
            "enable_sentiment": False,
            "servqual_dimension": None,
            "sort_order": 7,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "What is your age bracket?",
            "q_type": "Multiple Choice",
            "options": ["18-25", "26-35", "36-45", "46-55", "56+"],
            "is_required": True,
            "is_demographic": True,
            "enable_sentiment": False,
            "servqual_dimension": None,
            "sort_order": 8,
        },
        {
            "form_id": form_id,
            "admin_email": admin_email,
            "prompt": "Any additional feedback?",
            "q_type": "Paragraph",
            "options": [],
            "is_required": False,
            "is_demographic": False,
            "enable_sentiment": True,
            "servqual_dimension": None,
            "sort_order": 9,
        },
    ]
    
    try:
        result = client.table("form_questions").upsert(questions).execute()
        print(f"✓ {len(questions)} sample questions created (all 5 SERVQUAL dimensions + demographics)")
    except Exception as e:
        print(f"⚠️ Questions creation warning: {e}")
    
    # Step 4: Create sample responses (20 responses with calculated SERVQUAL averages)
    response_data = [
        # Day 1 (5 days ago)
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 4, "How reliable was the schedule/timeliness?": 5, "How responsive was the driver to your needs?": 4, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "Bus", "Any additional feedback?": "The bus was on time and comfortable. Driver was very helpful."}, "demo": {"What is your age bracket?": "26-35", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 5, "How would you rate the cleanliness of the vehicle?": 5, "How reliable was the schedule/timeliness?": 4, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 4, "What transport mode did you use?": "Jeepney", "Any additional feedback?": "Great service! The jeepney was clean and the driver was polite."}, "demo": {"What is your age bracket?": "36-45", "What is your gender?": "Male"}},
        {"answers": {"How would you rate your overall experience?": 3, "How would you rate the cleanliness of the vehicle?": 3, "How reliable was the schedule/timeliness?": 3, "How responsive was the driver to your needs?": 3, "How safe did you feel during the trip?": 3, "How courteous was the driver?": 3, "What transport mode did you use?": "E-trike", "Any additional feedback?": "Average service. Could be better."}, "demo": {"What is your age bracket?": "18-25", "What is your gender?": "Female"}},
        # Day 2 (4 days ago)
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 5, "How reliable was the schedule/timeliness?": 4, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "Tricycle", "Any additional feedback?": "Excellent service. Driver helped me with my bags. Very satisfied."}, "demo": {"What is your age bracket?": "56+", "What is your gender?": "Male"}},
        {"answers": {"How would you rate your overall experience?": 2, "How would you rate the cleanliness of the vehicle?": 2, "How reliable was the schedule/timeliness?": 2, "How responsive was the driver to your needs?": 2, "How safe did you feel during the trip?": 3, "How courteous was the driver?": 3, "What transport mode did you use?": "Bus", "Any additional feedback?": "Too crowded. AC was broken. Not satisfied."}, "demo": {"What is your age bracket?": "45-55", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 5, "How would you rate the cleanliness of the vehicle?": 5, "How reliable was the schedule/timeliness?": 5, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "Jeepney", "Any additional feedback?": "Perfect experience! Very clean and courteous driver."}, "demo": {"What is your age bracket?": "26-35", "What is your gender?": "Male"}},
        # Day 3 (3 days ago)
        {"answers": {"How would you rate your overall experience?": 3, "How would you rate the cleanliness of the vehicle?": 3, "How reliable was the schedule/timeliness?": 4, "How responsive was the driver to your needs?": 3, "How safe did you feel during the trip?": 4, "How courteous was the driver?": 4, "What transport mode did you use?": "E-trike", "Any additional feedback?": "Okay lang. Driver was friendly."}, "demo": {"What is your age bracket?": "36-45", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 4, "How reliable was the schedule/timeliness?": 4, "How responsive was the driver to your needs?": 4, "How safe did you feel during the trip?": 4, "How courteous was the driver?": 4, "What transport mode did you use?": "Bus", "Any additional feedback?": "Excellent experience. On time delivery."}, "demo": {"What is your age bracket?": "18-25", "What is your gender?": "Male"}},
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 4, "How reliable was the schedule/timeliness?": 5, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "Tricycle", "Any additional feedback?": "Excellent service. Driver was courteous and helpful."}, "demo": {"What is your age bracket?": "45-55", "What is your gender?": "Female"}},
        # Day 4 (2 days ago)
        {"answers": {"How would you rate your overall experience?": 2, "How would you rate the cleanliness of the vehicle?": 1, "How reliable was the schedule/timeliness?": 2, "How responsive was the driver to your needs?": 2, "How safe did you feel during the trip?": 2, "How courteous was the driver?": 2, "What transport mode did you use?": "Jeepney", "Any additional feedback?": "Very dirty. Driver rude. Not happy."}, "demo": {"What is your age bracket?": "56+", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 5, "How would you rate the cleanliness of the vehicle?": 5, "How reliable was the schedule/timeliness?": 5, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "E-trike", "Any additional feedback?": "Excellent! Clean vehicle and very professional driver."}, "demo": {"What is your age bracket?": "26-35", "What is your gender?": "Male"}},
        {"answers": {"How would you rate your overall experience?": 3, "How would you rate the cleanliness of the vehicle?": 2, "How reliable was the schedule/timeliness?": 3, "How responsive was the driver to your needs?": 3, "How safe did you feel during the trip?": 3, "How courteous was the driver?": 3, "What transport mode did you use?": "Bus", "Any additional feedback?": "Needs improvement. Cleanliness was below average."}, "demo": {"What is your age bracket?": "36-45", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 4, "How reliable was the schedule/timeliness?": 3, "How responsive was the driver to your needs?": 3, "How safe did you feel during the trip?": 4, "How courteous was the driver?": 3, "What transport mode did you use?": "Tricycle", "Any additional feedback?": "Satisfactory overall. Driver could be more courteous."}, "demo": {"What is your age bracket?": "18-25", "What is your gender?": "Male"}},
        # Day 5 (1 day ago)
        {"answers": {"How would you rate your overall experience?": 5, "How would you rate the cleanliness of the vehicle?": 5, "How reliable was the schedule/timeliness?": 5, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "Bus", "Any additional feedback?": "Perfect! Very clean and the driver was extremely helpful and professional."}, "demo": {"What is your age bracket?": "45-55", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 3, "How would you rate the cleanliness of the vehicle?": 3, "How reliable was the schedule/timeliness?": 3, "How responsive was the driver to your needs?": 4, "How safe did you feel during the trip?": 4, "How courteous was the driver?": 4, "What transport mode did you use?": "Jeepney", "Any additional feedback?": "Okay experience. Driver was helpful but vehicle could be cleaner."}, "demo": {"What is your age bracket?": "56+", "What is your gender?": "Male"}},
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 3, "How reliable was the schedule/timeliness?": 4, "How responsive was the driver to your needs?": 4, "How safe did you feel during the trip?": 4, "How courteous was the driver?": 4, "What transport mode did you use?": "E-trike", "Any additional feedback?": "Comfortable and safe ride overall."}, "demo": {"What is your age bracket?": "26-35", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 2, "How would you rate the cleanliness of the vehicle?": 2, "How reliable was the schedule/timeliness?": 2, "How responsive was the driver to your needs?": 2, "How safe did you feel during the trip?": 2, "How courteous was the driver?": 2, "What transport mode did you use?": "Tricycle", "Any additional feedback?": "Disappointing. Vehicle was dirty and driver was impolite."}, "demo": {"What is your age bracket?": "36-45", "What is your gender?": "Male"}},
        # Today
        {"answers": {"How would you rate your overall experience?": 5, "How would you rate the cleanliness of the vehicle?": 4, "How reliable was the schedule/timeliness?": 5, "How responsive was the driver to your needs?": 5, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 5, "What transport mode did you use?": "Bus", "Any additional feedback?": "Amazing experience! Would use again. Driver was very friendly."}, "demo": {"What is your age bracket?": "18-25", "What is your gender?": "Female"}},
        {"answers": {"How would you rate your overall experience?": 3, "How would you rate the cleanliness of the vehicle?": 4, "How reliable was the schedule/timeliness?": 3, "How responsive was the driver to your needs?": 3, "How safe did you feel during the trip?": 3, "How courteous was the driver?": 3, "What transport mode did you use?": "Jeepney", "Any additional feedback?": "Decent ride. Clean vehicle but driver could improve."}, "demo": {"What is your age bracket?": "45-55", "What is your gender?": "Male"}},
        {"answers": {"How would you rate your overall experience?": 4, "How would you rate the cleanliness of the vehicle?": 5, "How reliable was the schedule/timeliness?": 4, "How responsive was the driver to your needs?": 4, "How safe did you feel during the trip?": 5, "How courteous was the driver?": 4, "What transport mode did you use?": "E-trike", "Any additional feedback?": "Very satisfied. Clean and safe ride. Would recommend."}, "demo": {"What is your age bracket?": "56+", "What is your gender?": "Female"}},
    ]
    
    # Convert to proper format with calculated SERVQUAL averages
    sample_responses = []
    base_date = datetime.now(timezone.utc)
    for i, data in enumerate(response_data, 1):
        servqual_avgs = calculate_servqual_avgs(data["answers"])
        
        # Calculate which day this response should be on (spread across 5 days)
        # Responses 1-3: 5 days ago, 4-6: 4 days ago, 7-9: 3 days ago, 10-12: 2 days ago, 13-15: 1 day ago, 16-20: today
        day_offset = 5 - (i - 1) // 4
        created_at = base_date - timedelta(days=day_offset)
        
        response = {
            "form_id": form_id,
            "admin_email": admin_email,
            "client_submission_id": f"demo-resp-{i:03d}",
            "answers": data["answers"],
            "demo_answers": {**data["demo"], "What transport mode did you use?": data["answers"]["What transport mode did you use?"]},
            "created_at": created_at.isoformat(),
            **servqual_avgs,  # Add calculated SERVQUAL averages
        }
        sample_responses.append(response)
    
    try:
        result = client.table("form_responses").upsert(sample_responses).execute()
        print(f"✓ {len(sample_responses)} sample responses created (spread across 5 days for trends)")
    except Exception as e:
        print(f"⚠️ Responses creation warning: {e}")
    
    print(f"\n✅ Demo form '{form_data['title']}' created successfully!")
    print(f"📋 Form ID: {form_id}")
    print(f"📊 Now open the Sentiment Dashboard to see the data!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a demo form with sample data")
    parser.add_argument("--email", required=True, help="Admin email for the form")
    
    args = parser.parse_args()
    create_demo_form(args.email)
