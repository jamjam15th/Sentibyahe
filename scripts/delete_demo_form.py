#!/usr/bin/env python3
"""
Delete the demo form if it exists.

Usage:
    python scripts/delete_demo_form.py --email your-email@example.com
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
parser = argparse.ArgumentParser(description="Delete the demo form")
parser.add_argument("--email", required=True, help="Your admin email")
args = parser.parse_args()

admin_email = args.email
demo_form_id = "demo-form-001"

print(f"🗑️  Deleting demo form '{demo_form_id}' for {admin_email}...")

try:
    # Delete responses
    conn.table("form_responses").delete().eq("form_id", demo_form_id).eq("admin_email", admin_email).execute()
    print("  ✓ Deleted responses")
    
    # Delete questions
    conn.table("form_questions").delete().eq("form_id", demo_form_id).eq("admin_email", admin_email).execute()
    print("  ✓ Deleted questions")
    
    # Delete form metadata
    conn.table("form_meta").delete().eq("form_id", demo_form_id).eq("admin_email", admin_email).execute()
    print("  ✓ Deleted form metadata")
    
    # Delete form
    conn.table("form_list").delete().eq("id", demo_form_id).execute()
    print("  ✓ Deleted form")
    
    print("\n✅ Demo form deleted successfully!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)
