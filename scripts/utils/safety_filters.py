"""
Safety filters for ClarityMentor dataset processing.
Uses Detoxify for toxicity detection and keyword-based filtering.
"""

import re
from typing import Tuple, Optional
from functools import lru_cache


class SafetyFilter:
    """Filter content for toxicity, self-harm, and inappropriate advice."""

    def __init__(self, toxicity_threshold: float = 0.3, use_detoxify: bool = True):
        self.toxicity_threshold = toxicity_threshold
        self.use_detoxify = use_detoxify
        self._toxicity_model = None

        # High-risk keywords for self-harm detection
        self.self_harm_patterns = [
            r'\bkill\s*(my)?self\b',
            r'\bend\s*my\s*life\b',
            r'\bsuicide\s*method\b',
            r'\bhow\s*to\s*(commit\s*)?suicide\b',
            r'\bwant\s*to\s*die\b',
            r'\bcut\s*(my)?self\b',
            r'\bself[\s-]*harm\b',
        ]

        # Medical advice patterns (assistant shouldn't make medical claims)
        self.medical_patterns = [
            r'\byou\s*(definitely\s*)?have\s*(depression|anxiety|bipolar|adhd|ptsd)\b',
            r'\bi\s*diagnose\s*you\b',
            r'\byou\s*should\s*(take|stop\s*taking)\s*\w+\s*(medication|pills|meds)\b',
            r'\bprescribe\b',
        ]

        # Religious preaching patterns
        self.religious_patterns = [
            r'\bpray\s*to\s*(god|jesus|allah)\b',
            r'\bgod\s*(will|has\s*a\s*plan)\b',
            r'\bjust\s*have\s*faith\b',
            r'\bthe\s*lord\b',
            r'\bjesus\s*(loves|saves)\b',
            r'\bread\s*the\s*bible\b',
        ]

        # Toxic/hateful content patterns
        self.toxic_patterns = [
            r'\bkill\s*yourself\b',
            r'\byou\s*should\s*die\b',
            r'\bgo\s*die\b',
        ]

        # Compile patterns for efficiency
        self._self_harm_regex = re.compile('|'.join(self.self_harm_patterns), re.IGNORECASE)
        self._medical_regex = re.compile('|'.join(self.medical_patterns), re.IGNORECASE)
        self._religious_regex = re.compile('|'.join(self.religious_patterns), re.IGNORECASE)
        self._toxic_regex = re.compile('|'.join(self.toxic_patterns), re.IGNORECASE)

    @property
    def toxicity_model(self):
        """Lazy load Detoxify model."""
        if self._toxicity_model is None and self.use_detoxify:
            try:
                from detoxify import Detoxify
                self._toxicity_model = Detoxify('original')
            except ImportError:
                print("Warning: detoxify not installed. Using keyword-based filtering only.")
                self.use_detoxify = False
        return self._toxicity_model

    def check_toxicity(self, text: str) -> Tuple[bool, float]:
        """
        Check if text is toxic using Detoxify.
        Returns (is_safe, toxicity_score).
        """
        if not self.use_detoxify or self.toxicity_model is None:
            return True, 0.0

        try:
            scores = self.toxicity_model.predict(text)
            toxicity_score = scores.get('toxicity', 0.0)
            is_safe = toxicity_score < self.toxicity_threshold
            return is_safe, toxicity_score
        except Exception as e:
            print(f"Warning: Toxicity check failed: {e}")
            return True, 0.0

    def check_self_harm(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check for self-harm content in text.
        Returns (is_safe, matched_pattern).
        """
        match = self._self_harm_regex.search(text)
        if match:
            return False, match.group()
        return True, None

    def check_medical_claims(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check for inappropriate medical advice/claims.
        Returns (is_safe, matched_pattern).
        """
        match = self._medical_regex.search(text)
        if match:
            return False, match.group()
        return True, None

    def check_religious_preaching(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check for religious preaching content.
        Returns (is_safe, matched_pattern).
        """
        match = self._religious_regex.search(text)
        if match:
            return False, match.group()
        return True, None

    def check_toxic_keywords(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check for explicitly toxic/hateful keywords.
        Returns (is_safe, matched_pattern).
        """
        match = self._toxic_regex.search(text)
        if match:
            return False, match.group()
        return True, None

    def is_safe(self, text: str, check_all: bool = True) -> Tuple[bool, str]:
        """
        Comprehensive safety check on text.

        Args:
            text: The text to check
            check_all: If True, runs all checks. If False, stops at first failure.

        Returns:
            Tuple of (is_safe, reason) where reason describes why it failed.
        """
        if not text or not text.strip():
            return False, "empty_text"

        # Check toxic keywords first (fast)
        safe, match = self.check_toxic_keywords(text)
        if not safe:
            return False, f"toxic_keyword: {match}"

        # Check self-harm content
        safe, match = self.check_self_harm(text)
        if not safe:
            return False, f"self_harm: {match}"

        # Check Detoxify toxicity (slower, run last)
        if self.use_detoxify:
            safe, score = self.check_toxicity(text)
            if not safe:
                return False, f"toxicity_score: {score:.3f}"

        return True, "passed"

    def is_safe_for_training(self, user_text: str, assistant_text: str) -> Tuple[bool, str]:
        """
        Check if a user-assistant pair is safe for training.

        Args:
            user_text: The user's message
            assistant_text: The assistant's response

        Returns:
            Tuple of (is_safe, reason)
        """
        # User text can contain sensitive topics (that's what users ask about)
        # But we still filter extremely harmful content
        safe, reason = self.check_toxic_keywords(user_text)
        if not safe:
            return False, f"user_{reason}"

        # Assistant responses need stricter filtering
        safe, reason = self.is_safe(assistant_text)
        if not safe:
            return False, f"assistant_{reason}"

        # Check assistant doesn't give medical advice
        safe, match = self.check_medical_claims(assistant_text)
        if not safe:
            return False, f"assistant_medical_claim: {match}"

        # Check assistant doesn't preach
        safe, match = self.check_religious_preaching(assistant_text)
        if not safe:
            return False, f"assistant_religious: {match}"

        return True, "passed"

    def requires_professional_help(self, text: str) -> bool:
        """
        Detect if the user's message indicates they need professional help.
        These are cases where the model should recommend seeing a professional.
        """
        crisis_patterns = [
            r'\bdon\'?t\s*want\s*to\s*(be\s*)?alive\b',
            r'\bwant\s*to\s*(die|end\s*it)\b',
            r'\bsuicid(e|al)\b',
            r'\bself[\s-]*harm\b',
            r'\bhurt(ing)?\s*(my)?self\b',
            r'\bno\s*reason\s*to\s*live\b',
            r'\beveryone\s*(would\s*be)?\s*better\s*off\s*without\s*me\b',
        ]

        crisis_regex = re.compile('|'.join(crisis_patterns), re.IGNORECASE)
        return bool(crisis_regex.search(text))


class QualityFilter:
    """Filter content for quality (length, coherence, etc.)."""

    def __init__(
        self,
        min_user_length: int = 10,
        max_user_length: int = 2000,
        min_assistant_length: int = 50,
        max_assistant_length: int = 3000,
    ):
        self.min_user_length = min_user_length
        self.max_user_length = max_user_length
        self.min_assistant_length = min_assistant_length
        self.max_assistant_length = max_assistant_length

    def check_length(self, text: str, role: str = "user") -> Tuple[bool, str]:
        """Check if text length is within acceptable range."""
        length = len(text.strip())

        if role == "user":
            if length < self.min_user_length:
                return False, f"too_short ({length} < {self.min_user_length})"
            if length > self.max_user_length:
                return False, f"too_long ({length} > {self.max_user_length})"
        else:
            if length < self.min_assistant_length:
                return False, f"too_short ({length} < {self.min_assistant_length})"
            if length > self.max_assistant_length:
                return False, f"too_long ({length} > {self.max_assistant_length})"

        return True, "passed"

    def check_not_placeholder(self, text: str) -> Tuple[bool, str]:
        """Check if text is not a placeholder or deleted content."""
        placeholder_patterns = [
            r'^\.{3,}$',  # Just ellipsis
            r'^\[deleted\]$',
            r'^\[removed\]$',
            r'^n/a$',
            r'^null$',
            r'^none$',
        ]

        text_lower = text.strip().lower()
        for pattern in placeholder_patterns:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return False, "placeholder_text"

        return True, "passed"

    def is_quality(self, user_text: str, assistant_text: str) -> Tuple[bool, str]:
        """Check if a conversation pair meets quality standards."""
        # Check user text
        safe, reason = self.check_not_placeholder(user_text)
        if not safe:
            return False, f"user_{reason}"

        safe, reason = self.check_length(user_text, "user")
        if not safe:
            return False, f"user_{reason}"

        # Check assistant text
        safe, reason = self.check_not_placeholder(assistant_text)
        if not safe:
            return False, f"assistant_{reason}"

        safe, reason = self.check_length(assistant_text, "assistant")
        if not safe:
            return False, f"assistant_{reason}"

        return True, "passed"


def create_default_filters() -> Tuple[SafetyFilter, QualityFilter]:
    """Create default filter instances."""
    return SafetyFilter(), QualityFilter()


if __name__ == "__main__":
    # Test the filters
    safety = SafetyFilter(use_detoxify=False)  # Skip Detoxify for quick test
    quality = QualityFilter()

    # Test cases
    test_cases = [
        ("I feel sad today.", "I understand how you feel. Can you tell me more about what's making you sad?"),
        ("I want to die.", "I hear that you're in pain. Please consider reaching out to a crisis helpline."),
        ("What should I do?", "You should pray to God for guidance."),
        ("I'm anxious.", "You definitely have anxiety disorder and should take medication."),
    ]

    print("Testing safety filters:")
    for user, assistant in test_cases:
        safe, reason = safety.is_safe_for_training(user, assistant)
        print(f"  User: '{user[:40]}...' | Assistant: '{assistant[:40]}...'")
        print(f"    Safe: {safe}, Reason: {reason}")
        print()
