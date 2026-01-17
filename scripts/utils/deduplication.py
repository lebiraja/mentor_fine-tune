"""
Deduplication utilities for ClarityMentor dataset processing.
Uses TF-IDF + cosine similarity for near-duplicate detection.
"""

import hashlib
from typing import List, Set, Dict, Any, Tuple, Optional
from collections import defaultdict


class ExactDeduplicator:
    """Remove exact duplicates using hashing."""

    def __init__(self):
        self.seen_hashes: Set[str] = set()

    def _hash_text(self, text: str) -> str:
        """Create a hash of normalized text."""
        normalized = text.strip().lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def is_duplicate(self, text: str) -> bool:
        """Check if text is an exact duplicate."""
        text_hash = self._hash_text(text)
        if text_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(text_hash)
        return False

    def deduplicate(self, texts: List[str]) -> Tuple[List[str], int]:
        """
        Remove exact duplicates from a list of texts.
        Returns (deduplicated_list, num_removed).
        """
        self.seen_hashes.clear()
        result = []
        removed = 0

        for text in texts:
            if not self.is_duplicate(text):
                result.append(text)
            else:
                removed += 1

        return result, removed


class FuzzyDeduplicator:
    """Remove near-duplicates using TF-IDF and cosine similarity."""

    def __init__(self, threshold: float = 0.85):
        """
        Args:
            threshold: Cosine similarity threshold for considering texts as duplicates.
                       Higher = stricter (fewer duplicates detected).
        """
        self.threshold = threshold
        self._vectorizer = None
        self._tfidf_matrix = None

    def _get_vectorizer(self):
        """Lazy load TF-IDF vectorizer."""
        if self._vectorizer is None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._vectorizer = TfidfVectorizer(
                    max_features=10000,
                    ngram_range=(1, 2),
                    stop_words='english'
                )
            except ImportError:
                raise ImportError("scikit-learn is required for fuzzy deduplication. Install with: pip install scikit-learn")
        return self._vectorizer

    def deduplicate(self, texts: List[str], batch_size: int = 1000) -> Tuple[List[str], List[int]]:
        """
        Remove near-duplicates from a list of texts.

        Args:
            texts: List of texts to deduplicate
            batch_size: Process in batches for memory efficiency

        Returns:
            Tuple of (deduplicated_texts, indices_of_kept_texts)
        """
        if len(texts) < 2:
            return texts, list(range(len(texts)))

        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
        except ImportError:
            print("Warning: scikit-learn not available. Falling back to exact deduplication.")
            exact_dedup = ExactDeduplicator()
            deduped, _ = exact_dedup.deduplicate(texts)
            return deduped, list(range(len(deduped)))

        vectorizer = self._get_vectorizer()

        # Fit and transform all texts
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
        except ValueError as e:
            print(f"Warning: TF-IDF failed ({e}). Falling back to exact deduplication.")
            exact_dedup = ExactDeduplicator()
            deduped, _ = exact_dedup.deduplicate(texts)
            return deduped, list(range(len(deduped)))

        # Find duplicates using cosine similarity
        to_remove: Set[int] = set()
        n = len(texts)

        # Process in batches to avoid memory issues
        for i in range(0, n, batch_size):
            end_i = min(i + batch_size, n)

            # Compute similarity between batch and all texts
            batch_similarity = cosine_similarity(tfidf_matrix[i:end_i], tfidf_matrix)

            for batch_idx, global_idx in enumerate(range(i, end_i)):
                if global_idx in to_remove:
                    continue

                # Find similar texts (only look at indices > current to avoid double counting)
                for j in range(global_idx + 1, n):
                    if j in to_remove:
                        continue

                    if batch_similarity[batch_idx, j] > self.threshold:
                        # Keep the first occurrence, remove the later one
                        to_remove.add(j)

        # Build result
        kept_indices = [i for i in range(n) if i not in to_remove]
        deduplicated = [texts[i] for i in kept_indices]

        return deduplicated, kept_indices


