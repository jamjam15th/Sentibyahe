#!/usr/bin/env python3
"""
Fix the form_id mismatch by:
1. Deleting the "Good" demo form
2. Moving all questions from orphaned form to "First Form"

Usage:
    python scripts/fix_form_ids.py --email your-email@example.com
"""

import argparse
import os
from supabase import create_client

# ══════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# If not in environment, try to read from api_keys.txt
if not url or not key:
    try:
        # Try both relative paths
        api_file = None
        if os.path.exists("api_keys.txt"):
            api_file = "api_keys.txt"
        elif os.path.exists("../api_keys.txt"):
            api_file = "../api_keys.txt"
        
        if api_file:
            with open(api_file, "r") as f:
                content = f.read()
                for line in content.split("\n"):
                    if "SUPABASE_URL" in line:
                        url = line.split('=')[1].strip().strip('"')
                    elif "SUPABASE_KEY" in line:
                        key = line.split('=')[1].strip().strip('"')
    except Exception as e:
        print(f"Debug: {e}")
        pass

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY not found in environment or api_keys.txt")
    exit(1)

conn = create_client(url, key)

# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
parser = argparse.ArgumentParser(description="Fix form_id mismatches")
parser.add_argument("--email", required=True, help="Your admin email")
args = parser.parse_args()

admin_email = args.email

print(f"🔧 Fixing form IDs for {admin_email}...\n")

try:
    # Step 1: Find all forms
    forms_res = conn.table("form_list").select("*").eq("admin_email", admin_email).execute()
    forms = {f["id"]: f["title"] for f in forms_res.data or []}
    
    print("📋 Forms found:")
    for fid, title in forms.items():
        print(f"  - {title}: {fid}")
    
    # Step 2: Delete "Good" form if it exists
    good_form_id = None
    for fid, title in forms.items():
        if title == "Good":
            good_form_id = fid
            break
    
    if good_form_id:
        print(f"\n🗑️  Deleting 'Good' form ({good_form_id})...")
        conn.table("form_responses").delete().eq("form_id", good_form_id).execute()
        conn.table("form_questions").delete().eq("form_id", good_form_id).execute()
        conn.table("form_meta").delete().eq("form_id", good_form_id).execute()
        conn.table("form_list").delete().eq("id", good_form_id).execute()
        print("  ✓ Deleted 'Good' form")
    
    # Step 3: Find "First Form" ID
    first_form_id = None
    for fid, title in forms.items():
        if title == "First Form":
            first_form_id = fid
            break
    
    if not first_form_id:
        print("❌ 'First Form' not found!")
        exit(1)
    
    print(f"\n🔗 Moving all questions to 'First Form' ({first_form_id})...")
    
    # Find all questions
    q_res = conn.table("form_questions").select("*").eq("admin_email", admin_email).execute()
    questions = q_res.data or []
    
    print(f"   Found {len(questions)} questions")
    
    # Update all questions to use First Form ID
    for q in questions:
        if q.get("form_id") != first_form_id:
            print(f"   - Updating: {q.get('prompt', 'N/A')[:30]}...")
            conn.table("form_questions").update({"form_id": first_form_id}).eq("id", q["id"]).execute()
    
    print("  ✓ All questions updated!")
    
    # Step 4: Verify
    updated_q = conn.table("form_questions").select("*").eq("form_id", first_form_id).eq("admin_email", admin_email).execute()
    print(f"\n✅ Done! 'First Form' now has {len(updated_q.data or [])} questions")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
