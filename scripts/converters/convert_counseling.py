"""
Convert counseling datasets to ClarityMentor format.

Sources:
- Mental Health Counseling Conversations.zip → combined_dataset.json
- hf_datasets/LuangMV97/Empathetic_counseling_Dataset/
- hf_datasets/Felladrin/pretrain-mental-health-counseling-conversations/

Output: data/processed/counseling_processed.jsonl
"""

import json
import zipfile
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.safety_filters import SafetyFilter, QualityFilter


def load_system_prompt(config_path: Path) -> str:
    """Load the ClarityMentor system prompt."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def load_mental_health_counseling_zip(zip_path: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Load data from Mental Health Counseling Conversations.zip.
    Yields records from combined_dataset.json inside the zip.
    """
    print(f"Loading from {zip_path}...")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find the combined_dataset.json file
        for name in zf.namelist():
            if 'combined_dataset.json' in name:
                print(f"  Found: {name}")
                with zf.open(name) as f:
                    # It's a JSONL file (one JSON object per line)
                    for line in f:
                        line = line.decode('utf-8').strip()
                        if line:
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                continue
                return

    print("  Warning: combined_dataset.json not found in zip")


def load_arrow_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from an Arrow file."""
    try:
        import pyarrow as pa
    except ImportError:
        raise ImportError("pyarrow is required. Install with: pip install pyarrow")

    print(f"Loading {file_path}...")

    try:
        with pa.memory_map(str(file_path), 'r') as source:
            reader = pa.ipc.open_file(source)
            table = reader.read_all()
    except Exception:
        with open(file_path, 'rb') as f:
            reader = pa.ipc.open_stream(f)
            table = reader.read_all()

    df_dict = table.to_pydict()
    num_rows = len(list(df_dict.values())[0]) if df_dict else 0

    data = []
    for i in range(num_rows):
        row = {key: df_dict[key][i] for key in df_dict}
        data.append(row)

    print(f"  Loaded {len(data)} rows")
    return data


def convert_context_response(
    context: str,
    response: str,
    system_prompt: str,
    safety_filter: SafetyFilter,
    source: str = "counseling",
) -> Optional[Dict[str, Any]]:
    """
    Convert a context/response pair to ClarityMentor format.

    Args:
        context: User's message/question
        response: Counselor's response
        system_prompt: System prompt to prepend
        safety_filter: SafetyFilter instance
        source: Source identifier for metadata

    Returns:
        Converted conversation dict or None if filtered
    """
    context = context.strip() if context else ""
    response = response.strip() if response else ""

    # Basic validation
    if len(context) < 20 or len(response) < 50:
        return None

    # Safety check on response
    safe, reason = safety_filter.is_safe_for_training(context, response)
    if not safe:
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context},
        {"role": "assistant", "content": response}
    ]

    return {
        "messages": messages,
        "metadata": {
            "source": source,
        }
    }


def convert_felladrin_text(
    text: str,
    system_prompt: str,
    safety_filter: SafetyFilter,
) -> Optional[Dict[str, Any]]:
    """
    Convert Felladrin format (single text field with conversation).
    The text field contains the full conversation, need to parse it.
    """
    text = text.strip() if text else ""
    if not text:
        return None

    # Try to split into user/assistant parts
    # Common patterns: "User: ... Assistant: ..." or "Human: ... AI: ..."
    import re

    # Try different patterns
    patterns = [
        r'(?:User|Human|Patient|Client):\s*(.*?)(?:Assistant|AI|Counselor|Therapist):\s*(.*)',
        r'(?:Q|Question):\s*(.*?)(?:A|Answer):\s*(.*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            context = match.group(1).strip()
            response = match.group(2).strip()

            if len(context) >= 20 and len(response) >= 50:
                return convert_context_response(
                    context, response, system_prompt, safety_filter,
                    source="felladrin_counseling"
                )

    # If no pattern matches, skip
    return None


def process_mental_health_zip(
    zip_path: Path,
    system_prompt: str,
    safety_filter: SafetyFilter,
) -> List[Dict[str, Any]]:
    """Process Mental Health Counseling Conversations zip."""
    results = []

    for record in load_mental_health_counseling_zip(zip_path):
        context = record.get('Context', '')
        response = record.get('Response', '')

        converted = convert_context_response(
            context, response, system_prompt, safety_filter,
            source="mental_health_counseling"
        )
        if converted:
            results.append(converted)

    print(f"  Converted: {len(results)}")
    return results


def process_luangmv97(
    data_dir: Path,
    system_prompt: str,
    safety_filter: SafetyFilter,
) -> List[Dict[str, Any]]:
    """Process LuangMV97 Empathetic Counseling Dataset."""
    results = []

    # Find arrow files
    arrow_files = list(data_dir.glob("*.arrow"))
    if not arrow_files:
        arrow_files = list(data_dir.glob("**/*.arrow"))

    for arrow_file in arrow_files:
        data = load_arrow_file(arrow_file)

        for record in data:
            # Format: input, label
            user_input = record.get('input', '')
            label = record.get('label', '')

            converted = convert_context_response(
                user_input, label, system_prompt, safety_filter,
                source="empathetic_counseling"
            )
            if converted:
                results.append(converted)

    print(f"  Total converted: {len(results)}")
    return results


def process_felladrin(
    data_dir: Path,
    system_prompt: str,
    safety_filter: SafetyFilter,
) -> List[Dict[str, Any]]:
    """Process Felladrin mental health counseling conversations."""
    results = []

    # Find arrow files
    arrow_files = list(data_dir.glob("*.arrow"))
    if not arrow_files:
        arrow_files = list(data_dir.glob("**/*.arrow"))

    for arrow_file in arrow_files:
        data = load_arrow_file(arrow_file)

        for record in data:
            # Format: text (full conversation)
            text = record.get('text', '')

            converted = convert_felladrin_text(text, system_prompt, safety_filter)
            if converted:
                results.append(converted)

    print(f"  Total converted: {len(results)}")
    return results


def process_all_sources(
    project_dir: Path,
    output_file: Path,
    config_dir: Path,
    max_samples: Optional[int] = None,
) -> Dict[str, int]:
    """
    Process all counseling data sources.

    Args:
        project_dir: Root project directory
        output_file: Output JSONL file path
        config_dir: Directory containing system_prompt.txt
        max_samples: Maximum total samples

    Returns:
        Statistics dictionary
    """
    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")

    safety_filter = SafetyFilter(use_detoxify=False)

    all_data = []
    stats = {
        "mental_health_counseling": 0,
        "empathetic_counseling": 0,
        "felladrin_counseling": 0,
        "total_written": 0,
    }

    # Source 1: Mental Health Counseling Conversations.zip
    zip_path = project_dir / "Mental Health Counseling Conversations.zip"
    if zip_path.exists():
        print(f"\n1. Processing {zip_path.name}...")
        data = process_mental_health_zip(zip_path, system_prompt, safety_filter)
        stats["mental_health_counseling"] = len(data)
        all_data.extend(data)
    else:
        print(f"  Warning: {zip_path} not found")

    # Source 2: LuangMV97 Empathetic Counseling
    luang_dir = project_dir / "hf_datasets" / "LuangMV97" / "Empathetic_counseling_Dataset"
    if luang_dir.exists():
        print(f"\n2. Processing LuangMV97...")
        data = process_luangmv97(luang_dir, system_prompt, safety_filter)
        stats["empathetic_counseling"] = len(data)
        all_data.extend(data)
    else:
        # Try alternative paths
        alt_paths = list((project_dir / "hf_datasets" / "LuangMV97").glob("*"))
        for alt in alt_paths:
            if alt.is_dir():
                print(f"  Found: {alt}")
                data = process_luangmv97(alt, system_prompt, safety_filter)
                stats["empathetic_counseling"] = len(data)
                all_data.extend(data)
                break

    # Source 3: Felladrin
    felladrin_dir = project_dir / "hf_datasets" / "Felladrin" / "pretrain-mental-health-counseling-conversations"
    if felladrin_dir.exists():
        print(f"\n3. Processing Felladrin...")
        data = process_felladrin(felladrin_dir, system_prompt, safety_filter)
        stats["felladrin_counseling"] = len(data)
        all_data.extend(data)
    else:
        alt_paths = list((project_dir / "hf_datasets" / "Felladrin").glob("*"))
        for alt in alt_paths:
            if alt.is_dir():
                print(f"  Found: {alt}")
                data = process_felladrin(alt, system_prompt, safety_filter)
                stats["felladrin_counseling"] = len(data)
                all_data.extend(data)
                break

    print(f"\nTotal collected: {len(all_data)}")

    # Shuffle and limit
    import random
    random.seed(42)
    random.shuffle(all_data)

    if max_samples and len(all_data) > max_samples:
        all_data = all_data[:max_samples]
        print(f"Limited to {max_samples} samples")

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in all_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    stats["total_written"] = len(all_data)

    print(f"\nConversion complete!")
    print(f"  Mental Health Counseling: {stats['mental_health_counseling']}")
    print(f"  Empathetic Counseling: {stats['empathetic_counseling']}")
    print(f"  Felladrin: {stats['felladrin_counseling']}")
    print(f"  Total written: {stats['total_written']}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert counseling datasets to ClarityMentor format"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor"),
        help="Root project directory"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/processed/counseling_processed.jsonl"),
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
        default=None,
        help="Maximum number of samples"
    )

    args = parser.parse_args()

    stats = process_all_sources(
        project_dir=args.project_dir,
        output_file=args.output_file,
        config_dir=args.config_dir,
        max_samples=args.max_samples,
    )

    # Save stats
    stats_file = args.output_file.parent / "counseling_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