class ConversationDeduplicator:
    """Deduplicate conversation pairs based on user message similarity."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.exact_dedup = ExactDeduplicator()
        self.fuzzy_dedup = FuzzyDeduplicator(threshold)

    def deduplicate_pairs(
        self,
        conversations: List[Dict[str, Any]],
        user_key: str = "user",
        assistant_key: str = "assistant"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Deduplicate conversation pairs based on user messages.

        Args:
            conversations: List of dicts with user and assistant messages
            user_key: Key for user message in dict
            assistant_key: Key for assistant message in dict

        Returns:
            Tuple of (deduplicated_conversations, stats_dict)
        """
        if not conversations:
            return [], {"original": 0, "kept": 0, "removed": 0}

        # Extract user messages
        user_messages = [conv.get(user_key, "") for conv in conversations]

        # Exact deduplication first (fast)
        exact_seen: Set[str] = set()
        after_exact = []
        exact_indices = []

        for i, msg in enumerate(user_messages):
            msg_hash = hashlib.md5(msg.strip().lower().encode()).hexdigest()
            if msg_hash not in exact_seen:
                exact_seen.add(msg_hash)
                after_exact.append(msg)
                exact_indices.append(i)

        # Fuzzy deduplication on remaining
        _, fuzzy_kept_indices = self.fuzzy_dedup.deduplicate(after_exact)

        # Map back to original indices
        final_indices = [exact_indices[i] for i in fuzzy_kept_indices]
        result = [conversations[i] for i in final_indices]

        stats = {
            "original": len(conversations),
            "after_exact": len(after_exact),
            "kept": len(result),
            "removed": len(conversations) - len(result)
        }

        return result, stats


def deduplicate_jsonl(
    data: List[Dict[str, Any]],
    key: str = "messages",
    threshold: float = 0.85
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Deduplicate a list of JSONL entries based on conversation content.

    Args:
        data: List of JSONL entries (each with 'messages' key)
        key: Key containing the messages
        threshold: Similarity threshold for fuzzy deduplication

    Returns:
        Tuple of (deduplicated_data, stats)
    """
    if not data:
        return [], {"original": 0, "kept": 0, "removed": 0}

    # Create fingerprint from first user message
    def get_fingerprint(entry: Dict[str, Any]) -> str:
        messages = entry.get(key, [])
        for msg in messages:
            if msg.get("role") == "user":
                return msg.get("content", "").strip().lower()
        return ""

    # Extract fingerprints
    fingerprints = [get_fingerprint(entry) for entry in data]

    # Exact deduplication
    seen: Set[str] = set()
    after_exact = []
    exact_indices = []

    for i, fp in enumerate(fingerprints):
        if not fp:
            continue
        fp_hash = hashlib.md5(fp.encode()).hexdigest()
        if fp_hash not in seen:
            seen.add(fp_hash)
            after_exact.append(fp)
            exact_indices.append(i)

    # Fuzzy deduplication if we have enough samples
    if len(after_exact) > 100:
        fuzzy = FuzzyDeduplicator(threshold)
        _, fuzzy_kept = fuzzy.deduplicate(after_exact)
        final_indices = [exact_indices[i] for i in fuzzy_kept]
    else:
        final_indices = exact_indices

    result = [data[i] for i in final_indices]

    stats = {
        "original": len(data),
        "after_exact": len(after_exact),
        "kept": len(result),
        "removed": len(data) - len(result)
    }

    return result, stats


if __name__ == "__main__":
    # Test deduplication
    print("Testing deduplication...")

    # Test exact deduplication
    exact = ExactDeduplicator()
    texts = ["Hello world", "hello world", "Hello World", "Different text"]
    deduped, removed = exact.deduplicate(texts)
    print(f"Exact dedup: {len(texts)} -> {len(deduped)} (removed {removed})")

    # Test fuzzy deduplication
    fuzzy = FuzzyDeduplicator(threshold=0.8)
    texts = [
        "I feel really sad and lonely today.",
        "I'm feeling very sad and lonely today.",
        "I feel extremely happy and joyful!",
        "Today I'm feeling sad and alone.",
        "The weather is nice outside.",
    ]
    deduped, kept = fuzzy.deduplicate(texts)
    print(f"Fuzzy dedup: {len(texts)} -> {len(deduped)}")
    print(f"Kept texts: {deduped}")
