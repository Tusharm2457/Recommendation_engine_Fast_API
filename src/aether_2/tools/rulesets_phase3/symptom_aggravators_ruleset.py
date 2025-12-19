"""
Phase 3 Ruleset: Symptom Aggravators (Field 5)
"What makes your symptoms WORSE?"

Analyzes free-text responses about factors that worsen symptoms.
Detects food triggers, lifestyle factors, and physiological patterns with NLP-based matching.
"""

from typing import Dict, Tuple, List, Any
import re
from collections import defaultdict

from .constants import (
    get_spacy_model,
    lemmatize_text,
    match_keyword_fuzzy,
    RAPIDFUZZ_AVAILABLE
)


class SymptomAggravatorsRuleset:
    """
    Ruleset for scoring factors that make symptoms worse.
    
    Detects 3 main categories:
    1. Food timing & meal patterns (after meals, large meals, late-night eating)
    2. Specific foods & ingredients (dairy, gluten, FODMAPs, caffeine, alcohol, etc.)
    3. Lifestyle & physiological triggers (stress, sleep, morning flares, heat, exercise)
    
    Features:
    - NLP-based keyword matching with lemmatization + fuzzy matching
    - Intensity modifiers ("always", "every time" → +0.05; "sometimes" → ×0.5)
    - Negation detection ("coffee doesn't bother me")
    - Synergy bonus (≥3 GI triggers → GA +0.10)
    - Per-domain caps (GA ≤ 0.45, STR ≤ 0.35, IMM ≤ 0.30, etc.)
    - Safety flags (anaphylaxis, bloody stool, etc.)
    """
    
    # Per-domain caps for this field
    DOMAIN_CAPS = {
        "GA": 0.45,
        "STR": 0.35,
        "IMM": 0.30,
        "DTX": 0.25,
        "CM": 0.20,
        "SKN": 0.20,
        "COG": 0.15,
        "HRM": 0.10,
        "MITO": 0.10
    }
    
    # Safety flag keywords (route to triage, no scoring)
    SAFETY_KEYWORDS = [
        "anaphylaxis", "throat closing", "throat swelling", "can't breathe",
        "bloody stool", "blood in stool", "black tarry stool", "melena",
        "unintentional weight loss", "unexplained weight loss",
        "fever with severe pain", "high fever", "severe abdominal pain"
    ]
    
    # Intensity modifier keywords
    INTENSITY_HIGH = ["always", "every time", "severe", "extremely", "constantly"]
    INTENSITY_LOW = ["sometimes", "occasionally", "maybe", "unsure", "might"]
    
    def __init__(self):
        """Initialize the ruleset with NLP model and trigger lexicons."""
        self.nlp = get_spacy_model()
        self._build_trigger_lexicons()
    
    def _build_trigger_lexicons(self):
        """
        Build comprehensive trigger lexicons with keywords and base weights.
        
        Structure: {
            "trigger_name": {
                "keywords": [...],
                "scores": {"GA": 0.25, ...},
                "category": "food" | "lifestyle" | "meal_pattern"
            }
        }
        """
        self.triggers = {
            # ===== A1) FOOD TIMING & MEAL PATTERNS =====
            "after_meals": {
                "keywords": ["after meal", "post meal", "postmeal", "after eating", "post prandial", "postprandial"],
                "scores": {"GA": 0.25, "CM": 0.10},
                "category": "meal_pattern"
            },
            "large_meals": {
                "keywords": ["large meal", "big meal", "heavy meal", "overeating", "too much food", "big dinner", "large dinner", "big lunch", "large lunch"],
                "scores": {"GA": 0.25, "CM": 0.10},
                "category": "meal_pattern"
            },
            "late_night_meals": {
                "keywords": ["late night", "late meal", "nighttime eating", "eating before bed", "late dinner", "eat late", "eating late"],
                "scores": {"GA": 0.20, "CM": 0.10},
                "category": "meal_pattern"
            },
            "high_fat_meals": {
                "keywords": ["high fat", "fatty", "fried", "greasy", "oily food"],
                "scores": {"GA": 0.20},
                "category": "meal_pattern"
            },
            "bloating_immediate": {
                "keywords": ["bloating right after", "bloat immediately", "bloat after eating"],
                "scores": {"GA": 0.20},
                "category": "meal_pattern"
            },
            "bloating_delayed": {
                "keywords": ["bloating 2 hours", "bloat hours later", "delayed bloating"],
                "scores": {"GA": 0.20},
                "category": "meal_pattern"
            },
            
            # ===== A2) SPECIFIC FOODS & INGREDIENTS =====
            "dairy": {
                "keywords": ["dairy", "milk", "lactose", "ice cream", "whey", "cheese", "cream", "latte", "casein", "yogurt"],
                "scores": {"GA": 0.25, "IMM": 0.05, "SKN": 0.05},
                "category": "food"
            },
            "gluten": {
                "keywords": ["gluten", "wheat", "bread", "pasta", "pizza", "barley", "rye", "seitan"],
                "scores": {"GA": 0.20},
                "category": "food"
            },
            "fodmap_onions_garlic": {
                "keywords": ["onion", "garlic", "leek", "shallot", "fructan"],
                "scores": {"GA": 0.25},
                "category": "food"
            },
            "fodmap_beans": {
                "keywords": ["bean", "legume", "lentil", "chickpea", "pea"],
                "scores": {"GA": 0.20},
                "category": "food"
            },
            "spicy": {
                "keywords": ["spicy", "hot sauce", "chili", "pepper", "capsaicin"],
                "scores": {"GA": 0.15},
                "category": "food"
            },
            "coffee_caffeine": {
                "keywords": ["coffee", "caffeine", "espresso", "energy drink"],
                "scores": {"GA": 0.15, "STR": 0.05},
                "category": "food"
            },
            "alcohol": {
                "keywords": ["alcohol", "wine", "beer", "liquor", "drinking"],
                "scores": {"GA": 0.20, "DTX": 0.10},
                "category": "food"
            },
            "artificial_sweeteners": {
                "keywords": ["artificial sweetener", "sorbitol", "mannitol", "xylitol", "sucralose", "aspartame", "neotame", "sugar alcohol"],
                "scores": {"GA": 0.15, "IMM": 0.05},
                "category": "food"
            },
            "carbonated": {
                "keywords": ["carbonated", "fizzy", "soda", "sparkling", "pop", "cola"],
                "scores": {"GA": 0.10},
                "category": "food"
            },

            # ===== A3) LIFESTYLE & PHYSIOLOGICAL TRIGGERS =====
            "stress": {
                "keywords": ["stress", "anxiety", "anxious", "worried", "nervous", "tense"],
                "scores": {"STR": 0.20, "GA": 0.10},
                "category": "lifestyle"
            },
            "lack_of_sleep": {
                "keywords": ["lack of sleep", "poor sleep", "insomnia", "sleep deprivation", "not sleeping", "can't sleep"],
                "scores": {"STR": 0.20, "GA": 0.05, "COG": 0.10},
                "category": "lifestyle"
            },
            "morning_flares": {
                "keywords": ["morning", "wake up", "first thing", "early morning"],
                "scores": {"STR": 0.15, "GA": 0.05, "HRM": 0.05},
                "category": "lifestyle"
            },
            "heat": {
                "keywords": ["heat", "hot weather", "temperature", "hot shower", "sauna", "warm"],
                "scores": {"IMM": 0.15, "GA": 0.05, "SKN": 0.10},
                "category": "lifestyle"
            },
            "intense_exercise": {
                "keywords": ["intense exercise", "hard workout", "vigorous", "heavy exercise", "strenuous"],
                "scores": {"STR": 0.15, "GA": 0.05},
                "category": "lifestyle"
            }
        }

        # Preprocess lexicons for faster matching (lemmatize keywords)
        if self.nlp:
            for trigger_name, trigger_data in self.triggers.items():
                keywords = trigger_data["keywords"]
                # Lemmatize each keyword
                lemma_keywords = []
                for keyword in keywords:
                    lemmatized = lemmatize_text(keyword, self.nlp).lower()
                    lemma_keywords.append(lemmatized)
                trigger_data["lemma_keywords"] = lemma_keywords

    def _detect_safety_flags(self, text: str) -> Dict[str, bool]:
        """
        Detect safety flag keywords that should route to triage.

        Returns:
            Dictionary of safety flags (e.g., {"red_flag": True})
        """
        text_lower = text.lower()
        flags = {}

        for keyword in self.SAFETY_KEYWORDS:
            if keyword in text_lower:
                flags["red_flag"] = True
                break

        return flags

    def _detect_intensity_modifier(self, text: str, trigger_text: str) -> float:
        """
        Detect intensity modifiers near the trigger text.

        Args:
            text: Full input text
            trigger_text: The matched trigger text

        Returns:
            Multiplier (1.0 default, 1.5 for high intensity, 0.5 for low intensity)
        """
        # Look for intensity keywords within 10 words of the trigger
        text_lower = text.lower()

        # Find position of trigger
        trigger_pos = text_lower.find(trigger_text.lower())
        if trigger_pos == -1:
            return 1.0

        # Extract context window (50 chars before and after)
        start = max(0, trigger_pos - 50)
        end = min(len(text_lower), trigger_pos + len(trigger_text) + 50)
        context = text_lower[start:end]

        # Check for high intensity
        for keyword in self.INTENSITY_HIGH:
            if keyword in context:
                return 1.5  # +0.05 bonus translates to 1.5x multiplier

        # Check for low intensity
        for keyword in self.INTENSITY_LOW:
            if keyword in context:
                return 0.5

        return 1.0

    def _detect_negation(self, text: str, trigger_text: str) -> bool:
        """
        Detect if a trigger is negated (e.g., "coffee doesn't bother me").

        Args:
            text: Full input text
            trigger_text: The matched trigger text

        Returns:
            True if negated, False otherwise
        """
        text_lower = text.lower()

        # Find position of trigger
        trigger_pos = text_lower.find(trigger_text.lower())
        if trigger_pos == -1:
            return False

        # Split into words
        words = text_lower.split()
        trigger_word_idx = None

        # Find trigger word index
        for i, word in enumerate(words):
            if trigger_text.lower() in word:
                trigger_word_idx = i
                break

        if trigger_word_idx is None:
            return False

        # Find the start of the current clause (look for punctuation or conjunctions)
        clause_start = 0
        for i in range(trigger_word_idx - 1, -1, -1):
            word = words[i].strip(",.;:!?")
            # Stop at clause boundaries
            if word in ["but", "and", "or", "however", "though", "although"] or any(c in words[i] for c in [",", ";", "."]):
                clause_start = i + 1
                break

        # Extract the clause containing the trigger (from clause start to trigger + 3 words)
        end_idx = min(len(words), trigger_word_idx + 4)
        clause_words = words[clause_start:end_idx]
        clause = " ".join(clause_words)

        # Check for negation patterns within this clause only
        negation_words = ["not", "no", "never", "doesn't", "don't", "isn't", "aren't", "won't", "can't"]

        # Check if any negation word appears in the clause
        for neg_word in negation_words:
            if neg_word in clause_words:
                return True

        # Check for specific negation phrases
        negation_phrases = ["doesn't bother", "don't bother", "no problem", "not a problem"]
        for phrase in negation_phrases:
            if phrase in clause:
                return True

        return False

    def _detect_triggers(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all triggers in the text using NLP-based matching.

        Returns:
            List of detected triggers with metadata:
            [
                {
                    "trigger_name": "dairy",
                    "matched_text": "milk",
                    "base_scores": {"GA": 0.25, "IMM": 0.05},
                    "intensity_multiplier": 1.5,
                    "negated": False,
                    "category": "food"
                },
                ...
            ]
        """
        if not text or not text.strip():
            return []

        text_lower = text.lower()
        text_lemmatized = lemmatize_text(text, self.nlp).lower() if self.nlp else text_lower

        detected = []

        for trigger_name, trigger_data in self.triggers.items():
            keywords = trigger_data.get("keywords", [])
            lemma_keywords = trigger_data.get("lemma_keywords", keywords)
            base_scores = trigger_data["scores"]
            category = trigger_data["category"]

            matched_text = None

            # Try exact match first (on lemmatized text)
            for keyword, lemma_keyword in zip(keywords, lemma_keywords):
                # Use word boundaries to avoid substring matches
                pattern = r'\b' + re.escape(lemma_keyword) + r'\b'
                if re.search(pattern, text_lemmatized):
                    matched_text = keyword
                    break

            # Try fuzzy match if exact match failed and rapidfuzz available
            if not matched_text and RAPIDFUZZ_AVAILABLE:
                for keyword, lemma_keyword in zip(keywords, lemma_keywords):
                    if match_keyword_fuzzy(lemma_keyword, text_lemmatized, threshold=90):
                        matched_text = keyword
                        break

            if matched_text:
                # Check for negation
                if self._detect_negation(text_lower, matched_text):
                    continue  # Skip negated triggers

                # Detect intensity modifier
                intensity_multiplier = self._detect_intensity_modifier(text_lower, matched_text)

                detected.append({
                    "trigger_name": trigger_name,
                    "matched_text": matched_text,
                    "base_scores": base_scores.copy(),
                    "intensity_multiplier": intensity_multiplier,
                    "negated": False,
                    "category": category
                })

        return detected

    def _apply_synergy_rules(self, detected_triggers: List[Dict[str, Any]], scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Apply synergy rules based on combinations of triggers.

        Args:
            detected_triggers: List of detected triggers
            scores: Current scores dictionary (will be modified)

        Returns:
            List of synergy details for reason tracking
        """
        synergy_details = []

        # Count GI triggers (food + meal_pattern categories)
        gi_triggers = [t for t in detected_triggers if t["category"] in ["food", "meal_pattern"]]

        # Synergy: ≥3 distinct GI triggers → GA +0.10
        if len(gi_triggers) >= 3:
            scores["GA"] = scores.get("GA", 0.0) + 0.10
            synergy_details.append({
                "type": "synergy",
                "synergy_name": "multiple_gi_triggers",
                "description": f"{len(gi_triggers)} GI triggers detected",
                "scores": {"GA": 0.10}
            })

        return synergy_details

    def _apply_caps(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Apply per-domain caps to prevent overweighting.

        Args:
            scores: Uncapped scores

        Returns:
            Capped scores
        """
        capped = {}
        for domain, score in scores.items():
            cap = self.DOMAIN_CAPS.get(domain, 1.0)
            capped[domain] = min(score, cap)
        return capped

    def get_symptom_aggravators_weights(
        self,
        text: str,
        age: int = None
    ) -> Tuple[Dict[str, float], Dict[str, bool], List[Dict[str, Any]]]:
        """
        Main scoring method for symptom aggravators.

        Args:
            text: Free-text response about what makes symptoms worse
            age: Patient age (required, must be >= 18)

        Returns:
            Tuple of (scores, flags, details):
            - scores: Dict of focus area weights (e.g., {"GA": 0.45, "STR": 0.20})
            - flags: Dict of safety flags (e.g., {"red_flag": True})
            - details: List of trigger details for reason tracking
        """
        # Initialize
        scores = defaultdict(float)
        flags = {}
        details = []

        # Age gating: Only score for adults >= 18
        if age is None or age < 18:
            return (dict(scores), flags, details)

        # Empty input
        if not text or not text.strip():
            return (dict(scores), flags, details)

        # Check for safety flags first
        safety_flags = self._detect_safety_flags(text)
        if safety_flags:
            flags.update(safety_flags)
            # Return immediately if red flag detected (no scoring)
            return (dict(scores), flags, details)

        # Detect all triggers
        detected_triggers = self._detect_triggers(text)

        # Apply base scores with intensity modifiers
        for trigger in detected_triggers:
            trigger_name = trigger["trigger_name"]
            matched_text = trigger["matched_text"]
            base_scores = trigger["base_scores"]
            intensity_multiplier = trigger["intensity_multiplier"]
            category = trigger["category"]

            # Calculate adjusted scores
            adjusted_scores = {}
            for domain, base_score in base_scores.items():
                # Apply intensity modifier
                adjusted_score = base_score * intensity_multiplier

                # Add bonus for high intensity keywords
                if intensity_multiplier > 1.0:
                    adjusted_score = base_score + 0.05  # +0.05 bonus for "always", "every time"
                elif intensity_multiplier < 1.0:
                    adjusted_score = base_score * 0.5  # ×0.5 for "sometimes", "maybe"

                adjusted_scores[domain] = adjusted_score
                scores[domain] += adjusted_score

            # Track detail for reason tracking
            details.append({
                "type": "trigger",
                "trigger_name": trigger_name,
                "matched_text": matched_text,
                "category": category,
                "intensity_multiplier": intensity_multiplier,
                "scores": adjusted_scores
            })

        # Apply synergy rules
        synergy_details = self._apply_synergy_rules(detected_triggers, scores)
        details.extend(synergy_details)

        # Apply caps
        scores_capped = self._apply_caps(dict(scores))

        return (scores_capped, flags, details)

