"""
Convert Empathetic Dialogues LLM dataset to ClarityMentor format.

Source: empathetic_dialogues_llm/data/*.parquet
Format: Already has conversations with user/assistant roles

Output: data/processed/empathetic_llm_processed.jsonl
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.safety_filters import SafetyFilter, QualityFilter


def load_system_prompt(config_path: Path) -> str:
    """Load the ClarityMentor system prompt."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def load_parquet_files(data_dir: Path) -> List[Dict[str, Any]]:
    """Load all parquet files from the data directory."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError("pyarrow is required. Install with: pip install pyarrow")

    all_data = []
    parquet_files = list(data_dir.glob("*.parquet"))

    for pq_file in parquet_files:
        print(f"Loading {pq_file.name}...")
        table = pq.read_table(pq_file)
        df_dict = table.to_pydict()

        # Convert to list of dicts
        num_rows = len(df_dict.get('conv_id', []))
        for i in range(num_rows):
            row = {key: df_dict[key][i] for key in df_dict}
            all_data.append(row)

    return all_data


def convert_conversation(
    row: Dict[str, Any],
    system_prompt: str,
    safety_filter: SafetyFilter,
    quality_filter: QualityFilter,
    include_emotion_context: bool = True,
    min_turns: int = 2,
    max_turns: int = 12,
) -> Optional[Dict[str, Any]]:
    """
    Convert a single conversation row to ClarityMentor format.

    Args:
        row: Dictionary with conv_id, situation, emotion, conversations
        system_prompt: The system prompt to prepend
        safety_filter: SafetyFilter instance
        quality_filter: QualityFilter instance
        include_emotion_context: Whether to add emotion context to system prompt
        min_turns: Minimum number of turns required (user + assistant messages)
        max_turns: Maximum number of turns allowed

    Returns:
        Converted conversation dict or None if filtered out
    """
    conversations = row.get('conversations', [])
    emotion = row.get('emotion', '')
    situation = row.get('situation', '')

    # Skip empty conversations
    if not conversations:
        return None

    # Limit max turns
    if len(conversations) > max_turns:
        conversations = conversations[:max_turns]

    # Build system message with optional emotion context
    if include_emotion_context and emotion:
        system_content = f"{system_prompt}\n\n[Context: User is feeling {emotion}]"
    else:
        system_content = system_prompt

    # Build messages list
    messages = [{"role": "system", "content": system_content}]

    for turn in conversations:
        role = turn.get('role', '')
        content = turn.get('content', '').strip() if turn.get('content') else ''

        # Skip empty messages
        if not content:
            continue

        # Validate role
        if role not in ['user', 'assistant']:
            continue

        messages.append({"role": role, "content": content})

    # Ensure we have at least one user and one assistant message
    roles = [m['role'] for m in messages]
    if 'user' not in roles or 'assistant' not in roles:
        return None

    # Count non-system turns
    non_system = [m for m in messages if m['role'] != 'system']
    if len(non_system) < min_turns:
        return None

    # Ensure last non-system message is from assistant (for training)
    # If it ends with user, that's OK - it's a natural conversation
    # But we prefer conversations that end with assistant
    # Let's keep both for diversity

    # Safety check on the full conversation
    all_text = " ".join([m['content'] for m in messages])
    safe, reason = safety_filter.is_safe(all_text)
    if not safe:
        return None

    return {
        "messages": messages,
        "metadata": {
            "source": "empathetic_dialogues_llm",
            "emotion": emotion,
            "conv_id": row.get('conv_id', ''),
        }
    }


def process_dataset(
    input_dir: Path,
    output_file: Path,
    config_dir: Path,
    max_samples: Optional[int] = None,
) -> Dict[str, int]:
    """
    Process the entire dataset.

    Args:
        input_dir: Directory containing parquet files
        output_file: Output JSONL file path
        config_dir: Directory containing system_prompt.txt
        max_samples: Optional limit on number of samples

    Returns:
        Statistics dictionary
    """
    print(f"Loading data from {input_dir}...")
    data = load_parquet_files(input_dir)
    print(f"Loaded {len(data)} conversations")

    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")

    safety_filter = SafetyFilter(use_detoxify=False)  # Fast mode
    quality_filter = QualityFilter()

    stats = {
        "total_input": len(data),
        "processed": 0,
        "filtered_short": 0,
        "filtered_safety": 0,
        "written": 0,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, row in enumerate(data):
            if max_samples and stats["written"] >= max_samples:
                break

            result = convert_conversation(
                row=row,
                system_prompt=system_prompt,
                safety_filter=safety_filter,
                quality_filter=quality_filter,
            )

            if result is None:
                stats["filtered_short"] += 1
                continue

            # Write to JSONL
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
            stats["written"] += 1
            stats["processed"] += 1

            if (i + 1) % 1000 == 0:
                print(f"Processed {i + 1}/{len(data)}, written {stats['written']}")

    print(f"\nConversion complete!")
    print(f"  Total input: {stats['total_input']}")
    print(f"  Written: {stats['written']}")
    print(f"  Filtered: {stats['filtered_short']}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Empathetic Dialogues LLM to ClarityMentor format"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/empathetic_dialogues_llm/data"),
        help="Directory containing parquet files"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/processed/empathetic_llm_processed.jsonl"),
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
        default=None,
        help="Maximum number of samples to process"
    )

    args = parser.parse_args()

    stats = process_dataset(
        input_dir=args.input_dir,
        output_file=args.output_file,
        config_dir=args.config_dir,
        max_samples=args.max_samples,
    )

    # Save stats
    stats_file = args.output_file.parent / "empathetic_llm_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
