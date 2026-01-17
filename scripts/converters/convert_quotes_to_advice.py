"""
Convert quotes datasets to ClarityMentor advice format.

Sources:
- kaggle_datasets/quotes-500k/quotes.csv
- kaggle_datasets/goodreads-quotes/quotes.csv
- kaggle_datasets/inspirational-quotes/insparation.csv
- hf_datasets/datastax/philosopher-quotes/

Output: data/processed/quotes_advice_processed.jsonl
"""

import csv
import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.safety_filters import SafetyFilter


# Relevant quote categories/tags for life mentoring
RELEVANT_TAGS = {
    'philosophy', 'wisdom', 'life', 'meaning', 'purpose',
    'stoicism', 'existentialism', 'humanism',
    'growth', 'change', 'self-improvement', 'personal-development',
    'struggle', 'adversity', 'resilience', 'strength',
    'courage', 'fear', 'action', 'decision',
    'mindfulness', 'presence', 'awareness',
    'happiness', 'contentment', 'peace',
    'relationships', 'love', 'friendship', 'connection',
    'truth', 'honesty', 'integrity', 'character',
    'freedom', 'choice', 'responsibility',
    'death', 'mortality', 'impermanence',
    'suffering', 'pain', 'healing',
    'success', 'failure', 'learning',
    'motivation', 'inspiration', 'perseverance',
}

# Tags/categories to exclude
EXCLUDED_TAGS = {
    'god', 'jesus', 'faith', 'prayer', 'bible', 'christian', 'religious',
    'romance', 'sexy', 'erotic',
    'politics', 'political',
    'humor', 'funny', 'joke',
}

# Famous philosophers whose quotes are particularly valuable
PRIORITY_AUTHORS = {
    'marcus aurelius', 'seneca', 'epictetus',  # Stoics
    'friedrich nietzsche', 'albert camus', 'jean-paul sartre',  # Existentialists
    'socrates', 'plato', 'aristotle',  # Classics
    'confucius', 'lao tzu', 'buddha',  # Eastern
    'viktor frankl', 'carl jung', 'abraham maslow',  # Psychology
    'bertrand russell', 'simone de beauvoir', 'hannah arendt',  # Modern
    'ralph waldo emerson', 'henry david thoreau',  # Transcendentalists
}

# User scenarios that quotes can address
SCENARIO_TEMPLATES = {
    'meaning': [
        "I feel like my life has no purpose.",
        "What's the point of all this?",
        "I'm struggling to find meaning in my daily routine.",
    ],
    'adversity': [
        "I'm going through a really tough time right now.",
        "Everything seems to be going wrong.",
        "I feel like I can't catch a break.",
    ],
    'fear': [
        "I'm scared to make a big decision.",
        "Fear is holding me back from pursuing what I want.",
        "I'm afraid of failure.",
    ],
    'change': [
        "I want to change but don't know how to start.",
        "I feel stuck in my current situation.",
        "I know I need to change but it feels impossible.",
    ],
    'relationships': [
        "I'm having trouble in my relationships.",
        "I feel disconnected from the people around me.",
        "I don't know how to communicate what I'm feeling.",
    ],
    'self_worth': [
        "I don't feel good enough.",
        "I constantly compare myself to others.",
        "I struggle with self-acceptance.",
    ],
    'time': [
        "I feel like time is passing me by.",
        "I'm worried about getting older.",
        "I regret not doing things differently in the past.",
    ],
    'happiness': [
        "I don't know how to be happy.",
        "I've achieved what I thought I wanted but still feel empty.",
        "What does it mean to live a good life?",
    ],
}


def load_system_prompt(config_path: Path) -> str:
    """Load the ClarityMentor system prompt."""
    prompt_file = config_path / "system_prompt.txt"
    if prompt_file.exists():
        return prompt_file.read_text().strip()
    return "You are ClarityMentor, a thoughtful philosophical mentor."


def load_csv_quotes(file_path: Path) -> List[Dict[str, Any]]:
    """Load quotes from a CSV file."""
    quotes = []

    if not file_path.exists():
        print(f"  File not found: {file_path}")
        return quotes

    print(f"Loading {file_path.name}...")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Normalize field names
                quote_text = row.get('quote', row.get('Quote', row.get('text', ''))).strip()
                author = row.get('author', row.get('Author', '')).strip()
                tags = row.get('tags', row.get('Tags', row.get('category', row.get('Category', '')))).strip()

                if quote_text and len(quote_text) > 20:
                    quotes.append({
                        'quote': quote_text,
                        'author': author,
                        'tags': tags.lower() if tags else '',
                    })

        print(f"  Loaded {len(quotes)} quotes")

    except Exception as e:
        print(f"  Error loading {file_path}: {e}")

    return quotes


