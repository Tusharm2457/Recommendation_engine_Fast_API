"""
Phase 3 Ruleset: Food Avoidance (Field 17)
"Any foods you avoid because they cause issues?"

Analyzes foods avoided due to symptoms using NLP-based pattern matching.
Detects gluten, lactose, FODMAPs, histamine, GERD triggers, nightshades, and broad sensitivities.
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
from .helpers import parse_yes_no_with_followup


class FoodAvoidanceRuleset:
    """
    Ruleset for scoring foods avoided due to symptoms.
    
    Detects 7 main categories:
    1. Gluten/wheat
    2. Lactose/dairy
    3. High-FODMAP foods
    4. Histamine-rich foods
    5. GERD-promoting foods
    6. Nightshades
    7. Broad sensitivities (≥4 distinct foods)
    
    Features:
    - NLP-based keyword matching with lemmatization + fuzzy matching
    - Symptom linking (bloating, reflux, hives, etc.)
    - Skin symptom detection for SKN scoring
    - Elimination response detection (confidence boost)
    - Per-domain caps
    """
    
    # Per-domain caps for this field
    DOMAIN_CAPS = {
        "GA": 1.5,
        "IMM": 0.6,
        "SKN": 0.3,
        "STR": 0.1
    }
    
    # Safety keywords (immediate reactions)
    SAFETY_KEYWORDS = [
        "anaphylaxis", "throat closing", "throat swelling", "can't breathe",
        "angioedema", "severe hives", "epipen", "emergency"
    ]
    
    def __init__(self):
        """Initialize the ruleset with NLP model and food category lexicons."""
        self.nlp = get_spacy_model()
        self._build_food_lexicons()
        self._build_symptom_lexicons()
    
    def _build_food_lexicons(self):
        """
        Build food category lexicons with keywords and base weights.
        
        Structure: {
            "category_name": {
                "keywords": [...],
                "scores": {"GA": 0.45, ...},
                "skin_boost": 0.10  # Optional SKN boost if skin symptoms present
            }
        }
        """
        self.food_categories = {
            # 1) Gluten/wheat
            "gluten_wheat": {
                "keywords": [
                    "gluten", "wheat", "bread", "pasta", "cereal", "flour",
                    "barley", "rye", "malt", "seitan", "couscous", "semolina"
                ],
                "scores": {"GA": 0.45, "IMM": 0.15},
                "skin_boost": 0.10
            },
            
            # 2) Lactose/dairy
            "lactose_dairy": {
                "keywords": [
                    "milk", "dairy", "lactose", "ice cream", "cheese", "yogurt",
                    "cream", "butter", "whey", "casein", "kefir"
                ],
                "scores": {"GA": 0.35, "IMM": 0.10},
                "skin_boost": 0.15
            },
            
            # 3) High-FODMAP foods
            "high_fodmap": {
                "keywords": [
                    "garlic", "onion", "beans", "lentils", "chickpeas",
                    "apples", "pears", "stone fruit", "peaches", "plums",
                    "cauliflower", "broccoli", "cabbage", "brussels sprouts",
                    "wheat", "rye", "honey", "agave", "high fructose"
                ],
                "scores": {"GA": 0.35, "IMM": 0.10},
                "skin_boost": 0.0
            },
            
            # 4) Histamine-rich foods
            "histamine_rich": {
                "keywords": [
                    "aged cheese", "wine", "beer", "alcohol", "cured meat",
                    "salami", "pepperoni", "bacon", "ham", "sausage",
                    "vinegar", "kombucha", "fermented", "sauerkraut", "kimchi",
                    "leftovers", "tinned fish", "canned fish", "tuna", "sardines",
                    "tomato", "spinach", "eggplant", "avocado", "banana"
                ],
                "scores": {"GA": 0.35, "IMM": 0.20},
                "skin_boost": 0.15
            },
            
            # 5) GERD-promoting foods
            "gerd_triggers": {
                "keywords": [
                    "spicy", "chili", "hot sauce", "capsaicin", "pepper",
                    "fried", "fatty", "greasy", "oily",
                    "large meal", "late meal", "eating late", "late night",
                    "carbonated", "soda", "pop", "fizzy", "sparkling",
                    "acidic", "citrus", "orange", "lemon", "grapefruit",
                    "coffee", "caffeine", "chocolate", "mint", "peppermint"
                ],
                "scores": {"GA": 0.20, "STR": 0.05},
                "skin_boost": 0.0
            },
            
            # 6) Nightshades
            "nightshades": {
                "keywords": [
                    "nightshade", "tomato", "potato", "bell pepper", "peppers",
                    "eggplant", "aubergine", "goji", "paprika"
                ],
                "scores": {"GA": 0.10, "IMM": 0.10},
                "skin_boost": 0.10
            }
        }

    def _build_symptom_lexicons(self):
        """Build symptom keyword lists for linking foods to symptoms."""
        self.symptoms = {
            "gi_symptoms": [
                "bloating", "gas", "cramps", "cramping", "diarrhea", "loose stool",
                "constipation", "nausea", "vomiting", "reflux", "heartburn",
                "acid", "burning", "indigestion", "upset stomach", "pain"
            ],
            "skin_symptoms": [
                "rash", "hives", "eczema", "psoriasis", "acne", "breakout",
                "itchy", "itching", "flush", "flushing", "red", "redness"
            ],
            "neuro_symptoms": [
                "headache", "migraine", "brain fog", "foggy", "dizzy", "fatigue"
            ],
            "immediate_reactions": [
                "hives", "angioedema", "anaphylaxis", "throat closing",
                "swelling", "epipen", "emergency"
            ]
        }

        self.elimination_keywords = [
            "removing", "removed", "stopped", "quit", "avoiding", "eliminated",
            "fixed", "helped", "better", "improved", "resolved"
        ]

    def _detect_safety_flags(self, text: str) -> List[str]:
        """Detect safety keywords that require immediate attention."""
        text_lower = text.lower()
        flags = []

        for keyword in self.SAFETY_KEYWORDS:
            if keyword in text_lower:
                flags.append(f"SAFETY: {keyword}")

        return flags

    def _detect_skin_symptoms(self, text: str) -> bool:
        """Check if text mentions skin-related symptoms."""
        text_lower = text.lower()
        return any(symptom in text_lower for symptom in self.symptoms["skin_symptoms"])

    def _detect_elimination_response(self, text: str) -> bool:
        """Check if user reports improvement after eliminating foods."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.elimination_keywords)

    def _count_distinct_foods(self, text: str) -> int:
        """
        Count distinct food groups mentioned.
        Used for "broad sensitivities" rule (≥4 foods).
        """
        text_lower = text.lower()
        food_groups_found = set()

        # Check each category
        for category, data in self.food_categories.items():
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    food_groups_found.add(category)
                    break

        return len(food_groups_found)

    def _detect_gerd_severity(self, text: str) -> float:
        """
        Detect GERD severity modifiers.
        Returns multiplier for GERD scores (1.0 to 1.25).
        """
        text_lower = text.lower()

        # Check for late/large meals or carbonated drinks (higher GA score)
        if any(kw in text_lower for kw in ["late meal", "late night", "eating late", "large meal", "big meal", "carbonated", "soda"]):
            return 1.25  # GA +0.25 instead of +0.20

        return 1.0  # Base GA +0.20

    def get_food_avoidance_weights(
        self,
        avoidance_data: Any,
        age: int = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on foods avoided.

        Args:
            avoidance_data: Yes/No with followup text (e.g., "Yes; Gluten → bloating; Milk → cramps")
            age: Patient age (must be >= 18)

        Returns:
            Tuple of (weights dict, flags list)
            - weights: Dict mapping focus area codes to weight adjustments
            - flags: List of safety flags or special notes
        """
        # Initialize
        weights = defaultdict(float)
        flags = []

        # Age gating (adults only)
        if age is not None and age < 18:
            return dict(weights), flags

        # Parse Yes/No with followup
        is_yes, followup_text = parse_yes_no_with_followup(avoidance_data)

        if not is_yes or not followup_text:
            return dict(weights), flags

        # Normalize text
        text_lower = followup_text.lower().strip()

        if not text_lower:
            return dict(weights), flags

        # Check for safety flags
        safety_flags = self._detect_safety_flags(text_lower)
        flags.extend(safety_flags)

        # Detect skin symptoms (for SKN boost)
        has_skin_symptoms = self._detect_skin_symptoms(text_lower)

        # Detect elimination response (for confidence boost)
        has_elimination_response = self._detect_elimination_response(text_lower)

        # Count distinct foods (for broad sensitivities rule)
        distinct_food_count = self._count_distinct_foods(text_lower)

        # Track matched categories for explainability
        matched_categories = []

        # ===== SCORE EACH FOOD CATEGORY =====
        for category, data in self.food_categories.items():
            category_matched = False

            # Check if any keyword matches
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    category_matched = True
                    break

            if not category_matched:
                continue

            matched_categories.append(category)

            # Apply base scores
            for domain, score in data["scores"].items():
                weights[domain] += score

            # Apply skin boost if skin symptoms mentioned
            if has_skin_symptoms and data.get("skin_boost", 0) > 0:
                weights["SKN"] += data["skin_boost"]

            # Special handling for GERD triggers (severity modifier)
            if category == "gerd_triggers":
                gerd_multiplier = self._detect_gerd_severity(text_lower)
                if gerd_multiplier > 1.0:
                    # Adjust GA score from +0.20 to +0.25
                    weights["GA"] += 0.05

        # ===== BROAD SENSITIVITIES RULE =====
        # If ≥4 distinct food groups OR user says "many foods"
        if distinct_food_count >= 4 or any(phrase in text_lower for phrase in ["many foods", "lots of foods", "multiple foods", "several foods"]):
            weights["GA"] += 0.45
            weights["IMM"] += 0.30
            weights["SKN"] += 0.20
            flags.append("Broad sensitivities detected (≥4 food groups)")

        # ===== ELIMINATION RESPONSE BOOST =====
        # If user reports improvement after eliminating foods, boost confidence
        if has_elimination_response:
            # Multiply GA/IMM/SKN weights by 1.1× (cap per-item at +0.60)
            for domain in ["GA", "IMM", "SKN"]:
                if weights[domain] > 0:
                    weights[domain] = min(weights[domain] * 1.1, 0.60)
            flags.append("Elimination response reported")

        # ===== IMMEDIATE REACTIONS (SAFETY + SCORING) =====
        # Check for immediate/severe reactions
        if any(kw in text_lower for kw in self.symptoms["immediate_reactions"]):
            weights["IMM"] += 0.60
            weights["SKN"] += 0.30
            flags.append("SAFETY: Immediate/severe reaction reported")

        # ===== APPLY DOMAIN CAPS =====
        for domain, cap in self.DOMAIN_CAPS.items():
            if weights[domain] > cap:
                weights[domain] = cap

        # Add explainability note
        if matched_categories:
            flags.append(f"Detected: {', '.join(matched_categories)}")

        return dict(weights), flags

