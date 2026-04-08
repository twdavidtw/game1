from huggingface_hub import HfApi
import os

TOKEN = "PUT_YOUR_TOKEN_HERE"
REPO_ID = "twdavidtw/victor-snake-battle"

api = HfApi(token=TOKEN)
base_dir = r"d:\AI"

print("Uploading entire project folder to Hugging Face Space...")
print("This may take a minute, please wait...")
print()

try:
    api.upload_folder(
        folder_path=base_dir,
        repo_id=REPO_ID,
        repo_type="space",
        ignore_patterns=[
            ".git/*", ".gitignore", "build/*", "dist/*",
            "*.spec", "*.zip", "*.py.bak",
            "deploy_hf.ps1", "deploy_hf_api.py", "deploy_now.py",
            "gen_sounds.py", "snake.py",
        ],
    )
    print("=" * 55)
    print("  DEPLOY SUCCESS!")
    print(f"  URL: https://huggingface.co/spaces/{REPO_ID}")
    print("=" * 55)
except Exception as e:
    print(f"FAILED: {e}")
