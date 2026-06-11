"""
Convert Reddit dataset to ClarityMentor format with heavy safety filtering.

Source: reddit_dataset_170/ (requires git lfs pull first)
Format: Parquet files with text, label, dataType, communityName, etc.

Output: data/processed/reddit_processed.jsonl

IMPORTANT: Run `cd reddit_dataset_170 && git lfs pull` before using this script.
"""

import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.safety_filters import SafetyFilter, QualityFilter


# Subreddits relevant for life mentoring
RELEVANT_SUBREDDITS = {
    'relationship_advice',
    'relationships',
    'amitheasshole',
    'aitah',
    'amiwrong',
    'decidingtobebetter',
    'selfimprovement',
    'socialskills',
    'advice',
    'needadvice',
    'internetparents',
    'askmenover30',
    'askwomenover30',
    'lifeadvice',
    'careerguidance',
    'findapath',
    'lonely',
    'depression',  # Requires extra safety filtering
    'anxiety',  # Requires extra safety filtering
    'offmychest',
    'trueoffmychest',
    'confessions',
    'self',
    'mentalhealth',  # Requires extra safety filtering
}

# Subreddits to explicitly exclude
EXCLUDED_SUBREDDITS = {
    'politics',
    'wallstreetbets',
    'cryptocurrency',
    'gaming',
    'memes',
    'funny',
    'pics',
    'videos',
    'news',
    'worldnews',
    'conservative',
    'liberal',
    'conspiracy',
    'drugs',
    'trees',
    'sex',
    'gonewild',
    'roastme',
    'suicidewatch',  # Too sensitive, needs professional help
}


