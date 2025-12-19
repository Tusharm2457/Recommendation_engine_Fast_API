"""
Food Cravings Ruleset (Field 18) - Phase 3

Evaluates food cravings patterns and their impact on focus areas.
Uses simple substring matching on normalized multi-select input.

UI: Multi-select chips — Sweets · Salty · Bread/Pasta · Chocolate · Caffeine · None/NO/NA · Other (short text)
"""

from typing import Dict, List, Tuple, Any
import re


class FoodCravingsRuleset:
    """
    Ruleset for evaluating food cravings impact on focus areas.
    
    Accepted values: {Sweets, Salty, Bread/Pasta, Chocolate, Caffeine, None, Other(+text)}
    """
    
    # Domain caps for this field
    DOMAIN_CAPS = {
        "CM": 1.5,
        "COG": 1.5,
        "DTX": 1.5,
        "GA": 1.5,
        "IMM": 1.5,
        "MITO": 1.5,
        "STR": 1.5,
        "HRM": 1.5,
        "SKN": 1.5
    }
    
    # Base weights for each craving type
    CRAVING_WEIGHTS = {
        "sweets": {
            "CM": 0.60,
            "MITO": 0.25,
            "IMM": 0.15,
            "GA": 0.30,
            "STR": 0.10
        },
        "bread_pasta": {
            "CM": 0.50,
            "GA": 0.30,
            "MITO": 0.20
        },
        "chocolate": {
            "STR": 0.15,
            "COG": 0.10,
            "GA": 0.10
        },
        "caffeine": {
            "STR": 0.40,
            "COG": 0.20,
            "GA": 0.10
        },
        "salty": {
            # Neutral by default, only scores with special conditions
        }
    }
    
    # "Other" category lexicon
    OTHER_LEXICON = {
        "alcohol": {
            "DTX": 0.40,
            "CM": 0.20,
            "GA": 0.20
        },
        "energy_drink": {
            "STR": 0.30,
            "COG": 0.15,
            "GA": 0.10
        },
        "fast_food": {
            "CM": 0.40,
            "IMM": 0.20,
            "GA": 0.25
        },
        "ultra_processed": {
            "CM": 0.40,
            "IMM": 0.20,
            "GA": 0.25
        },
        "late_night": {
            "STR": 0.20,
            "CM": 0.15,
            "GA": 0.15
        }
    }
    
    # Frequency terms for intensity multiplier
    HIGH_FREQUENCY_TERMS = ["daily", "every day", "everyday", ">5/wk", "5+/wk"]
    MODERATE_FREQUENCY_TERMS = ["2-5/wk", "3-5/wk", "few times a week", "several times"]
    LOW_FREQUENCY_TERMS = ["rare", "rarely", "occasional", "occasionally", "sometimes"]
    
    # Keywords for "Other" category parsing
    ALCOHOL_KEYWORDS = ["alcohol", "beer", "wine", "liquor", "drinking", "drinks"]
    ENERGY_DRINK_KEYWORDS = ["energy drink", "red bull", "monster", "rockstar"]
    FAST_FOOD_KEYWORDS = ["fast food", "fastfood", "junk food", "takeout", "take-out"]
    UPF_KEYWORDS = ["ultra-processed", "ultra processed", "processed food", "upf"]
    LATE_NIGHT_KEYWORDS = ["late-night", "late night", "midnight snack", "before bed"]
    
    # Keywords for special conditions
    DIZZINESS_KEYWORDS = ["dizzy", "dizziness", "lightheaded", "standing up"]
    LOW_BP_KEYWORDS = ["low blood pressure", "low bp", "hypotension"]
    POST_MEAL_CRASH_KEYWORDS = ["crash", "sleepy after eating", "tired after meal", "energy dip"]
    
    def __init__(self):
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip punctuation, deduplicate."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Replace semicolons and commas with spaces for splitting
        text = text.replace(";", " ").replace(",", " ")
        
        return text.strip()
    
    def _detect_frequency_multiplier(self, text: str) -> float:
        """
        Detect frequency terms and return intensity multiplier.
        
        Returns:
            1.5 for high frequency
            1.25 for moderate frequency
            1.0 for low/no frequency terms
        """
        text_lower = text.lower()
        
        # Check high frequency
        for term in self.HIGH_FREQUENCY_TERMS:
            if term in text_lower:
                return 1.5
        
        # Check moderate frequency
        for term in self.MODERATE_FREQUENCY_TERMS:
            if term in text_lower:
                return 1.25
        
        # Low frequency or no frequency terms
        return 1.0

    def _parse_other_text(self, text: str) -> Dict[str, float]:
        """
        Parse "Other" free text and map to known categories.

        Returns:
            Dict of focus area weights from "Other" text
        """
        weights = {}
        text_lower = text.lower()

        # Check for alcohol
        if any(kw in text_lower for kw in self.ALCOHOL_KEYWORDS):
            for domain, weight in self.OTHER_LEXICON["alcohol"].items():
                weights[domain] = weights.get(domain, 0) + weight

        # Check for energy drinks
        if any(kw in text_lower for kw in self.ENERGY_DRINK_KEYWORDS):
            for domain, weight in self.OTHER_LEXICON["energy_drink"].items():
                weights[domain] = weights.get(domain, 0) + weight

        # Check for fast food
        if any(kw in text_lower for kw in self.FAST_FOOD_KEYWORDS):
            for domain, weight in self.OTHER_LEXICON["fast_food"].items():
                weights[domain] = weights.get(domain, 0) + weight

        # Check for ultra-processed foods
        if any(kw in text_lower for kw in self.UPF_KEYWORDS):
            for domain, weight in self.OTHER_LEXICON["ultra_processed"].items():
                weights[domain] = weights.get(domain, 0) + weight

        # Check for late-night snacking
        if any(kw in text_lower for kw in self.LATE_NIGHT_KEYWORDS):
            for domain, weight in self.OTHER_LEXICON["late_night"].items():
                weights[domain] = weights.get(domain, 0) + weight

        return weights

    def get_food_cravings_weights(
        self,
        cravings_data: Any,
        sleep_hours: float = None,
        sleep_irregular: bool = False,
        sex: str = None,
        menstrual_pattern: str = None,
        other_symptoms: str = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on food cravings.

        Args:
            cravings_data: Multi-select input (string with comma/semicolon separated values)
            sleep_hours: Hours of sleep per night (for sweets amplifier)
            sleep_irregular: Whether sleep schedule is irregular (for sweets amplifier)
            sex: Patient sex (for chocolate/HRM rule)
            menstrual_pattern: Menstrual pattern text (for chocolate/HRM rule)
            other_symptoms: Other symptoms text (for salty/HRM rule, post-meal crash)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Handle None or empty input
        if not cravings_data or cravings_data in ["", "None", "NO", "NA", "none", "no", "na"]:
            return (weights, flags)

        # Normalize text
        text = self._normalize_text(str(cravings_data))

        # Check if "None" is selected with other items → drop None
        has_none = any(term in text for term in ["none", "no", "na"])
        has_other_items = any(term in text for term in ["sweets", "salty", "bread", "pasta", "chocolate", "caffeine", "other"])

        if has_none and has_other_items:
            # Drop "None" - user selected both None and actual cravings
            text = text.replace("none", "").replace("no", "").replace("na", "")
        elif has_none and not has_other_items:
            # Only "None" selected → no scoring
            return (weights, flags)

        # Detect frequency multiplier from entire text
        frequency_multiplier = self._detect_frequency_multiplier(text)

        # A) Sweets
        if "sweets" in text or "sweet" in text:
            for domain, weight in self.CRAVING_WEIGHTS["sweets"].items():
                weights[domain] = weights.get(domain, 0) + (weight * frequency_multiplier)

            # Amplifier: If sleep <6h or irregular → add STR +0.10
            if (sleep_hours is not None and sleep_hours < 6) or sleep_irregular:
                weights["STR"] = weights.get("STR", 0) + 0.10

        # B) Bread/Pasta
        if "bread" in text or "pasta" in text:
            for domain, weight in self.CRAVING_WEIGHTS["bread_pasta"].items():
                weights[domain] = weights.get(domain, 0) + (weight * frequency_multiplier)

            # If post-meal crash mentioned → add CM +0.10
            if other_symptoms:
                other_lower = other_symptoms.lower()
                if any(kw in other_lower for kw in self.POST_MEAL_CRASH_KEYWORDS):
                    weights["CM"] = weights.get("CM", 0) + 0.10

        # C) Chocolate
        if "chocolate" in text:
            for domain, weight in self.CRAVING_WEIGHTS["chocolate"].items():
                weights[domain] = weights.get(domain, 0) + (weight * frequency_multiplier)

            # Women with cyclical/PMS pattern → HRM +0.20
            if sex and sex.lower() in ["female", "f", "woman"]:
                if menstrual_pattern:
                    pattern_lower = menstrual_pattern.lower()
                    if any(term in pattern_lower for term in ["pms", "pre-menstrual", "premenstrual", "luteal", "before period"]):
                        weights["HRM"] = weights.get("HRM", 0) + 0.20

        # D) Caffeine
        if "caffeine" in text:
            for domain, weight in self.CRAVING_WEIGHTS["caffeine"].items():
                weights[domain] = weights.get(domain, 0) + (weight * frequency_multiplier)

            # If >3 cups/day or "to function" after poor sleep → STR +0.10
            if ">3 cups" in text or "3+ cups" in text or "to function" in text or "to get going" in text:
                weights["STR"] = weights.get("STR", 0) + 0.10

        # E) Salty
        if "salty" in text or "salt" in text:
            # Neutral by default
            # Exception: If dizziness on standing / low BP / fatigue → HRM +0.30
            if other_symptoms:
                other_lower = other_symptoms.lower()
                has_dizziness = any(kw in other_lower for kw in self.DIZZINESS_KEYWORDS)
                has_low_bp = any(kw in other_lower for kw in self.LOW_BP_KEYWORDS)
                has_fatigue = "fatigue" in other_lower or "tired" in other_lower

                if has_dizziness or has_low_bp or (has_fatigue and has_dizziness):
                    weights["HRM"] = weights.get("HRM", 0) + 0.30

        # F) Other (text parsed)
        if "other" in text:
            # Extract text after "other"
            other_match = re.search(r'other[:\s]+(.+)', text)
            if other_match:
                other_text = other_match.group(1)
                other_weights = self._parse_other_text(other_text)

                # Apply frequency multiplier
                for domain, weight in other_weights.items():
                    weights[domain] = weights.get(domain, 0) + (weight * frequency_multiplier)

        # Apply domain caps
        for domain in weights:
            if domain in self.DOMAIN_CAPS:
                weights[domain] = min(weights[domain], self.DOMAIN_CAPS[domain])

        return (weights, flags)

