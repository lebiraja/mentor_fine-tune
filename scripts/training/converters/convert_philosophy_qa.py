"""
Convert Strix Philosophy QA dataset to ClarityMentor format.

Source: hf_datasets/sayhan/strix-philosophy-qa/data-00000-of-00001.arrow
Format: category, question, answer

Output: data/processed/philosophy_qa_processed.jsonl
"""

import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.safety_filters import SafetyFilter, QualityFilter


# Categories relevant to life mentoring
RELEVANT_CATEGORIES = {
    'ethics',
    'existentialism',
    'meaning',
    'consciousness',
    'death',
    'free will',
    'freedom',
    'happiness',
    'virtue',
    'stoicism',
    'humanism',
    'absurdism',
    'nihilism',
    'morality',
    'suffering',
    'identity',
    'self',
    'mind',
    'emotion',
    'reason',
    'wisdom',
    'love',
    'friendship',
    'justice',
    'courage',
    'purpose',
    'life',
    'human nature',
    'values',
    'choice',
    'responsibility',
    'authenticity',
}

# User message prefixes to make questions more natural
USER_PREFIXES = [
    "I've been thinking about ",
    "I'm curious about ",
    "Can you help me understand ",
    "I've been wondering about ",
    "What's your perspective on ",
    "I'd like to explore the idea of ",
    "",  # No prefix (use question as-is)
]


def load_system_prompt(config_path: Path) -> str:
    """Load the ClarityMentor system prompt."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def load_arrow_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from an Arrow file."""
    try:
        import pyarrow as pa
    except ImportError:
        raise ImportError("pyarrow is required. Install with: pip install pyarrow")

    print(f"Loading {file_path}...")

    # Try reading as IPC file
    try:
        with pa.memory_map(str(file_path), 'r') as source:
            reader = pa.ipc.open_file(source)
            table = reader.read_all()
    except Exception:
        # Fallback: try as stream
        with open(file_path, 'rb') as f:
            reader = pa.ipc.open_stream(f)
            table = reader.read_all()

    # Convert to list of dicts
    df_dict = table.to_pydict()
    num_rows = len(df_dict.get('question', df_dict.get('category', [])))

    data = []
    for i in range(num_rows):
        row = {key: df_dict[key][i] for key in df_dict}
        data.append(row)

    return data


def is_relevant_category(category: str, relevant_set: Set[str]) -> bool:
    """Check if category is relevant for life mentoring."""
    if not category:
        return False

    category_lower = category.lower().strip()

    # Direct match
    if category_lower in relevant_set:
        return True

    # Partial match
    for relevant in relevant_set:
        if relevant in category_lower or category_lower in relevant:
            return True

    return False


def format_user_message(question: str) -> str:
    """Format question as a natural user message."""
    question = question.strip()

    # If question already starts with a common phrase, use as-is
    lower_q = question.lower()
    if any(lower_q.startswith(p) for p in ['what', 'why', 'how', 'is', 'are', 'can', 'do', 'does']):
        # Sometimes add a prefix, sometimes not
        if random.random() < 0.3:
            prefix = random.choice(USER_PREFIXES[:-1])  # Exclude empty prefix
            # Remove the question mark for prefixed versions
            if question.endswith('?'):
                topic = question[:-1].lower()
            else:
                topic = question.lower()
            return f"{prefix}{topic}?"
        return question

    # For statement-like questions, add a prefix
    prefix = random.choice(USER_PREFIXES)
    if prefix:
        return f"{prefix}{question.lower().rstrip('?')}?"
    return question