def load_system_prompt(config_path: Path) -> str:
    """Load the ClarityMentor system prompt."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def check_git_lfs_status(data_dir: Path) -> bool:
    """Check if Git LFS files have been pulled."""
    parquet_files = list(data_dir.glob("data/*.parquet"))

    if not parquet_files:
        print("No parquet files found in data/ directory.")
        print("Please run: cd reddit_dataset_170 && git lfs pull")
        return False

    # Check if files are actual data (not LFS pointers)
    for pf in parquet_files[:1]:  # Check first file
        try:
            with open(pf, 'rb') as f:
                header = f.read(4)
                # Parquet files start with 'PAR1'
                if header != b'PAR1':
                    print(f"File {pf.name} appears to be a Git LFS pointer, not actual data.")
                    print("Please run: cd reddit_dataset_170 && git lfs pull")
                    return False
        except Exception as e:
            print(f"Error checking file: {e}")
            return False

    return True


def load_parquet_files(data_dir: Path, max_files: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load parquet files from the data directory."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError("pyarrow is required. Install with: pip install pyarrow")

    all_data = []
    parquet_files = sorted(data_dir.glob("data/*.parquet"))

    if max_files:
        parquet_files = parquet_files[:max_files]

    for pf in parquet_files:
        print(f"Loading {pf.name}...")
        try:
            table = pq.read_table(pf)
            df_dict = table.to_pydict()

            num_rows = len(df_dict.get('text', []))
            for i in range(num_rows):
                row = {key: df_dict[key][i] for key in df_dict}
                all_data.append(row)

            print(f"  Loaded {num_rows} rows")

        except Exception as e:
            print(f"  Error loading {pf.name}: {e}")
            continue

    return all_data


def is_relevant_subreddit(community: str) -> bool:
    """Check if subreddit is relevant for life mentoring."""
    if not community:
        return False

    community_lower = community.lower().strip()

    # Remove r/ prefix if present
    if community_lower.startswith('r/'):
        community_lower = community_lower[2:]

    # Check exclusions first
    if community_lower in EXCLUDED_SUBREDDITS:
        return False

    # Check inclusions
    return community_lower in RELEVANT_SUBREDDITS


def generate_mentor_response(text: str, safety_filter: SafetyFilter) -> Optional[str]:
    """
    Generate a placeholder mentor-style response.

    Since we're not using LLM rewriting, we'll create template-based responses
    that demonstrate the expected format. These will be mixed with other datasets
    that have proper responses.
    """
    # Detect if user needs professional help
    if safety_filter.requires_professional_help(text):
        return (
            "I hear that you're going through something very difficult. "
            "What you're feeling is valid, and I want you to know that support is available. "
            "While I can offer perspective, a mental health professional would be much better equipped "
            "to help you work through this. Please consider reaching out to a counselor, therapist, "
            "or a crisis helpline in your area. You don't have to face this alone."
        )

    # For now, return None - we'll primarily use this dataset for user messages
    # paired with other dataset's assistant responses, or skip assistant generation
    return None


def convert_reddit_post(
    row: Dict[str, Any],
    system_prompt: str,
    safety_filter: SafetyFilter,
    quality_filter: QualityFilter,
    min_text_length: int = 100,
    max_text_length: int = 2000,
) -> Optional[Dict[str, Any]]:
    """
    Convert a Reddit post to ClarityMentor format.

    Args:
        row: Dictionary with text, communityName, dataType, etc.
        system_prompt: System prompt to prepend
        safety_filter: SafetyFilter instance
        quality_filter: QualityFilter instance
        min_text_length: Minimum post length
        max_text_length: Maximum post length

    Returns:
        Converted conversation dict or None if filtered
    """
    text = row.get('text', '').strip()
    community = row.get('communityName', '')
    data_type = row.get('dataType', '')

    # Only use posts (not comments) as they contain full context
    if data_type != 'post':
        return None

    # Check subreddit relevance
    if not is_relevant_subreddit(community):
        return None

    # Length filtering
    if len(text) < min_text_length or len(text) > max_text_length:
        return None

    # Safety filtering
    safe, reason = safety_filter.is_safe(text)
    if not safe:
        return None

    # Generate response (may return None)
    response = generate_mentor_response(text, safety_filter)

    if response is None:
        # For posts without generated responses, create a clarifying response
        # This teaches the model to ask questions for context
        response = create_clarifying_response(text)

    if not response:
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
        {"role": "assistant", "content": response}
    ]

    return {
        "messages": messages,
        "metadata": {
            "source": "reddit",
            "subreddit": community,
        }
    }


def create_clarifying_response(text: str) -> str:
    """
    Create a clarifying response that asks for more context.
    This teaches the model Socratic questioning.
    """
    # Detect the general topic/emotion
    text_lower = text.lower()

    if any(word in text_lower for word in ['relationship', 'partner', 'boyfriend', 'girlfriend', 'husband', 'wife', 'dating']):
        return (
            "I can see you're dealing with a challenging relationship situation. "
            "Before I offer my perspective, I'd like to understand better:\n\n"
            "1. How long have you been in this situation?\n"
            "2. Have you been able to communicate your feelings directly?\n"
            "3. What outcome would you ideally want?\n\n"
            "Understanding these details will help me give you more useful guidance."
        )

    elif any(word in text_lower for word in ['job', 'career', 'work', 'boss', 'coworker', 'fired', 'quit']):
        return (
            "Career decisions can be some of the most impactful choices we make. "
            "To help you think through this clearly, I have some questions:\n\n"
            "1. What are your core priorities right now (stability, growth, meaning)?\n"
            "2. What would success look like for you in this situation?\n"
            "3. What's holding you back from taking action?\n\n"
            "Let's explore this together once I understand your perspective better."
        )

    elif any(word in text_lower for word in ['family', 'parent', 'mother', 'father', 'sibling', 'sister', 'brother']):
        return (
            "Family dynamics are complex, and it's clear this matters to you. "
            "Help me understand more:\n\n"
            "1. What specific outcome are you hoping for?\n"
            "2. Have you tried addressing this directly?\n"
            "3. Are there boundaries you need to establish or reinforce?\n\n"
            "With more context, I can offer a more grounded perspective."
        )

    elif any(word in text_lower for word in ['anxious', 'anxiety', 'worried', 'stressed', 'overwhelmed']):
        return (
            "It sounds like you're carrying a heavy mental load right now. "
            "I want to understand your situation better:\n\n"
            "1. Is this a recent feeling or something ongoing?\n"
            "2. Are there specific triggers you've identified?\n"
            "3. What coping strategies have you tried so far?\n\n"
            "Understanding these will help me offer more practical suggestions."
        )

    elif any(word in text_lower for word in ['lonely', 'alone', 'isolated', 'friend', 'social']):
        return (
            "Feeling disconnected is genuinely difficult. "
            "To offer you useful perspective:\n\n"
            "1. Is this a new feeling or something you've struggled with for a while?\n"
            "2. What kind of connections are you seeking?\n"
            "3. What has prevented you from making those connections?\n\n"
            "Let's work through this together."
        )

    else:
        # Generic clarifying response
        return (
            "Thank you for sharing this. Before I offer my perspective, "
            "I'd like to understand a few things:\n\n"
            "1. What specific aspect of this situation troubles you most?\n"
            "2. What outcome would you ideally want?\n"
            "3. What have you already tried or considered?\n\n"
            "These details will help me give you more grounded guidance."
        )


def process_dataset(
    data_dir: Path,
    output_file: Path,
    config_dir: Path,
    max_samples: int = 15000,
    max_parquet_files: Optional[int] = None,
) -> Dict[str, int]:
    """
    Process the Reddit dataset.

    Args:
        data_dir: Directory containing reddit_dataset_170
        output_file: Output JSONL file path
        config_dir: Directory containing system_prompt.txt
        max_samples: Maximum number of samples to include
        max_parquet_files: Limit number of parquet files to process

    Returns:
        Statistics dictionary
    """
    # Check Git LFS status
    if not check_git_lfs_status(data_dir):
        return {"error": "Git LFS files not pulled"}

    print(f"Loading data from {data_dir}...")
    data = load_parquet_files(data_dir, max_files=max_parquet_files)
    print(f"Loaded {len(data)} total rows")

    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")

    safety_filter = SafetyFilter(use_detoxify=True)  # Use full safety filtering
    quality_filter = QualityFilter()

    stats = {
        "total_input": len(data),
        "filtered_subreddit": 0,
        "filtered_type": 0,
        "filtered_length": 0,
        "filtered_safety": 0,
        "written": 0,
        "subreddit_counts": {},
    }

    results = []

    print("\nProcessing posts...")
    for i, row in enumerate(data):
        if len(results) >= max_samples:
            break

        result = convert_reddit_post(
            row=row,
            system_prompt=system_prompt,
            safety_filter=safety_filter,
            quality_filter=quality_filter,
        )

        if result is not None:
            results.append(result)

            # Track subreddit distribution
            subreddit = result['metadata'].get('subreddit', 'unknown')
            stats["subreddit_counts"][subreddit] = stats["subreddit_counts"].get(subreddit, 0) + 1

        if (i + 1) % 50000 == 0:
            print(f"  Processed {i + 1}, collected {len(results)}")

    # Shuffle results
    random.seed(42)
    random.shuffle(results)

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    stats["written"] = len(results)

    print(f"\nConversion complete!")
    print(f"  Total input: {stats['total_input']}")
    print(f"  Written: {stats['written']}")
    print(f"\nSubreddit distribution:")
    for sub, count in sorted(stats["subreddit_counts"].items(), key=lambda x: -x[1])[:10]:
        print(f"    {sub}: {count}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Reddit dataset to ClarityMentor format"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/reddit_dataset_170"),
        help="Directory containing reddit dataset"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/processed/reddit_processed.jsonl"),
        help="Output JSONL file"
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/config"),
        help="Config directory"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=15000,
        help="Maximum number of samples"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of parquet files to process"
    )

    args = parser.parse_args()

    stats = process_dataset(
        data_dir=args.data_dir,
        output_file=args.output_file,
        config_dir=args.config_dir,
        max_samples=args.max_samples,
        max_parquet_files=args.max_files,
    )

    # Save stats
    stats_file = args.output_file.parent / "reddit_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
