"""
Rebuild ClarityMentor dataset with quality improvements.

Fixes:
1. Re-processes empathetic dialogues (was 0 samples due to Git LFS issue)
2. Applies NEW system prompt aligned with inference
3. Filters template responses that ask questions
4. Excludes Reddit data (96% template pollution)
5. Balances sources with target ratios
6. Generates quality report

Output:
- data/final/claritymentor_train_v2.jsonl
- data/final/claritymentor_eval_v2.jsonl
- data/final/rebuild_report.json
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
from utils.safety_filters import SafetyFilter, QualityFilter


# Target ratios (excluding Reddit)
TARGET_RATIOS = {
    "empathetic_dialogues": 0.30,  # 15,000 samples
    "philosophy_qa": 0.25,         # 12,500 samples
    "counseling": 0.25,            # 12,500 samples
    "conversation_starters": 0.10, # 5,000 samples
    "quotes_advice": 0.10,         # 5,000 samples
}

# Template patterns to filter (these ask questions, conflicting with system prompt)
TEMPLATE_PATTERNS = [
    "I can see you're dealing with",
    "Before I offer my perspective",
    "I'd like to understand",
    "Help me understand more",
    "To help you think through this",
    "Career decisions can be some of the most impactful",
    "Family dynamics are complex",
    "Feeling disconnected is genuinely difficult",
    "Thank you for sharing this. Before I offer",
    "Understanding these details will help",
]


def load_system_prompt(config_path: Path) -> str:
    """Load the current (NEW) system prompt for training."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    raise FileNotFoundError(f"System prompt not found at {prompt_file}")


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


def is_template_response(assistant_content: str) -> bool:
    """Check if response matches known template patterns."""
    for pattern in TEMPLATE_PATTERNS:
        if pattern.lower() in assistant_content.lower():
            return True
    return False


def has_question_in_response(assistant_content: str) -> bool:
    """Check if response contains a question (conflicts with 'never ask questions' rule)."""
    # Count question marks
    question_count = assistant_content.count('?')
    # Allow rhetorical questions in philosophical context (max 1)
    return question_count > 1


