"""
One-click deploy to Hugging Face Spaces.
Step 1: Opens the correct browser page for creating a Write token
Step 2: Asks you to paste the token
Step 3: Uploads everything automatically
"""
import webbrowser
import os
import time

# Step 1: Open the browser to create a Write token
print("=" * 55)
print("  STEP 1: Creating a Write Access Token")
print("=" * 55)
print()
print("  Opening browser to create a NEW Write token...")
print("  Please follow these steps in the browser:")
print()
print("  1. Token name: type  deploy")
print("  2. Token type: select  WRITE  (very important!)")
print("  3. Click  Create token")
print("  4. Copy the hf_... string shown")
print()

# Open the SIMPLE token creation page (not fine-grained)
webbrowser.open("https://huggingface.co/settings/tokens/new?tokenType=write")
time.sleep(2)

# Step 2: Ask for the token in terminal
print("=" * 55)
print("  STEP 2: Paste your token below")
print("=" * 55)
print()
token = input("  Paste your token here >>> ").strip()

if not token:
    print("\n  No token entered. Cancelled.")
    exit(1)

# Step 3: Upload all files
print()
print("=" * 55)
print("  STEP 3: Uploading files to Hugging Face...")
print("=" * 55)
print()

from huggingface_hub import HfApi

REPO_ID = "twdavidtw/victor-snake-battle"
api = HfApi(token=token)

FILES = [
    "app.py",
    "requirements.txt",
    "Dockerfile",
    "README.md",
    "templates/index.html",
    "static/style.css",
    "static/script.js",
    "static/background.wav",
    "static/score.wav",
]

base_dir = os.path.dirname(os.path.abspath(__file__))
success_count = 0
fail_count = 0

for f in FILES:
    full_path = os.path.join(base_dir, f)
    if not os.path.exists(full_path):
        print(f"  SKIP  {f} (file not found)")
        continue
    try:
        api.upload_file(
            path_or_fileobj=full_path,
            path_in_repo=f,
            repo_id=REPO_ID,
            repo_type="space",
        )
        print(f"  OK    {f}")
        success_count += 1
    except Exception as e:
        print(f"  FAIL  {f} -> {e}")
        fail_count += 1

print()
print("=" * 55)
if fail_count == 0:
    print(f"  ALL {success_count} FILES UPLOADED SUCCESSFULLY!")
    print(f"  Your game: https://huggingface.co/spaces/{REPO_ID}")
else:
    print(f"  {success_count} OK, {fail_count} FAILED")
    print(f"  Make sure your token has WRITE permission!")
print("=" * 55)
