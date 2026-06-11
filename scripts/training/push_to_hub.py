#!/usr/bin/env python3
"""
Push ClarityMentor LoRA model to Hugging Face Hub.

Usage:
    python push_to_hub.py --repo-name claritymentor-lora
    python push_to_hub.py --repo-name claritymentor-lora --private
"""

import argparse
from pathlib import Path
from huggingface_hub import HfApi, create_repo

def main():
    parser = argparse.ArgumentParser(description="Push ClarityMentor model to Hugging Face Hub")
    parser.add_argument(
        "--repo-name",
        type=str,
        default="claritymentor-lora",
        help="Name of the repository on Hugging Face"
    )
    parser.add_argument(
        "--username",
        type=str,
        help="Your Hugging Face username (if not provided, will use your account)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make the repository private"
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("/home/lebi/projects/mentor/models/claritymentor-lora/final"),
        help="Path to the local model directory"
    )

    args = parser.parse_args()

    # Get HF API
    api = HfApi()

    # Get current user info
    try:
        user_info = api.whoami()
        username = args.username or user_info.get('name', 'unknown')
        print(f"Logged in as: {username}")
    except Exception as e:
        print(f"Error: Could not get user info. Make sure you're logged in with 'hf auth login'")
        print(f"Details: {e}")
        return

    # Create repository URL
    repo_id = f"{username}/{args.repo_name}"
    repo_url = f"https://huggingface.co/{repo_id}"

    print(f"\n{'='*60}")
    print(f"Pushing model to Hugging Face")
    print(f"{'='*60}")
    print(f"Repository: {repo_id}")
    print(f"URL: {repo_url}")
    print(f"Private: {args.private}")
    print(f"Model path: {args.model_path}")
    print(f"{'='*60}\n")

    # Create repository if it doesn't exist
    try:
        print("Creating/updating repository...")
        create_repo(
            repo_id=repo_id,
            repo_type="model",
            private=args.private,
            exist_ok=True
        )
        print(f"✓ Repository ready: {repo_url}")
    except Exception as e:
        print(f"✗ Error creating repository: {e}")
        return

    # Upload files
    try:
        print("\nUploading model files...")
        api.upload_folder(
            folder_path=str(args.model_path),
            repo_id=repo_id,
            repo_type="model",
            multi_commits=True,
            multi_commits_verbose=True,
        )
        print(f"✓ Model uploaded successfully!")
    except Exception as e:
        print(f"✗ Error uploading model: {e}")
        return

    # Upload README
    readme_path = args.model_path / "README.md"
    if readme_path.exists():
        try:
            print("\nUpdating README on hub...")
            api.upload_file(
                path_or_fileobj=str(readme_path),
                path_in_repo="README.md",
                repo_id=repo_id,
                repo_type="model",
            )
            print("✓ README updated")
        except Exception as e:
            print(f"Warning: Could not update README: {e}")

    print(f"\n{'='*60}")
    print(f"✓ Model successfully pushed to Hugging Face!")
    print(f"{'='*60}")
    print(f"\nView your model: {repo_url}")
    print(f"\nTo use it:")
    print(f"  from peft import PeftModel")
    print(f"  from transformers import AutoModelForCausalLM, AutoTokenizer")
    print(f"  ")
    print(f"  base_model = 'Qwen/Qwen2.5-1.5B-Instruct'")
    print(f"  model = AutoModelForCausalLM.from_pretrained(base_model, load_in_4bit=True)")
    print(f"  model = PeftModel.from_pretrained(model, '{repo_id}')")
    print(f"  tokenizer = AutoTokenizer.from_pretrained(base_model)")

if __name__ == "__main__":
    main()
