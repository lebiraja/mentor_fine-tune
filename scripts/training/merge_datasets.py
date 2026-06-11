"""
Merge all processed datasets into final training and evaluation sets.

Combines:
- empathetic_llm_processed.jsonl (25%)
- philosophy_qa_processed.jsonl (20%)
- counseling_processed.jsonl (20%)
- reddit_processed.jsonl (20%)
- quotes_advice_processed.jsonl (10%)
- conversation_starters_processed.jsonl (5%)

Output:
- data/final/claritymentor_train.jsonl
- data/final/claritymentor_eval.jsonl
"""

import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.deduplication import deduplicate_jsonl


# Default mixing ratios
DEFAULT_RATIOS = {
    "empathetic_llm_processed.jsonl": 0.25,
    "philosophy_qa_processed.jsonl": 0.20,
    "counseling_processed.jsonl": 0.20,
    "reddit_processed.jsonl": 0.20,
    "quotes_advice_processed.jsonl": 0.10,
    "conversation_starters_processed.jsonl": 0.05,
}


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file."""
    data = []
    if not file_path.exists():
        print(f"  Warning: {file_path} not found")
        return data

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return data


def sample_dataset(
    data: List[Dict[str, Any]],
    target_count: int,
    source_name: str,
) -> List[Dict[str, Any]]:
    """
    Sample from a dataset to meet target count.

    If dataset has fewer items than target, use all items.
    If dataset has more items, randomly sample.
    """
    if len(data) <= target_count:
        print(f"  {source_name}: using all {len(data)} samples (target: {target_count})")
        return data.copy()

    sampled = random.sample(data, target_count)
    print(f"  {source_name}: sampled {len(sampled)} from {len(data)} (target: {target_count})")
    return sampled


def validate_conversation(conv: Dict[str, Any]) -> bool:
    """Validate that a conversation has the required structure."""
    messages = conv.get('messages', [])

    if not messages:
        return False

    # Must have at least system + user + assistant
    if len(messages) < 3:
        return False

    # First message should be system
    if messages[0].get('role') != 'system':
        return False

    # Must have at least one user and one assistant message
    roles = [m.get('role') for m in messages]
    if 'user' not in roles or 'assistant' not in roles:
        return False

    # All messages must have content
    for msg in messages:
        if not msg.get('content', '').strip():
            return False

    return True


def merge_datasets(
    processed_dir: Path,
    output_dir: Path,
    total_samples: int = 50000,
    eval_ratio: float = 0.05,
    ratios: Optional[Dict[str, float]] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Merge all processed datasets according to specified ratios.

    Args:
        processed_dir: Directory containing processed JSONL files
        output_dir: Directory for output files
        total_samples: Target total number of training samples
        eval_ratio: Fraction to hold out for evaluation
        ratios: Dictionary mapping filename to ratio (must sum to 1.0)
        seed: Random seed for reproducibility

    Returns:
        Statistics dictionary
    """
    random.seed(seed)

    if ratios is None:
        ratios = DEFAULT_RATIOS

    # Validate ratios sum to 1.0
    ratio_sum = sum(ratios.values())
    if abs(ratio_sum - 1.0) > 0.01:
        print(f"Warning: Ratios sum to {ratio_sum}, normalizing...")
        ratios = {k: v / ratio_sum for k, v in ratios.items()}

    stats = {
        "target_total": total_samples,
        "eval_ratio": eval_ratio,
        "sources": {},
        "total_loaded": 0,
        "total_after_validation": 0,
        "total_after_dedup": 0,
        "train_count": 0,
        "eval_count": 0,
    }

    all_data = []

    print(f"\nLoading datasets from {processed_dir}...")
    print(f"Target total: {total_samples} samples\n")

    for filename, ratio in ratios.items():
        file_path = processed_dir / filename
        target_count = int(total_samples * ratio)

        print(f"Loading {filename}...")
        data = load_jsonl(file_path)

        stats["sources"][filename] = {
            "loaded": len(data),
            "ratio": ratio,
            "target": target_count,
        }

        if data:
            # Validate conversations
            valid_data = [d for d in data if validate_conversation(d)]
            print(f"  Valid conversations: {len(valid_data)} / {len(data)}")

            # Sample according to ratio
            sampled = sample_dataset(valid_data, target_count, filename)
            stats["sources"][filename]["sampled"] = len(sampled)

            all_data.extend(sampled)
            stats["total_loaded"] += len(data)
            stats["total_after_validation"] += len(valid_data)

    print(f"\nTotal collected: {len(all_data)}")

    # Deduplicate
    print("\nDeduplicating...")
    deduped_data, dedup_stats = deduplicate_jsonl(all_data, threshold=0.85)
    stats["total_after_dedup"] = len(deduped_data)
    stats["deduplication"] = dedup_stats
    print(f"After deduplication: {len(deduped_data)} (removed {dedup_stats['removed']})")

    # Shuffle
    random.shuffle(deduped_data)

    # Split into train/eval
    eval_count = int(len(deduped_data) * eval_ratio)
    train_count = len(deduped_data) - eval_count

    eval_data = deduped_data[:eval_count]
    train_data = deduped_data[eval_count:]

    stats["train_count"] = len(train_data)
    stats["eval_count"] = len(eval_data)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write training set
    train_file = output_dir / "claritymentor_train.jsonl"
    print(f"\nWriting training set to {train_file}...")
    with open(train_file, 'w', encoding='utf-8') as f:
        for record in train_data:
            # Remove metadata for training (optional, keeps file smaller)
            train_record = {"messages": record["messages"]}
            f.write(json.dumps(train_record, ensure_ascii=False) + '\n')
    print(f"  Written: {len(train_data)} samples")

    # Write evaluation set
    eval_file = output_dir / "claritymentor_eval.jsonl"
    print(f"Writing evaluation set to {eval_file}...")
    with open(eval_file, 'w', encoding='utf-8') as f:
        for record in eval_data:
            # Keep metadata for evaluation analysis
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"  Written: {len(eval_data)} samples")

    # Calculate source distribution in final dataset
    source_dist = defaultdict(int)
    for record in train_data + eval_data:
        source = record.get('metadata', {}).get('source', 'unknown')
        source_dist[source] += 1

    stats["final_distribution"] = dict(source_dist)

    print(f"\nFinal dataset statistics:")
    print(f"  Training samples: {stats['train_count']}")
    print(f"  Evaluation samples: {stats['eval_count']}")
    print(f"\nSource distribution:")
    for source, count in sorted(source_dist.items(), key=lambda x: -x[1]):
        pct = count / (stats['train_count'] + stats['eval_count']) * 100
        print(f"    {source}: {count} ({pct:.1f}%)")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge processed datasets into final training/eval sets"
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/processed"),
        help="Directory containing processed JSONL files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/final"),
        help="Directory for output files"
    )
    parser.add_argument(
        "--total-samples",
        type=int,
        default=50000,
        help="Target total number of samples"
    )
    parser.add_argument(
        "--eval-ratio",
        type=float,
        default=0.05,
        help="Fraction to hold out for evaluation"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    stats = merge_datasets(
        processed_dir=args.processed_dir,
        output_dir=args.output_dir,
        total_samples=args.total_samples,
        eval_ratio=args.eval_ratio,
        seed=args.seed,
    )

    # Save stats
    stats_file = args.output_dir / "merge_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\nStats saved to {stats_file}")


if __name__ == "__main__":
    main()