def convert_qa_pair(
    row: Dict[str, Any],
    system_prompt: str,
    safety_filter: SafetyFilter,
    quality_filter: QualityFilter,
    min_answer_length: int = 100,
    max_answer_length: int = 1500,
) -> Optional[Dict[str, Any]]:
    """
    Convert a single Q/A pair to ClarityMentor format.

    Args:
        row: Dictionary with category, question, answer
        system_prompt: The system prompt to prepend
        safety_filter: SafetyFilter instance
        quality_filter: QualityFilter instance
        min_answer_length: Minimum answer length in characters
        max_answer_length: Maximum answer length in characters

    Returns:
        Converted conversation dict or None if filtered out
    """
    question = row.get('question', '').strip()
    answer = row.get('answer', '').strip()
    category = row.get('category', '').strip()

    # Filter by length
    if len(answer) < min_answer_length:
        return None
    if len(answer) > max_answer_length:
        return None
    if len(question) < 10:
        return None

    # Safety check
    safe, _ = safety_filter.is_safe(answer)
    if not safe:
        return None

    # Format user message
    user_content = format_user_message(question)

    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": answer}
    ]

    return {
        "messages": messages,
        "metadata": {
            "source": "strix_philosophy_qa",
            "category": category,
        }
    }


def process_dataset(
    input_file: Path,
    output_file: Path,
    config_dir: Path,
    max_samples: Optional[int] = 20000,
    filter_categories: bool = True,
) -> Dict[str, int]:
    """
    Process the philosophy QA dataset.

    Args:
        input_file: Path to Arrow file
        output_file: Output JSONL file path
        config_dir: Directory containing system_prompt.txt
        max_samples: Maximum number of samples to include
        filter_categories: Whether to filter by relevant categories

    Returns:
        Statistics dictionary
    """
    data = load_arrow_file(input_file)
    print(f"Loaded {len(data)} Q/A pairs")

    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")

    safety_filter = SafetyFilter(use_detoxify=False)
    quality_filter = QualityFilter(min_assistant_length=100, max_assistant_length=1500)

    stats = {
        "total_input": len(data),
        "filtered_category": 0,
        "filtered_length": 0,
        "filtered_safety": 0,
        "written": 0,
    }

    # First pass: filter by category if enabled
    if filter_categories:
        filtered_data = []
        for row in data:
            category = row.get('category', '')
            if is_relevant_category(category, RELEVANT_CATEGORIES):
                filtered_data.append(row)
            else:
                stats["filtered_category"] += 1
        data = filtered_data
        print(f"After category filtering: {len(data)} Q/A pairs")

    # Shuffle for variety
    random.seed(42)
    random.shuffle(data)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, row in enumerate(data):
            if max_samples and stats["written"] >= max_samples:
                break

            result = convert_qa_pair(
                row=row,
                system_prompt=system_prompt,
                safety_filter=safety_filter,
                quality_filter=quality_filter,
            )

            if result is None:
                stats["filtered_length"] += 1
                continue

            f.write(json.dumps(result, ensure_ascii=False) + '\n')
            stats["written"] += 1

            if (i + 1) % 5000 == 0:
                print(f"Processed {i + 1}, written {stats['written']}")

    print(f"\nConversion complete!")
    print(f"  Total input: {stats['total_input']}")
    print(f"  Filtered by category: {stats['filtered_category']}")
    print(f"  Filtered by length/safety: {stats['filtered_length']}")
    print(f"  Written: {stats['written']}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Strix Philosophy QA to ClarityMentor format"
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/hf_datasets/sayhan/strix-philosophy-qa/data-00000-of-00001.arrow"),
        help="Path to Arrow file"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/processed/philosophy_qa_processed.jsonl"),
        help="Output JSONL file"
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/config"),
        help="Config directory containing system_prompt.txt"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=20000,
        help="Maximum number of samples to process"
    )
    parser.add_argument(
        "--no-category-filter",
        action="store_true",
        help="Disable category filtering"
    )

    args = parser.parse_args()

    # Check if file exists
    if not args.input_file.exists():
        # Try to find the arrow file
        search_dir = args.input_file.parent
        if search_dir.exists():
            arrow_files = list(search_dir.glob("*.arrow"))
            if arrow_files:
                args.input_file = arrow_files[0]
                print(f"Found arrow file: {args.input_file}")

    stats = process_dataset(
        input_file=args.input_file,
        output_file=args.output_file,
        config_dir=args.config_dir,
        max_samples=args.max_samples,
        filter_categories=not args.no_category_filter,
    )

    # Save stats
    stats_file = args.output_file.parent / "philosophy_qa_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