def load_arrow_quotes(file_path: Path) -> List[Dict[str, Any]]:
    """Load quotes from an Arrow file."""
    try:
        import pyarrow as pa
    except ImportError:
        print("  pyarrow not installed, skipping arrow file")
        return []

    quotes = []

    if not file_path.exists():
        # Try to find arrow file
        parent = file_path.parent
        if parent.exists():
            arrow_files = list(parent.glob("*.arrow"))
            if arrow_files:
                file_path = arrow_files[0]
            else:
                print(f"  No arrow files found in {parent}")
                return []

    print(f"Loading {file_path.name}...")

    try:
        with pa.memory_map(str(file_path), 'r') as source:
            reader = pa.ipc.open_file(source)
            table = reader.read_all()

        df_dict = table.to_pydict()
        num_rows = len(list(df_dict.values())[0]) if df_dict else 0

        for i in range(num_rows):
            quote_text = df_dict.get('quote', [''])[i] if 'quote' in df_dict else ''
            author = df_dict.get('author', [''])[i] if 'author' in df_dict else ''
            tags = df_dict.get('tags', [''])[i] if 'tags' in df_dict else ''

            if quote_text and len(quote_text) > 20:
                quotes.append({
                    'quote': quote_text.strip(),
                    'author': author.strip() if author else '',
                    'tags': tags.lower() if tags else '',
                })

        print(f"  Loaded {len(quotes)} quotes")

    except Exception as e:
        print(f"  Error loading {file_path}: {e}")

    return quotes


def is_relevant_quote(quote: Dict[str, Any]) -> bool:
    """Check if quote is relevant for life mentoring."""
    tags = quote.get('tags', '').lower()
    author = quote.get('author', '').lower()
    text = quote.get('quote', '').lower()

    # Check excluded tags
    for excluded in EXCLUDED_TAGS:
        if excluded in tags:
            return False

    # Priority authors always included
    for priority in PRIORITY_AUTHORS:
        if priority in author:
            return True

    # Check relevant tags
    for relevant in RELEVANT_TAGS:
        if relevant in tags:
            return True

    # Check if quote text contains relevant concepts
    relevant_concepts = ['life', 'wisdom', 'courage', 'fear', 'meaning', 'purpose',
                        'change', 'growth', 'truth', 'action', 'choice']
    if any(concept in text for concept in relevant_concepts):
        return True

    return False


def categorize_quote(quote: Dict[str, Any]) -> str:
    """Categorize a quote into a scenario type."""
    text = quote.get('quote', '').lower()
    tags = quote.get('tags', '').lower()

    if any(word in text or word in tags for word in ['meaning', 'purpose', 'why']):
        return 'meaning'
    elif any(word in text or word in tags for word in ['struggle', 'adversity', 'hard', 'difficult', 'suffer']):
        return 'adversity'
    elif any(word in text or word in tags for word in ['fear', 'afraid', 'scared', 'courage', 'brave']):
        return 'fear'
    elif any(word in text or word in tags for word in ['change', 'grow', 'become', 'transform']):
        return 'change'
    elif any(word in text or word in tags for word in ['love', 'friend', 'relationship', 'people', 'connect']):
        return 'relationships'
    elif any(word in text or word in tags for word in ['worth', 'value', 'self', 'enough', 'accept']):
        return 'self_worth'
    elif any(word in text or word in tags for word in ['time', 'moment', 'present', 'past', 'future', 'age']):
        return 'time'
    else:
        return 'happiness'


def create_advice_from_quote(
    quote: Dict[str, Any],
    system_prompt: str,
    safety_filter: SafetyFilter,
) -> Optional[Dict[str, Any]]:
    """
    Create a full advice conversation from a quote.

    The quote is used as an anchor in the philosophical reframe section.
    """
    quote_text = quote.get('quote', '')
    author = quote.get('author', 'Unknown')

    # Safety check
    safe, _ = safety_filter.is_safe(quote_text)
    if not safe:
        return None

    # Categorize and select scenario
    category = categorize_quote(quote)
    scenarios = SCENARIO_TEMPLATES.get(category, SCENARIO_TEMPLATES['happiness'])
    user_message = random.choice(scenarios)

    # Build response incorporating the quote
    if author and author != 'Unknown':
        quote_attribution = f'As {author} wisely observed: "{quote_text}"'
    else:
        quote_attribution = f'There\'s wisdom in the saying: "{quote_text}"'

    # Create structured response
    response_parts = [
        f"I hear you, and what you're feeling is completely valid.",
        "",
        quote_attribution,
        "",
        "This speaks to something fundamental about the human experience.",
        "",
        "Here are some thoughts on how to move forward:",
        "1. Start small - even tiny steps in a meaningful direction matter",
        "2. Reflect on what specifically resonates with you about this",
        "3. Consider one concrete action you could take today",
        "",
        "What would taking even a small step in this direction look like for you?"
    ]

    response = "\n".join(response_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]

    return {
        "messages": messages,
        "metadata": {
            "source": "quotes_to_advice",
            "category": category,
            "original_quote": quote_text,
            "author": author,
        }
    }


