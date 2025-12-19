from typing import Dict, Any, List, Tuple
import re
from src.aether_2.utils.text_processing import split_by_delimiters
from .constants import (
    FOCUS_AREAS,
    get_spacy_model,
    preprocess_lexicons,
    lemmatize_text,
    match_keyword_fuzzy,
    RAPIDFUZZ_AVAILABLE
)


class HealthGoalsRuleset:

    def __init__(self):
        """Initialize the ruleset with NLP models."""
        # Load shared spaCy model
        self.nlp = get_spacy_model()

        # Pre-lemmatize all keywords for faster matching
        self.lemmatized_lexicons = preprocess_lexicons(self.LEXICONS, self.nlp) if self.nlp else {}

    CAPS = {
        "CM": 0.60,
        "COG": 0.60,
        "MITO": 0.60,
        "GA": 0.60,
        "STR": 0.50,
        "IMM": 0.40,
        "DTX": 0.35,
        "HRM": 0.35,
        "SKN": 0.30
    }
    
    # Safety flags
    CRISIS_KEYWORDS = ["suicidal", "self-harm", "self harm", "kill myself", "end my life"]
    URGENT_CARE_KEYWORDS = ["chest pain", "worst headache", "blood in stool", "severe chest pain"]
    
    # Intensity modifiers
    INTENSIFIERS = ["severe", "debilitating", "urgent", "constant", "chronic", "extreme", "intense"]
    
    # Lexicons for goal mapping
    LEXICONS = {
        "GA": [
            "bloat", "bloating", "gas", "burp", "belch", "reflux", "heartburn", "gerd",
            "constipation", "diarrhea", "diarrhoea", "loose stools", "ibs", "sibo",
            "celiac", "coeliac", "leaky gut", "abdominal pain", "cramps", "nausea",
            "stool issues", "fodmap", "low-fodmap", "histamine after foods", "indigestion"
        ],
        "CM": [
            "lose weight", "weight loss", "metabolic health", "reverse prediabetes",
            "lower a1c", "lower blood sugar", "improve cholesterol", "heart health",
            "blood pressure", "cardiovascular", "metabolic"
        ],
        "COG": [
            "brain fog", "focus", "concentrate", "memory", "mental clarity", "productivity",
            "cognitive", "mental sharpness"
        ],
        "MITO": [
            "fatigue", "low energy", "stamina", "burnout", "exhaustion", "vitality",
            "increase energy", "energy levels", "energy", "improve energy"
        ],
        "STR": [
            "reduce stress", "anxiety", "anxious", "calm", "resilience", "burnout", "improve sleep",
            "sleep better", "insomnia", "circadian rhythm", "stress management", "stressed"
        ],
        "HRM": [
            "balance hormones", "thyroid", "pcos", "pcos symptoms", "menopause",
            "perimenopause", "hot flashes", "cycles", "pms", "low testosterone", "libido"
        ],
        "DTX": [
            "detox", "cleanse", "reduce toxins", "mold detox", "chemical sensitivity",
            "reduce exposure", "heavy metals", "detoxification"
        ],
        "IMM": [
            "lower inflammation", "autoimmune remission", "allergies", "histamine intolerance",
            "reduce flares", "inflammatory", "immune", "inflammation", "reduce inflammation"
        ],
        "SKN": [
            "clear skin", "acne", "eczema", "psoriasis", "rashes", "dermatitis", "skin issues",
            "skin", "clear my skin"
        ]
    }
    
    # Pain/musculoskeletal keywords (cross-maps to multiple domains)
    PAIN_KEYWORDS = [
        "reduce pain", "joint pain", "stiffness", "back pain", "migraines", "headaches",
        "chronic pain", "muscle pain"
    ]
    
    # Longevity/prevention keywords
    LONGEVITY_KEYWORDS = [
        "longevity", "age well", "prevention", "healthy aging", "anti-aging",
        "long aging", "aging well", "live longer"
    ]



    def get_health_goals_weights(
        self,
        health_goals_text: str,
        age: int = None
    ) -> Tuple[Dict[str, float], Dict[str, bool], List[Dict[str, Any]]]:
        """
        Score health goals text and return focus area weights plus safety flags.

        Args:
            health_goals_text: Free text containing health goals
            age: Patient age (for validation)

        Returns:
            Tuple of (scores_dict, safety_flags_dict, goal_details_list)
            - scores_dict: Focus area scores
            - safety_flags: {"crisis": bool, "urgent_care": bool}
            - goal_details: List of dicts with per-goal breakdown for reason tracking
              [{"rank": 1, "goal_text": "lose weight", "matched_domains": ["CM"], "weight": 0.35, "scores": {"CM": 0.35}}]
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        safety_flags = {"crisis": False, "urgent_care": False}
        goal_details = []  # Track individual goal contributions

        # Safety check: age < 18 or empty text
        if age and age < 18:
            return scores, safety_flags, goal_details
        if not health_goals_text or not health_goals_text.strip():
            return scores, safety_flags, goal_details

        # 1) Normalize and split
        normalized_text = self._normalize_text(health_goals_text)

        # Safety intercept
        safety_flags = self._check_safety_flags(normalized_text)
        if safety_flags["crisis"]:
            # Return scores but with crisis flag set
            return scores, safety_flags, goal_details

        # Split goals using shared utility function
        goals = split_by_delimiters(normalized_text)[:3]  # Keep first 3 unique

        if not goals:
            return scores, safety_flags, goal_details

        # Priority weights by rank
        weights_by_rank = [0.35, 0.30, 0.25]

        # Process each goal
        for i, goal in enumerate(goals):
            if i >= len(weights_by_rank):
                break

            # Check for negation
            if self._is_negated(goal):
                continue

            weight = weights_by_rank[i]

            # Match intents (returns list of (domain, fraction) tuples)
            intents = self._match_intents(goal)

            if not intents:
                continue

            # Track per-goal scores for reason tracking
            goal_scores = {code: 0.0 for code in FOCUS_AREAS}

            # Apply base weight to each mapped domain
            for domain, fraction in intents:
                contribution = weight * fraction
                scores[domain] += contribution
                goal_scores[domain] += contribution

            # Intensity modifier
            if self._has_intensifier(goal):
                for domain, _ in intents:
                    scores[domain] += 0.05
                    goal_scores[domain] += 0.05

            # Apply bonus logic
            scores = self._apply_bonus_logic(goal, scores, intents)
            goal_scores = self._apply_bonus_logic(goal, goal_scores, intents)

            # Record goal details for reason tracking
            matched_domains = [domain for domain, _ in intents]
            goal_details.append({
                "rank": i + 1,
                "goal_text": goal.strip(),
                "matched_domains": matched_domains,
                "base_weight": weight,
                "scores": {k: v for k, v in goal_scores.items() if v > 0}  # Only non-zero
            })

        # Apply caps
        for domain in scores:
            scores[domain] = min(scores[domain], self.CAPS.get(domain, 1.0))

        return scores, safety_flags, goal_details
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip punctuation, normalize spellings."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Normalize common typos and synonyms
        replacements = {
            "diarrhoea": "diarrhea",
            "stomach acid": "heartburn",
            "stomachache": "abdominal pain",
            "tummy": "abdominal",
            "poop": "stool",
            "bm": "bowel movement"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove punctuation (keep spaces and basic separators)
        text = re.sub(r'[^\w\s;,\-]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _split_goals(self, text: str) -> List[str]:
        """Split goals by semicolons, line breaks, 'and', commas."""
        if not text:
            return []
        
        # Split by semicolons first
        parts = re.split(r'[;\n]', text)
        
        # Then split by ' and ' and commas
        all_parts = []
        for part in parts:
            # Split by ' and ' (with word boundaries)
            sub_parts = re.split(r'\s+and\s+', part, flags=re.IGNORECASE)
            for sub_part in sub_parts:
                # Split by commas
                comma_parts = [p.strip() for p in sub_part.split(',')]
                all_parts.extend(comma_parts)
        
        # Clean and filter empty
        goals = [g.strip() for g in all_parts if g.strip()]
        return goals
    
    def _dedupe_goals(self, goals: List[str]) -> List[str]:
        """Remove duplicates while preserving order."""
        seen = set()
        unique = []
        for goal in goals:
            goal_lower = goal.lower().strip()
            if goal_lower and goal_lower not in seen:
                seen.add(goal_lower)
                unique.append(goal)
        return unique
    
    def _is_negated(self, text: str) -> bool:
        """Check if text is negated (preceded by 'no', 'not', 'without')."""
        text_lower = text.lower().strip()
        negation_patterns = [
            r'^no\s+',
            r'^not\s+',
            r'^without\s+',
            r'\bno\s+',
            r'\bnot\s+',
            r'\bwithout\s+'
        ]
        for pattern in negation_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _check_safety_flags(self, text: str) -> Dict[str, bool]:
        """Check for crisis and urgent care keywords."""
        flags = {"crisis": False, "urgent_care": False}
        text_lower = text.lower()
        
        # Check crisis keywords
        for keyword in self.CRISIS_KEYWORDS:
            if keyword in text_lower:
                flags["crisis"] = True
                break
        
        # Check urgent care keywords
        for keyword in self.URGENT_CARE_KEYWORDS:
            if keyword in text_lower:
                flags["urgent_care"] = True
                break
        
        return flags
    
    def _has_intensifier(self, text: str) -> bool:
        """Check if text contains intensity modifiers."""
        text_lower = text.lower()
        for intensifier in self.INTENSIFIERS:
            if intensifier in text_lower:
                return True
        return False
    
    def _match_intents(self, goal: str) -> List[Tuple[str, float]]:
        """
        Hybrid matching pipeline:
        1. Try lemmatized match (fast path) - handles word forms
        2. If no match, try fuzzy match (slow path) - handles typos
        3. Apply cross-mapping logic (pain, longevity, sleep)

        Returns list of (domain, fraction) tuples.
        """
        intents = []
        goal_lower = goal.lower()

        # STAGE 1: Lemmatized matching (fast path)
        if self.nlp and self.lemmatized_lexicons:
            goal_lemmatized = lemmatize_text(goal_lower, self.nlp)

            for domain, lemma_keywords in self.lemmatized_lexicons.items():
                for lemma_keyword in lemma_keywords:
                    if lemma_keyword in goal_lemmatized:
                        intents.append((domain, 1.0))
                        break  # Only match once per domain per goal

        # STAGE 2: Fuzzy matching fallback (slow path) - only if no exact match
        if not intents and RAPIDFUZZ_AVAILABLE:
            for domain, keywords in self.LEXICONS.items():
                for keyword in keywords:
                    if match_keyword_fuzzy(keyword, goal_lower, threshold=85):
                        intents.append((domain, 0.95))  # Slightly lower confidence for fuzzy
                        break  # Only match once per domain per goal

        # STAGE 3: Fallback to simple substring (if no NLP libraries available)
        if not intents:
            for domain, keywords in self.LEXICONS.items():
                for keyword in keywords:
                    if keyword in goal_lower:
                        intents.append((domain, 1.0))
                        break  # Only match once per domain per goal

        # CROSS-MAPPING LOGIC (same as before)

        # Check pain/musculoskeletal (cross-maps)
        pain_matched = False
        for keyword in self.PAIN_KEYWORDS:
            # Use lemmatized matching if available
            if self.nlp:
                keyword_lemma = lemmatize_text(keyword, self.nlp)
                goal_lemmatized = lemmatize_text(goal_lower, self.nlp)
                if keyword_lemma in goal_lemmatized:
                    pain_matched = True
                    break
            elif keyword in goal_lower:
                pain_matched = True
                break

        if pain_matched:
            # Cross-map: STR, IMM, MITO
            if ("STR", 1.0) not in intents:
                intents.append(("STR", 1.0))
            if ("IMM", 1.0) not in intents:
                intents.append(("IMM", 1.0))
            if ("MITO", 1.0) not in intents:
                intents.append(("MITO", 1.0))

            # If migraines/headaches + focus/clarity phrase
            if any(term in goal_lower for term in ["migraine", "headache", "headaches"]):
                if any(term in goal_lower for term in ["focus", "clarity", "concentrate"]):
                    if ("COG", 1.0) not in intents:
                        intents.append(("COG", 1.0))

        # Check longevity/prevention
        longevity_matched = False
        for keyword in self.LONGEVITY_KEYWORDS:
            # Use lemmatized matching if available
            if self.nlp:
                keyword_lemma = lemmatize_text(keyword, self.nlp)
                goal_lemmatized = lemmatize_text(goal_lower, self.nlp)
                if keyword_lemma in goal_lemmatized:
                    longevity_matched = True
                    break
            elif keyword in goal_lower:
                longevity_matched = True
                break

        if longevity_matched:
            # Distributed: CM, MITO, IMM
            if ("CM", 1.0) not in intents:
                intents.append(("CM", 1.0))
            if ("MITO", 1.0) not in intents:
                intents.append(("MITO", 1.0))
            if ("IMM", 1.0) not in intents:
                intents.append(("IMM", 1.0))

        # Special handling for sleep-related goals (STR + COG)
        sleep_terms = ["improve sleep", "sleep better", "sleep quality", "better sleep"]
        sleep_matched = False
        for term in sleep_terms:
            if self.nlp:
                term_lemma = lemmatize_text(term, self.nlp)
                goal_lemmatized = lemmatize_text(goal_lower, self.nlp)
                if term_lemma in goal_lemmatized:
                    sleep_matched = True
                    break
            elif term in goal_lower:
                sleep_matched = True
                break

        if sleep_matched:
            if ("COG", 1.0) not in intents:
                intents.append(("COG", 1.0))

        # Dedupe intents (keep first occurrence)
        seen = set()
        unique_intents = []
        for domain, fraction in intents:
            if domain not in seen:
                seen.add(domain)
                unique_intents.append((domain, fraction))

        return unique_intents if unique_intents else []
    
    def _apply_bonus_logic(self, goal: str, scores: Dict[str, float], intents: List[Tuple[str, float]]) -> Dict[str, float]:
        """Apply bonus logic for specific terms."""
        goal_lower = goal.lower()
        
        # FODMAP → IMM +0.05
        if "fodmap" in goal_lower:
            scores["IMM"] += 0.05
        
        # Histamine → IMM +0.05
        if "histamine" in goal_lower:
            scores["IMM"] += 0.05
        
        # Skin issues → IMM +0.05 and GA +0.05
        skin_keywords = ["acne", "eczema", "psoriasis", "rashes", "dermatitis", "clear skin"]
        if any(keyword in goal_lower for keyword in skin_keywords):
            scores["IMM"] += 0.05
            scores["GA"] += 0.05
        
        # Detox/chemicals → IMM +0.05
        if any(term in goal_lower for term in ["detox", "cleanse", "reduce toxins", "chemical"]):
            scores["IMM"] += 0.05
        
        # Pain/musculoskeletal cross-map bonuses
        # Base weights are applied in match_intents, but we need to ensure proper distribution
        # The base weight (0.35/0.30/0.25) goes to STR, IMM, MITO equally
        # Additional COG bonus for migraines+focus is handled in match_intents
        
        # Longevity/prevention bonuses
        # Base weights are applied in match_intents to CM, MITO, IMM
        # The distributed nature is handled by the base weight application
        
        return scores

