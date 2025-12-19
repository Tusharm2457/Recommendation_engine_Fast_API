"""
Mood Ruleset (Field 19): "How would you describe your mood lately?"

NLP-based lexicon matching with cross-field synergies for sleep, digestive symptoms, and work context.
"""

from typing import Dict, List, Tuple, Any
import re


class MoodRuleset:
    """
    Evaluates mood description and returns focus area weights.
    
    Uses lexicon-based NLP to detect:
    - Depression terms
    - Anxiety/stress terms
    - Cognitive complaints
    - Fatigue/low energy
    - Irritability
    - Positive affect
    - Trauma/PTSD cues
    - Workplace context
    
    Cross-field synergies:
    - Digestive symptoms → GA boost (gut-brain axis)
    - Sleep <6h or irregular → COG/STR boost
    - Shift work → COG boost
    """
    
    # Lexicons (lowercase, lemmatized forms)
    DEPRESSION_KEYWORDS = [
        "low", "sad", "down", "hopeless", "empty", "flat", "anhedonia",
        "tearful", "numb", "depressed", "depression", "crying", "cry"
    ]
    
    ANXIETY_STRESS_KEYWORDS = [
        "anxious", "anxiety", "edge", "panic", "overwhelmed", "ruminating",
        "worried", "worry", "tense", "tension", "irritable", "stressed",
        "stress", "nervous", "restless"
    ]
    
    COGNITIVE_KEYWORDS = [
        "brain fog", "foggy", "forgetful", "focus", "scattered", "slowed",
        "slow", "concentration", "memory", "confused", "confusion"
    ]
    
    FATIGUE_KEYWORDS = [
        "exhausted", "drained", "wiped out", "no energy", "wired and tired",
        "wired-and-tired", "tired", "fatigue", "fatigued", "weary", "worn out"
    ]
    
    IRRITABILITY_KEYWORDS = [
        "irritable", "irritability", "angry", "anger", "short temper",
        "short-tempered", "snappy", "agitated"
    ]
    
    POSITIVE_AFFECT_KEYWORDS = [
        "calm", "energized", "balanced", "upbeat", "optimistic", "good",
        "great", "happy", "content", "peaceful", "relaxed"
    ]
    
    TRAUMA_KEYWORDS = [
        "trauma", "ptsd", "post-traumatic", "assault", "abuse", "abused",
        "traumatic", "flashback", "nightmares"
    ]
    
    WORKPLACE_KEYWORDS = [
        "at work", "work", "job", "boss", "deadline", "deadlines",
        "coworker", "coworkers", "office", "workplace"
    ]
    
    # Intensity modifiers
    HIGH_INTENSITY_KEYWORDS = [
        "very", "extremely", "most days", "nearly every day", "always",
        "constantly", "severe", "severely"
    ]
    
    LOW_INTENSITY_KEYWORDS = [
        "a little", "sometimes", "occasionally", "mild", "mildly", "slightly"
    ]
    
    # Safety keywords (self-harm ideation)
    SAFETY_KEYWORDS = [
        "suicide", "suicidal", "kill myself", "end it all", "self-harm",
        "self harm", "hurt myself", "die", "death wish"
    ]
    
    def __init__(self):
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip emojis (except mood indicators), collapse punctuation."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower().strip()
        
        # Map emojis to text
        text = text.replace("😊", " positive ")
        text = text.replace("☹️", " negative ")
        text = text.replace("😔", " sad ")
        text = text.replace("😰", " anxious ")
        text = text.replace("😫", " exhausted ")
        
        # Strip other emojis (simple approach: remove non-ASCII)
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        # Collapse repeated punctuation
        text = re.sub(r'([!?.]){2,}', r'\1', text)
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _check_safety(self, text: str) -> bool:
        """Check for self-harm ideation keywords. Returns True if safety concern detected."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.SAFETY_KEYWORDS)
    
    def _detect_intensity_multiplier(self, text: str) -> float:
        """Detect intensity modifiers and return multiplier (0.8, 1.0, or 1.2)."""
        text_lower = text.lower()

        has_high = any(keyword in text_lower for keyword in self.HIGH_INTENSITY_KEYWORDS)
        has_low = any(keyword in text_lower for keyword in self.LOW_INTENSITY_KEYWORDS)

        if has_high and not has_low:
            return 1.2  # +20%
        elif has_low and not has_high:
            return 0.8  # -20%
        else:
            return 1.0  # No change

    def get_mood_weights(
        self,
        mood_data: Any,
        digestive_symptoms: str = None,
        sleep_hours: float = None,
        sleep_irregular: bool = False,
        shift_work: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on mood description.

        Args:
            mood_data: Free text mood description
            digestive_symptoms: Digestive symptoms from Phase 2 (for gut-brain axis)
            sleep_hours: Hours of sleep per night (for sleep-mood synergy)
            sleep_irregular: Whether sleep schedule is irregular (for sleep-mood synergy)
            shift_work: Whether patient does shift work (for workplace context)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Validate input
        if not mood_data or mood_data in ["", "None", "N/A", "NA"]:
            return weights, flags

        text = str(mood_data).strip()

        # Length guardrails (1-1000 characters)
        if len(text) < 1 or len(text) > 1000:
            return weights, flags

        # Normalize text
        text = self._normalize_text(text)

        # Safety check
        if self._check_safety(text):
            flags.append("SAFETY: Self-harm ideation detected - escalate to clinician")
            return weights, flags  # Do not score

        # Detect intensity multiplier
        intensity = self._detect_intensity_multiplier(text)

        # Detect categories
        has_depression = any(kw in text for kw in self.DEPRESSION_KEYWORDS)
        has_anxiety = any(kw in text for kw in self.ANXIETY_STRESS_KEYWORDS)
        has_cognitive = any(kw in text for kw in self.COGNITIVE_KEYWORDS)
        has_fatigue = any(kw in text for kw in self.FATIGUE_KEYWORDS)
        has_irritability = any(kw in text for kw in self.IRRITABILITY_KEYWORDS)
        has_positive = any(kw in text for kw in self.POSITIVE_AFFECT_KEYWORDS)
        has_trauma = any(kw in text for kw in self.TRAUMA_KEYWORDS)
        has_workplace = any(kw in text for kw in self.WORKPLACE_KEYWORDS)

        # Check for digestive symptoms (for gut-brain axis)
        has_digestive = bool(digestive_symptoms and digestive_symptoms.strip())
        has_bloating = False
        if has_digestive:
            digestive_lower = digestive_symptoms.lower()
            has_bloating = "bloat" in digestive_lower

        # A) Depression terms
        if has_depression:
            weights["COG"] = weights.get("COG", 0) + (0.30 * intensity)
            weights["STR"] = weights.get("STR", 0) + (0.25 * intensity)
            weights["IMM"] = weights.get("IMM", 0) + (0.10 * intensity)
            weights["HRM"] = weights.get("HRM", 0) + (0.05 * intensity)

            # If bloating → GA +0.20 (gut-brain interaction)
            if has_bloating:
                weights["GA"] = weights.get("GA", 0) + 0.20

        # B) Anxiety/stress terms
        if has_anxiety:
            weights["STR"] = weights.get("STR", 0) + (0.30 * intensity)
            weights["COG"] = weights.get("COG", 0) + (0.20 * intensity)

            # If digestive symptoms → GA +0.20-0.30 (brain-gut axis)
            if has_digestive:
                weights["GA"] = weights.get("GA", 0) + 0.25

        # C) Cognitive complaints
        if has_cognitive:
            weights["COG"] = weights.get("COG", 0) + (0.30 * intensity)
            weights["MITO"] = weights.get("MITO", 0) + (0.15 * intensity)
            weights["IMM"] = weights.get("IMM", 0) + (0.10 * intensity)

        # D) Fatigue/low energy
        if has_fatigue:
            weights["MITO"] = weights.get("MITO", 0) + (0.30 * intensity)
            weights["STR"] = weights.get("STR", 0) + (0.10 * intensity)
            weights["COG"] = weights.get("COG", 0) + (0.10 * intensity)

        # E) Irritability
        if has_irritability:
            weights["STR"] = weights.get("STR", 0) + (0.15 * intensity)

        # F) Positive affect (protective - reduces scores)
        if has_positive:
            weights["STR"] = weights.get("STR", 0) - 0.10
            weights["COG"] = weights.get("COG", 0) - 0.05

        # G) Trauma/PTSD cues
        if has_trauma:
            weights["STR"] = weights.get("STR", 0) + (0.35 * intensity)
            weights["COG"] = weights.get("COG", 0) + (0.15 * intensity)
            weights["IMM"] = weights.get("IMM", 0) + (0.10 * intensity)
            weights["GA"] = weights.get("GA", 0) + 0.10

        # H) Sleep interplay
        poor_sleep = (sleep_hours is not None and sleep_hours < 6) or sleep_irregular
        if poor_sleep and (has_depression or has_anxiety or "low" in text or "flat" in text):
            weights["COG"] = weights.get("COG", 0) + 0.10
            weights["STR"] = weights.get("STR", 0) + 0.10

        # I) Workplace qualifier
        if has_workplace and has_anxiety:
            weights["STR"] = weights.get("STR", 0) + 0.10

            # If shift work → COG +0.05 (circadian strain)
            if shift_work:
                weights["COG"] = weights.get("COG", 0) + 0.05

        # Remove negative scores (floor at 0)
        weights = {k: max(0, v) for k, v in weights.items()}

        # Remove zero scores
        weights = {k: v for k, v in weights.items() if v != 0}

        return weights, flags

