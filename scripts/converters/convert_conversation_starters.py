"""
Convert conversation starters dataset to ClarityMentor format.

Source: hf_datasets/Langame/conversation-starters/
Format: topics (list), prompt (string)

This dataset is used to train the model to:
1. Handle open-ended questions
2. Ask clarifying questions (Socratic style)
3. Explore context before giving advice

Output: data/processed/conversation_starters_processed.jsonl
"""

import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.safety_filters import SafetyFilter


# Topics relevant for life mentoring
RELEVANT_TOPICS = {
    'philosophy', 'life', 'meaning', 'purpose', 'values',
    'relationships', 'family', 'friendship', 'love',
    'career', 'work', 'success', 'goals',
    'personal', 'growth', 'self', 'identity',
    'emotions', 'feelings', 'mental', 'health',
    'decisions', 'choices', 'future', 'past',
    'happiness', 'fulfillment', 'contentment',
    'challenges', 'struggles', 'difficulties',
    'wisdom', 'advice', 'guidance',
    'ethics', 'morality', 'right', 'wrong',
    'death', 'mortality', 'legacy',
    'change', 'transformation', 'improvement',
}


def load_system_prompt(config_path: Path) -> str:
    """Load the ClarityMentor system prompt."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def load_dataset_from_disk(data_dir: Path) -> List[Dict[str, Any]]:
    """Load data using HuggingFace datasets library."""
    try:
        from datasets import load_from_disk
    except ImportError:
        raise ImportError("datasets is required. Install with: pip install datasets")

    print(f"Loading {data_dir}...")

    try:
        ds = load_from_disk(str(data_dir))
        data = [{"topics": row["topics"], "prompt": row["prompt"]} for row in ds]
        print(f"  Loaded {len(data)} rows")
        return data
    except Exception as e:
        print(f"  Error loading dataset: {e}")
        return []


def is_relevant_prompt(row: Dict[str, Any]) -> bool:
    """Check if prompt is relevant for life mentoring."""
    topics = row.get('topics', [])
    prompt = row.get('prompt', '')

    # Handle None values
    if prompt is None:
        return False

    prompt_lower = prompt.lower()

    # Check topics
    if topics:
        for topic in topics:
            if topic is None:
                continue
            topic_lower = topic.lower() if isinstance(topic, str) else ''
            for relevant in RELEVANT_TOPICS:
                if relevant in topic_lower:
                    return True

    # Check prompt content
    for relevant in RELEVANT_TOPICS:
        if relevant in prompt:
            return True

    # Check for question words that indicate reflection
    reflection_starters = ['what', 'why', 'how', 'when', 'who', 'which', 'where']
    if any(prompt.strip().lower().startswith(word) for word in reflection_starters):
        return True

    return False


def create_clarifying_response(prompt: str) -> str:
    """
    Create a Socratic-style response that asks clarifying questions.
    This teaches the model to explore context before giving advice.
    """
    prompt_lower = prompt.lower()

    # Detect topic and create appropriate response
    if any(word in prompt_lower for word in ['success', 'career', 'job', 'work', 'goal']):
        return (
            "That's a meaningful question to reflect on. Before I share my perspective, "
            "I'd like to understand yours better:\n\n"
            "- What does success look like to you personally, beyond external markers?\n"
            "- Are there moments when you've felt genuinely fulfilled? What made them special?\n"
            "- What values would you want to preserve even if it meant conventional 'success' came slower?\n\n"
            "Your answers to these will shape any meaningful response I could offer."
        )

    elif any(word in prompt_lower for word in ['relationship', 'love', 'friend', 'family', 'partner']):
        return (
            "Relationships shape so much of our experience. Let me ask you a few things:\n\n"
            "- What does a healthy relationship look like to you?\n"
            "- When you think about the relationships that matter most, what do they have in common?\n"
            "- Are there patterns in your connections that you've noticed over time?\n\n"
            "Understanding your perspective will help us explore this more meaningfully."
        )

    elif any(word in prompt_lower for word in ['happy', 'happiness', 'content', 'joy', 'fulfill']):
        return (
            "Happiness is something philosophers have debated for millennia. "
            "Before I offer my thoughts, I'm curious:\n\n"
            "- What moments in your life have brought you the deepest sense of contentment?\n"
            "- Do you distinguish between pleasure and fulfillment? How?\n"
            "- What would you be willing to sacrifice for lasting peace of mind?\n\n"
            "Your reflections here matter more than any definition I could give."
        )

    elif any(word in prompt_lower for word in ['meaning', 'purpose', 'why', 'point', 'reason']):
        return (
            "Questions of meaning are among the most profound we can ask. "
            "Let me understand where you're coming from:\n\n"
            "- When you ask about meaning, are you seeking something to discover or something to create?\n"
            "- What activities or relationships make you feel most alive?\n"
            "- If you couldn't 'find' meaning, would you be willing to make it?\n\n"
            "These questions might reveal more than any answer I could provide."
        )

    elif any(word in prompt_lower for word in ['change', 'different', 'better', 'improve', 'grow']):
        return (
            "Change is one of the few constants we can count on. To explore this with you:\n\n"
            "- What specifically draws you to this question right now?\n"
            "- Is there something you're hoping to change, or are you reflecting more generally?\n"
            "- What has past experience taught you about how you handle transitions?\n\n"
            "Your relationship with change is unique, and understanding it will guide our conversation."
        )

    elif any(word in prompt_lower for word in ['fear', 'afraid', 'scared', 'worry', 'anxious']):
        return (
            "Fear is a powerful teacher when we know how to listen to it. Help me understand:\n\n"
            "- Are you exploring fear as a concept, or working through something specific?\n"
            "- How do you typically respond when fear shows up in your life?\n"
            "- Is there a relationship between your fears and what you care about most?\n\n"
            "Once I understand your experience, I can offer more grounded perspective."
        )

    elif any(word in prompt_lower for word in ['decision', 'choose', 'choice', 'option', 'dilemma']):
        return (
            "The weight of decisions can feel heavy. Let me ask you:\n\n"
            "- Is there a specific decision on your mind, or are you thinking about choices in general?\n"
            "- What makes certain decisions feel harder than others for you?\n"
            "- When you've made good decisions in the past, what guided you?\n\n"
            "Understanding your decision-making process will help us explore this together."
        )

    elif any(word in prompt_lower for word in ['death', 'die', 'mortality', 'end', 'finite']):
        return (
            "Mortality is something most people avoid thinking about, yet engaging with it can be clarifying. "
            "I'd like to understand:\n\n"
            "- What prompted this reflection for you?\n"
            "- Does awareness of mortality feel paralyzing or motivating?\n"
            "- How does this awareness affect what feels important to you?\n\n"
            "There's no right answer here—only your truth."
        )

    else:
        # Generic Socratic response
        return (
            "That's worth exploring deeply. Before I share my perspective, "
            "a few questions:\n\n"
            "- What drew you to this particular question?\n"
            "- Is there a situation or experience that's prompting this reflection?\n"
            "- What would a satisfying answer look like to you?\n\n"
            "Your responses will help me engage with what matters most to you."
        )


def convert_starter(
    row: Dict[str, Any],
    system_prompt: str,
    safety_filter: SafetyFilter,
) -> Optional[Dict[str, Any]]:
    """
    Convert a conversation starter to ClarityMentor format.

    Args:
        row: Dictionary with topics and prompt
        system_prompt: System prompt to prepend
        safety_filter: SafetyFilter instance

    Returns:
        Converted conversation dict or None if filtered
    """
    prompt = row.get('prompt', '').strip()
    topics = row.get('topics', [])

    # Basic validation
    if not prompt or len(prompt) < 10:
        return None

    # Safety check
    safe, _ = safety_filter.is_safe(prompt)
    if not safe:
        return None

    # Generate clarifying response
    response = create_clarifying_response(prompt)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response}
    ]

    return {
        "messages": messages,
        "metadata": {
            "source": "conversation_starters",
            "topics": topics if isinstance(topics, list) else [],
        }
    }


def process_dataset(
    data_dir: Path,
    output_file: Path,
    config_dir: Path,
    max_samples: int = 3000,
) -> Dict[str, int]:
    """
    Process the conversation starters dataset.

    Args:
        data_dir: Directory containing arrow files
        output_file: Output JSONL file path
        config_dir: Config directory
        max_samples: Maximum samples to include

    Returns:
        Statistics dictionary
    """
    # Load dataset using datasets library
    data = load_dataset_from_disk(data_dir)

    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")

    safety_filter = SafetyFilter(use_detoxify=False)

    stats = {
        "total_input": len(data),
        "relevant": 0,
        "written": 0,
    }

    # Filter for relevant prompts
    relevant_data = [row for row in data if is_relevant_prompt(row)]
    stats["relevant"] = len(relevant_data)
    print(f"Relevant prompts: {len(relevant_data)}")

    # Shuffle and sample
    random.seed(42)
    random.shuffle(relevant_data)

    if len(relevant_data) > max_samples:
        relevant_data = relevant_data[:max_samples]

    # Convert to ClarityMentor format
    results = []
    for row in relevant_data:
        result = convert_starter(row, system_prompt, safety_filter)
        if result:
            results.append(result)

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    stats["written"] = len(results)

    print(f"\nConversion complete!")
    print(f"  Total input: {stats['total_input']}")
    print(f"  Relevant: {stats['relevant']}")
    print(f"  Written: {stats['written']}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert conversation starters to ClarityMentor format"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("/home/lebi/projects/mentor/hf_datasets/Langame/conversation-starters"),
        help="Directory containing arrow files"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("/home/lebi/projects/mentor/data/processed/conversation_starters_processed.jsonl"),
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
        default=3000,
        help="Maximum number of samples"
    )

    args = parser.parse_args()

    stats = process_dataset(
        data_dir=args.data_dir,
        output_file=args.output_file,
        config_dir=args.config_dir,
        max_samples=args.max_samples,
    )

    # Save stats
    stats_file = args.output_file.parent / "conversation_starters_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