def process_all_quotes(
    project_dir: Path,
    output_file: Path,
    config_dir: Path,
    max_samples: int = 5000,
) -> Dict[str, int]:
    """
    Process all quote sources.

    Args:
        project_dir: Root project directory
        output_file: Output JSONL file path
        config_dir: Config directory
        max_samples: Maximum samples to include

    Returns:
        Statistics dictionary
    """
    system_prompt = load_system_prompt(config_dir)
    print(f"Loaded system prompt ({len(system_prompt)} chars)")

    safety_filter = SafetyFilter(use_detoxify=False)

    all_quotes = []
    stats = {
        "quotes_500k": 0,
        "goodreads": 0,
        "inspirational": 0,
        "philosopher": 0,
        "total_loaded": 0,
        "relevant": 0,
        "written": 0,
    }

    # Load from all sources
    print("\nLoading quote sources...")

    # 1. Quotes 500k
    csv_path = project_dir / "kaggle_datasets" / "quotes-500k" / "quotes.csv"
    quotes = load_csv_quotes(csv_path)
    stats["quotes_500k"] = len(quotes)
    all_quotes.extend(quotes)

    # 2. Goodreads
    csv_path = project_dir / "kaggle_datasets" / "goodreads-quotes" / "quotes.csv"
    quotes = load_csv_quotes(csv_path)
    stats["goodreads"] = len(quotes)
    all_quotes.extend(quotes)

    # 3. Inspirational
    csv_path = project_dir / "kaggle_datasets" / "inspirational-quotes" / "insparation.csv"
    quotes = load_csv_quotes(csv_path)
    stats["inspirational"] = len(quotes)
    all_quotes.extend(quotes)

    # 4. Philosopher quotes (Arrow)
    arrow_path = project_dir / "hf_datasets" / "datastax" / "philosopher-quotes"
    quotes = load_arrow_quotes(arrow_path / "data-00000-of-00001.arrow")
    stats["philosopher"] = len(quotes)
    all_quotes.extend(quotes)

    stats["total_loaded"] = len(all_quotes)
    print(f"\nTotal quotes loaded: {len(all_quotes)}")

    # Filter for relevance
    relevant_quotes = [q for q in all_quotes if is_relevant_quote(q)]
    stats["relevant"] = len(relevant_quotes)
    print(f"Relevant quotes: {len(relevant_quotes)}")

    # Shuffle and sample
    random.seed(42)
    random.shuffle(relevant_quotes)

    # Prioritize philosopher quotes
    priority_quotes = [q for q in relevant_quotes
                      if any(p in q.get('author', '').lower() for p in PRIORITY_AUTHORS)]
    other_quotes = [q for q in relevant_quotes
                   if not any(p in q.get('author', '').lower() for p in PRIORITY_AUTHORS)]

    # Take all priority quotes, then fill with others
    sampled = priority_quotes[:min(len(priority_quotes), max_samples // 2)]
    remaining = max_samples - len(sampled)
    sampled.extend(other_quotes[:remaining])

    print(f"Sampled {len(sampled)} quotes ({len(priority_quotes)} from priority authors)")

    # Convert to advice format
    results = []
    for quote in sampled:
        result = create_advice_from_quote(quote, system_prompt, safety_filter)
        if result:
            results.append(result)

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    stats["written"] = len(results)

    print(f"\nConversion complete!")
    print(f"  Total loaded: {stats['total_loaded']}")
    print(f"  Relevant: {stats['relevant']}")
    print(f"  Written: {stats['written']}")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert quotes to ClarityMentor advice format"
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
        default=Path("/home/lebi/projects/mentor/data/processed/quotes_advice_processed.jsonl"),
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
        default=5000,
        help="Maximum number of samples"
    )

    args = parser.parse_args()

    stats = process_all_quotes(
        project_dir=args.project_dir,
        output_file=args.output_file,
        config_dir=args.config_dir,
        max_samples=args.max_samples,
    )

    # Save stats
    stats_file = args.output_file.parent / "quotes_advice_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to {stats_file}")


if __name__ == "__main__":
    main()
