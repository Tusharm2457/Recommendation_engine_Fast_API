"""
Phase 3 Ruleset: When Did You Last Feel Really Well

Analyzes temporal patterns and triggers for when patient last felt well.
Captures chronicity overlay and specific trigger events (GI infection, post-viral, mold, stress, hormonal).
"""

from typing import Dict, Tuple, List, Any, Optional
from datetime import datetime, timedelta
import re
from ..rulesets.constants import FOCUS_AREAS
from .constants import (
    get_spacy_model,
    preprocess_lexicons,
    lemmatize_text,
    match_keyword_fuzzy,
    RAPIDFUZZ_AVAILABLE
)


class LastFeltWellRuleset:
    """
    Ruleset for 'When did you last feel really well—body and mind?'
    
    Scoring logic:
    1. Chronicity overlay: Based on months since well (STR, COG, MITO)
    2. Trigger detection: GI infection, post-viral, mold, life stressor, hormonal
    
    Age requirement: Only score if age >= 18
    """
    
    # Temporal keywords for parsing
    SEASON_MAPPING = {
        "spring": (3, 15),   # March 15
        "summer": (6, 15),   # June 15
        "fall": (9, 15),     # September 15
        "autumn": (9, 15),   # September 15
        "winter": (12, 15)   # December 15
    }
    
    # Trigger lexicons
    TRIGGER_LEXICONS = {
        "gi_infection": {
            "keywords": [
                "gastroenteritis", "food poisoning", "traveler's diarrhea", "travelers diarrhea",
                "montezuma's revenge", "montezumas revenge", "stomach bug", "stomach flu",
                "gi infection", "intestinal infection", "bad food", "food illness",
                "diarrhea", "dysentery", "giardia", "parasites", "parasite",
                "trip to mexico", "trip to india", "travel", "international travel",
                "bali belly", "delhi belly", "turista"
            ],
            "weights": {"GA": 0.25}
        },
        "antibiotics": {
            "keywords": [
                "antibiotics", "antibiotic", "abx", "amoxicillin", "cipro", "ciprofloxacin",
                "azithromycin", "z-pack", "zpack", "doxycycline", "flagyl", "metronidazole"
            ],
            "weights": {"GA": 0.25}
        },
        "post_viral": {
            "keywords": [
                "covid", "covid-19", "coronavirus", "long covid", "long-covid",
                "mono", "mononucleosis", "epstein-barr", "ebv", "glandular fever",
                "flu", "influenza", "viral infection", "virus", "viral illness",
                "post-viral", "postviral", "after being sick", "after illness"
            ],
            "weights": {"MITO": 0.15, "COG": 0.10, "IMM": 0.10}
        },
        "mold": {
            "keywords": [
                "mold", "mould", "water damage", "water-damage", "water damaged",
                "damp", "dampness", "musty", "leak", "leaks", "flooding", "flooded",
                "black mold", "toxic mold", "mycotoxin", "mycotoxins"
            ],
            "weights": {"DTX": 0.20, "IMM": 0.15, "MITO": 0.05}
        },
        "life_stressor": {
            "keywords": [
                "job change", "new job", "lost job", "laid off", "fired", "unemployment",
                "divorce", "breakup", "break up", "separation", "relationship ended",
                "bereavement", "death", "died", "passed away", "loss",
                "caregiving", "caregiver", "caring for", "taking care of",
                "moved", "moving", "relocation", "new city", "new house",
                "financial stress", "money problems", "debt", "bankruptcy"
            ],
            "weights": {"STR": 0.20, "COG": 0.05, "CM": 0.05}
        },
        "hormonal": {
            "keywords": [
                "pregnancy", "pregnant", "postpartum", "post-partum", "after baby",
                "after birth", "childbirth", "gave birth",
                "menopause", "menopausal", "perimenopause", "peri-menopause",
                "hrt", "hormone replacement", "started hrt", "stopped hrt",
                "birth control", "started pill", "stopped pill", "iud"
            ],
            "weights": {"HRM": 0.20, "STR": 0.05, "IMM": 0.05}
        }
    }
    
    def __init__(self):
        """Initialize the ruleset and preprocess lexicons."""
        # Load shared spaCy model
        self.nlp = get_spacy_model()
        
        # Pre-lemmatize all trigger keywords
        self.lemmatized_lexicons = preprocess_lexicons(
            {k: v["keywords"] for k, v in self.TRIGGER_LEXICONS.items()},
            self.nlp
        )
    
    def get_last_felt_well_weights(
        self,
        text: str,
        age: int = None,
        current_date: datetime = None
    ) -> Tuple[Dict[str, float], Dict[str, bool], List[Dict[str, Any]]]:
        """
        Calculate focus area weights from 'last felt well' text.
        
        Args:
            text: Patient's response about when they last felt well
            age: Patient's age (required, must be >= 18)
            current_date: Reference date for temporal calculations (defaults to today)
        
        Returns:
            Tuple of (scores_dict, flags_dict, detail_list)
            - scores_dict: Focus area scores
            - flags_dict: {"temporal_uncertain": bool}
            - detail_list: List of dicts with breakdown for reason tracking
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        flags = {"temporal_uncertain": False}
        details = []
        
        # Age check: Only score if age >= 18
        if age is None or age < 18:
            return scores, flags, details
        
        # Handle empty input
        if not text or not text.strip():
            return scores, flags, details
        
        text_lower = text.lower().strip()
        
        # Set current date
        if current_date is None:
            current_date = datetime.now()
        
        # Step 1: Parse temporal information
        months_since_well, temporal_uncertain = self._parse_temporal(text_lower, current_date)
        flags["temporal_uncertain"] = temporal_uncertain
        
        # Step 2: Apply chronicity overlay
        chronicity_scores = self._apply_chronicity_overlay(months_since_well)
        if chronicity_scores:
            for domain, weight in chronicity_scores.items():
                scores[domain] += weight
            
            # Track chronicity contribution
            chronicity_label = self._get_chronicity_label(months_since_well)
            details.append({
                "type": "chronicity",
                "label": chronicity_label,
                "months": months_since_well,
                "scores": {k: v for k, v in chronicity_scores.items() if v > 0}
            })

        # Step 3: Detect triggers
        trigger_scores = self._detect_triggers(text_lower)

        # Track each trigger separately
        for trigger_name, trigger_data in trigger_scores.items():
            trigger_weights = trigger_data["scores"]
            for domain, weight in trigger_weights.items():
                scores[domain] += weight

            details.append({
                "type": "trigger",
                "trigger_name": trigger_name,
                "matched_text": trigger_data["matched_text"],
                "scores": trigger_weights
            })

        # Step 4: Apply per-field cap (max +0.45 per domain from this field)
        for domain in scores:
            if scores[domain] > 0.45:
                scores[domain] = 0.45

        return scores, flags, details

    def _parse_temporal(self, text: str, current_date: datetime) -> Tuple[int, bool]:
        """
        Parse temporal information from text and return months since well.

        Returns:
            Tuple of (months_since_well, temporal_uncertain)
        """
        temporal_uncertain = False

        # Handle "never felt well" cases
        never_patterns = [
            r'\bnever\b.*\bwell\b',
            r'\bnever\b.*\bfelt\b.*\bgood\b',
            r'\bcan\'?t\s+remember\b',
            r'\bdon\'?t\s+remember\b'
        ]
        for pattern in never_patterns:
            if re.search(pattern, text):
                return 120, False  # Use 120 months (10 years) as lower bound

        # Try to extract relative time FIRST (e.g., "2 years ago", "6 months ago")
        # This takes precedence over year extraction
        relative_match = re.search(r'(\d+)\s*(year|month|yr|mo)s?\s*ago', text)
        if relative_match:
            number = int(relative_match.group(1))
            unit = relative_match.group(2)

            if unit in ['year', 'yr']:
                months_since = number * 12
            else:  # month, mo
                months_since = number

            return months_since, False

        # Try to extract year (e.g., "2022", "Summer 2022", "in 2021", "around 2021")
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            year = int(year_match.group())

            # Check for season
            season_found = None
            for season, (month, day) in self.SEASON_MAPPING.items():
                if season in text:
                    season_found = (month, day)
                    break

            if season_found:
                # Use season midpoint
                anchor_date = datetime(year, season_found[0], season_found[1])
            else:
                # Use mid-year if no season specified
                anchor_date = datetime(year, 6, 15)

            # Calculate months since
            delta = current_date - anchor_date
            months_since = max(0, int(delta.days / 30))
            return months_since, False

        # Check for relative phrases like "before job change", "after moving", "since COVID"
        # WITHOUT a year - use conservative estimate
        relative_phrases = [
            r'\bbefore\b', r'\bafter\b', r'\bsince\b', r'\bwhen\b',
            r'\bduring\b', r'\baround\b'
        ]
        has_relative_phrase = False
        for pattern in relative_phrases:
            if re.search(pattern, text):
                has_relative_phrase = True
                break

        if has_relative_phrase:
            temporal_uncertain = True
            # Use conservative estimate (24 months for sub-chronic)
            return 24, temporal_uncertain

        # If we can't parse anything, mark as uncertain and return 0
        return 0, True

    def _apply_chronicity_overlay(self, months_since_well: int) -> Dict[str, float]:
        """
        Apply chronicity overlay based on months since well.

        Chronicity bands:
        - <= 12 months: No overlay
        - 13-36 months (sub-chronic): STR +0.15, COG +0.10, MITO +0.05
        - > 36 months (chronic): STR +0.25, COG +0.20, MITO +0.10
        """
        scores = {}

        if months_since_well <= 12:
            # No chronicity overlay
            return scores
        elif 13 <= months_since_well <= 36:
            # Sub-chronic
            scores["STR"] = 0.15
            scores["COG"] = 0.10
            scores["MITO"] = 0.05
        else:  # > 36 months
            # Chronic
            scores["STR"] = 0.25
            scores["COG"] = 0.20
            scores["MITO"] = 0.10

        return scores

    def _get_chronicity_label(self, months_since_well: int) -> str:
        """Get human-readable chronicity label."""
        if months_since_well <= 12:
            return "recent"
        elif 13 <= months_since_well <= 36:
            return "sub_chronic"
        else:
            return "chronic"

    def _detect_triggers(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Detect trigger events in the text.

        Returns:
            Dict mapping trigger_name to {"matched_text": str, "scores": dict}
        """
        triggers_found = {}

        # Lemmatize input text
        text_lemmatized = lemmatize_text(text, self.nlp) if self.nlp else text

        # Check each trigger category
        for trigger_name, trigger_config in self.TRIGGER_LEXICONS.items():
            matched_keywords = []

            # Get lemmatized keywords for this trigger
            lemmatized_keywords = self.lemmatized_lexicons.get(trigger_name, set())

            # Try exact match first (on lemmatized text)
            for lemma_keyword in lemmatized_keywords:
                if lemma_keyword in text_lemmatized:
                    # Find original keyword that matched
                    for orig_keyword in trigger_config["keywords"]:
                        if lemmatize_text(orig_keyword, self.nlp) == lemma_keyword:
                            matched_keywords.append(orig_keyword)
                            break

            # If no exact match, try fuzzy matching
            if not matched_keywords and RAPIDFUZZ_AVAILABLE:
                for keyword in trigger_config["keywords"]:
                    if match_keyword_fuzzy(keyword, text, threshold=85):
                        matched_keywords.append(keyword)

            # If trigger matched, record it
            if matched_keywords:
                triggers_found[trigger_name] = {
                    "matched_text": matched_keywords[0],  # Use first match
                    "scores": trigger_config["weights"].copy()
                }

        # Special handling: GI infection + antibiotics escalation
        if "gi_infection" in triggers_found and "antibiotics" in triggers_found:
            # Escalate GA from 0.25 to 0.35 (cap at 0.35)
            triggers_found["gi_infection"]["scores"]["GA"] = 0.35
            # Remove antibiotics as separate trigger to avoid double-counting
            del triggers_found["antibiotics"]

        # Special handling: Post-viral + GI symptoms co-mention
        if "post_viral" in triggers_found:
            # Check if GI symptoms are mentioned
            gi_symptom_keywords = ["bloat", "gas", "diarrhea", "constipation", "stomach", "gut", "digestive", "ibs"]
            has_gi_symptoms = any(kw in text for kw in gi_symptom_keywords)

            if has_gi_symptoms:
                # Add GA +0.05 to post-viral scores
                triggers_found["post_viral"]["scores"]["GA"] = 0.05

        return triggers_found