def filter_dataset(
    data: List[Dict[str, Any]],
    remove_templates: bool = True,
    remove_questions: bool = True,
    source_name: str = "unknown",
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter dataset for quality.

    Returns:
        Tuple of (filtered_data, stats)
    """
    stats = {
        "input": len(data),
        "removed_templates": 0,
        "removed_questions": 0,
        "removed_invalid": 0,
        "kept": 0,
    }

    filtered = []

    for entry in data:
        messages = entry.get('messages', [])

        # Find assistant response
        assistant_content = None
        for msg in messages:
            if msg.get('role') == 'assistant':
                assistant_content = msg.get('content', '')
                break

        if not assistant_content:
            stats["removed_invalid"] += 1
            continue

        # Check template patterns
        if remove_templates and is_template_response(assistant_content):
            stats["removed_templates"] += 1
            continue

        # Check for questions (all sources - "Never ask questions" is a hard rule)
        if remove_questions:
            if has_question_in_response(assistant_content):
                stats["removed_questions"] += 1
                continue

        # Check for echo responses (assistant just repeats user)
        user_content = None
        for msg in messages:
            if msg.get('role') == 'user':
                user_content = msg.get('content', '')
                break
        if user_content and assistant_content.startswith(user_content[:50]):
            stats["removed_invalid"] += 1
            continue

        filtered.append(entry)
        stats["kept"] += 1

    return filtered, stats


def update_system_prompt(
    data: List[Dict[str, Any]],
    new_system_prompt: str,
) -> List[Dict[str, Any]]:
    """Replace system prompt in all samples with the new one."""
    updated = []

    for entry in data:
        messages = entry.get('messages', [])
        if not messages:
            continue

        # Update system message
        new_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                new_messages.append({
                    'role': 'system',
                    'content': new_system_prompt,
                })
            else:
                new_messages.append(msg)

        # Create updated entry
        updated_entry = {
            'messages': new_messages,
        }

        # Preserve metadata if present
        if 'metadata' in entry:
            updated_entry['metadata'] = entry['metadata']

        updated.append(updated_entry)

    return updated


def load_empathetic_dialogues(
    data_dir: Path,
    system_prompt: str,
) -> List[Dict[str, Any]]:
    """
    Load and process empathetic dialogues from parquet files.
    This was previously failing due to Git LFS not being pulled.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("Warning: pyarrow not installed. Cannot load empathetic dialogues.")
        return []

    parquet_dir = data_dir / "empathetic_dialogues_llm" / "data"
    if not parquet_dir.exists():
        print(f"Warning: {parquet_dir} not found")
        return []

    all_data = []
    parquet_files = list(parquet_dir.glob("*.parquet"))

    safety_filter = SafetyFilter(use_detoxify=False)

    for pf in parquet_files:
        print(f"  Loading {pf.name}...")
        try:
            table = pq.read_table(pf)
            df_dict = table.to_pydict()

            num_rows = len(df_dict.get('conv_id', []))
            for i in range(num_rows):
                row = {key: df_dict[key][i] for key in df_dict}

                conversations = row.get('conversations', [])
                emotion = row.get('emotion', '')

                if not conversations or len(conversations) < 2:
                    continue

                # Build messages
                messages = [{'role': 'system', 'content': system_prompt}]

                for turn in conversations:
                    role = turn.get('role', '')
                    content = turn.get('content', '').strip() if turn.get('content') else ''

                    if not content or role not in ['user', 'assistant']:
                        continue

                    messages.append({'role': role, 'content': content})

                # Validate structure
                roles = [m['role'] for m in messages]
                if 'user' not in roles or 'assistant' not in roles:
                    continue

                # Safety check
                all_text = " ".join([m['content'] for m in messages])
                safe, _ = safety_filter.is_safe(all_text)
                if not safe:
                    continue

                all_data.append({
                    'messages': messages,
                    'metadata': {
                        'source': 'empathetic_dialogues',
                        'emotion': emotion,
                        'conv_id': row.get('conv_id', ''),
                    }
                })

            print(f"    Loaded {num_rows} rows, kept {len(all_data)} so far")

        except Exception as e:
            print(f"    Error loading {pf.name}: {e}")
            continue

    # Filter empathetic dialogues for questions (to align with "never ask questions" rule)
    print(f"  Filtering empathetic dialogues for questions...")
    filtered_data, filter_stats = filter_dataset(
        all_data,
        remove_templates=True,
        remove_questions=True,
        source_name="empathetic_dialogues"
    )
    print(f"  After filtering: {len(filtered_data)} samples (removed {len(all_data) - len(filtered_data)})")

    return filtered_data


def sample_dataset(
    data: List[Dict[str, Any]],
    target_count: int,
    source_name: str,
) -> List[Dict[str, Any]]:
    """Sample from dataset to meet target count."""
    if len(data) <= target_count:
        print(f"  {source_name}: using all {len(data)} samples (target: {target_count})")
        return data.copy()

    sampled = random.sample(data, target_count)
    print(f"  {source_name}: sampled {len(sampled)} from {len(data)} (target: {target_count})")
    return sampled


def rebuild_dataset(
    project_dir: Path,
    total_samples: int = 50000,
    eval_ratio: float = 0.05,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Rebuild the dataset with quality improvements.

    Args:
        project_dir: Project root directory
        total_samples: Target total samples
        eval_ratio: Fraction for evaluation
        seed: Random seed

    Returns:
        Statistics dictionary
    """
    random.seed(seed)

    processed_dir = project_dir / "data" / "processed"
    output_dir = project_dir / "data" / "final"
    config_dir = project_dir / "config"

    # Load NEW system prompt
    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")
    print(f"First 100 chars: {system_prompt[:100]}...")

    stats = {
        "target_total": total_samples,
        "eval_ratio": eval_ratio,
        "system_prompt_length": len(system_prompt),
        "sources": {},
        "filtering": {},
        "final": {},
    }

    all_data = []

    # 1. Load empathetic dialogues (re-process from parquet)
    print("\n1. Loading empathetic dialogues from parquet...")
    empathetic_data = load_empathetic_dialogues(project_dir, system_prompt)
    print(f"   Loaded {len(empathetic_data)} samples")
    stats["sources"]["empathetic_dialogues"] = {"loaded": len(empathetic_data)}

    # 2. Load and filter philosophy QA
    print("\n2. Loading philosophy QA...")
    philosophy_data = load_jsonl(processed_dir / "philosophy_qa_processed.jsonl")
    print(f"   Loaded {len(philosophy_data)} samples")
    philosophy_data = update_system_prompt(philosophy_data, system_prompt)
    philosophy_filtered, phil_stats = filter_dataset(
        philosophy_data,
        remove_templates=True,
        remove_questions=True,
        source_name="philosophy_qa"
    )
    print(f"   After filtering: {len(philosophy_filtered)} samples")
    stats["sources"]["philosophy_qa"] = {"loaded": len(philosophy_data), "filtered": len(philosophy_filtered)}
    stats["filtering"]["philosophy_qa"] = phil_stats

    # 3. Load and filter counseling
    print("\n3. Loading counseling...")
    counseling_data = load_jsonl(processed_dir / "counseling_processed.jsonl")
    print(f"   Loaded {len(counseling_data)} samples")
    counseling_data = update_system_prompt(counseling_data, system_prompt)
    counseling_filtered, counsel_stats = filter_dataset(
        counseling_data,
        remove_templates=True,
        remove_questions=True,
        source_name="counseling"
    )
    print(f"   After filtering: {len(counseling_filtered)} samples")
    stats["sources"]["counseling"] = {"loaded": len(counseling_data), "filtered": len(counseling_filtered)}
    stats["filtering"]["counseling"] = counsel_stats

    # 4. Load and filter conversation starters
    print("\n4. Loading conversation starters...")
    starters_data = load_jsonl(processed_dir / "conversation_starters_processed.jsonl")
    print(f"   Loaded {len(starters_data)} samples")
    starters_data = update_system_prompt(starters_data, system_prompt)
    starters_filtered, starters_stats = filter_dataset(
        starters_data,
        remove_templates=True,
        remove_questions=True,
        source_name="conversation_starters"
    )
    print(f"   After filtering: {len(starters_filtered)} samples")
    stats["sources"]["conversation_starters"] = {"loaded": len(starters_data), "filtered": len(starters_filtered)}
    stats["filtering"]["conversation_starters"] = starters_stats

    # 5. Load and filter quotes (most were deduplicated, let's keep what we can)
    print("\n5. Loading quotes advice...")
    quotes_data = load_jsonl(processed_dir / "quotes_advice_processed.jsonl")
    print(f"   Loaded {len(quotes_data)} samples")
    quotes_data = update_system_prompt(quotes_data, system_prompt)
    quotes_filtered, quotes_stats = filter_dataset(
        quotes_data,
        remove_templates=True,
        remove_questions=True,
        source_name="quotes_advice"
    )
    print(f"   After filtering: {len(quotes_filtered)} samples")
    stats["sources"]["quotes_advice"] = {"loaded": len(quotes_data), "filtered": len(quotes_filtered)}
    stats["filtering"]["quotes_advice"] = quotes_stats

    # 6. Sample according to ratios
    print("\n6. Sampling according to target ratios...")

    # Calculate available vs target
    available = {
        "empathetic_dialogues": empathetic_data,
        "philosophy_qa": philosophy_filtered,
        "counseling": counseling_filtered,
        "conversation_starters": starters_filtered,
        "quotes_advice": quotes_filtered,
    }

    # Calculate targets
    targets = {k: int(total_samples * v) for k, v in TARGET_RATIOS.items()}

    for source, target in targets.items():
        data = available[source]
        sampled = sample_dataset(data, target, source)

        # Update metadata source field for consistency
        for item in sampled:
            if 'metadata' not in item:
                item['metadata'] = {}
            item['metadata']['source'] = source

        all_data.extend(sampled)
        stats["sources"][source]["sampled"] = len(sampled)

    print(f"\nTotal collected: {len(all_data)}")

    # 7. Deduplicate
    print("\n7. Deduplicating...")
    deduped_data, dedup_stats = deduplicate_jsonl(all_data, threshold=0.85)
    print(f"   After deduplication: {len(deduped_data)} (removed {dedup_stats['removed']})")
    stats["deduplication"] = dedup_stats

    # 8. Shuffle
    random.shuffle(deduped_data)

    # 9. Split train/eval
    eval_count = int(len(deduped_data) * eval_ratio)
    train_count = len(deduped_data) - eval_count

    eval_data = deduped_data[:eval_count]
    train_data = deduped_data[eval_count:]

    stats["final"]["train_count"] = len(train_data)
    stats["final"]["eval_count"] = len(eval_data)
    stats["final"]["total"] = len(deduped_data)

    # 10. Calculate final distribution
    source_dist = defaultdict(int)
    for record in train_data + eval_data:
        source = record.get('metadata', {}).get('source', 'unknown')
        source_dist[source] += 1
    stats["final"]["distribution"] = dict(source_dist)

    # 11. Write output files
    output_dir.mkdir(parents=True, exist_ok=True)

    train_file = output_dir / "claritymentor_train_v2.jsonl"
    print(f"\n8. Writing training set to {train_file}...")
    with open(train_file, 'w', encoding='utf-8') as f:
        for record in train_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"   Written: {len(train_data)} samples")

    eval_file = output_dir / "claritymentor_eval_v2.jsonl"
    print(f"   Writing evaluation set to {eval_file}...")
    with open(eval_file, 'w', encoding='utf-8') as f:
        for record in eval_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"   Written: {len(eval_data)} samples")

    # 12. Print summary
    print("\n" + "="*60)
    print("REBUILD COMPLETE")
    print("="*60)
    print(f"\nFinal dataset:")
    print(f"  Training samples: {stats['final']['train_count']}")
    print(f"  Evaluation samples: {stats['final']['eval_count']}")
    print(f"\nSource distribution:")
    for source, count in sorted(source_dist.items(), key=lambda x: -x[1]):
        pct = count / stats['final']['total'] * 100
        print(f"  {source}: {count} ({pct:.1f}%)")

    # Check for issues
    print("\n" + "-"*60)
    print("QUALITY CHECKS:")

    # Check template removal
    template_count = 0
    question_count = 0
    for record in train_data[:1000]:  # Sample check
        for msg in record.get('messages', []):
            if msg.get('role') == 'assistant':
                content = msg.get('content', '')
                if is_template_response(content):
                    template_count += 1
                if content.count('?') > 1:
                    question_count += 1

    print(f"  Templates in first 1000: {template_count} ({template_count/10:.1f}%)")
    print(f"  Multi-question responses in first 1000: {question_count} ({question_count/10:.1f}%)")

    # Check system prompt
    if train_data:
        first_system = train_data[0]['messages'][0]['content']
        if "Never ask questions" in first_system:
            print("  ✓ System prompt aligned (contains 'Never ask questions')")
        else:
            print("  ✗ System prompt may not be aligned!")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rebuild ClarityMentor dataset with quality improvements"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor"),
        help="Project root directory"
    )
    parser.add_argument(
        "--total-samples",
        type=int,
        default=50000,
        help="Target total samples"
    )
    parser.add_argument(
        "--eval-ratio",
        type=float,
        default=0.05,
        help="Fraction for evaluation"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    stats = rebuild_dataset(
        project_dir=args.project_dir,
        total_samples=args.total_samples,
        eval_ratio=args.eval_ratio,
        seed=args.seed,
    )

    # Save report
    report_file = args.project_dir / "data" / "final" / "rebuild_report.json"
    with open(report_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"\nReport saved to {report_file}")


if __name__ == "__main__":
    main()
