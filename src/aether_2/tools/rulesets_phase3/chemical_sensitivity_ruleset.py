"""
Chemical Sensitivity Ruleset (Field 31)

Evaluates unusual sensitivity to small amounts of chemicals, perfumes, smoke, or exhaust.
Radio: Yes/No with optional free text for triggers and reactions.
"""

import re
from typing import Dict, List, Tuple


class ChemicalSensitivityRuleset:
    """
    Ruleset for evaluating chemical sensitivity (IEI/MCS signal).
    
    Decision tree:
    - No → no change
    - Yes → baseline + category add-ons + reaction modifiers + dose/frequency modifiers
    
    Per-field cap: All domains ≤ +2.0
    """
    
    # Per-field cap
    MAX_WEIGHT = 2.0
    
    # Baseline weights for "Yes" (IEI/MCS signal)
    BASELINE_WEIGHTS = {
        "DTX": 0.40,
        "IMM": 0.30,
        "STR": 0.20,
        "COG": 0.15,
        "GA": 0.20,
        "SKN": 0.10,
        "MITO": 0.10
    }
    
    # Category add-ons
    CATEGORY_WEIGHTS = {
        "fragrances": {"DTX": 0.20, "SKN": 0.10, "IMM": 0.10, "COG": 0.10, "GA": 0.10},
        "paint_solvents": {"DTX": 0.20, "IMM": 0.10, "COG": 0.10, "GA": 0.10, "SKN": 0.10},
        "combustion": {"IMM": 0.20, "DTX": 0.15, "CM": 0.10, "COG": 0.10, "GA": 0.05},
        "cleaning_agents": {"DTX": 0.15, "IMM": 0.10, "SKN": 0.10, "GA": 0.05, "COG": 0.05},
        "pesticides": {"DTX": 0.20, "IMM": 0.15, "MITO": 0.10, "COG": 0.10, "GA": 0.10},
        "damp_mold": {"IMM": 0.25, "GA": 0.20, "DTX": 0.15, "SKN": 0.10, "COG": 0.10}
    }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _detect_fragrances(self, text: str) -> bool:
        """Detect fragrances/VOCs triggers."""
        keywords = [
            "perfume", "cologne", "air freshener", "scented candle", "scented wax",
            "new car smell", "cleaning aisle", "fragrance", "scent"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_paint_solvents(self, text: str) -> bool:
        """Detect paint/solvents/formaldehyde triggers."""
        keywords = [
            "paint", "solvent", "new carpet", "flooring glue", "adhesive",
            "formaldehyde", "voc", "volatile organic"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_combustion(self, text: str) -> bool:
        """Detect combustion triggers."""
        keywords = [
            "smoke", "cigarette", "cigar", "incense", "wildfire",
            "exhaust", "diesel", "gas stove", "combustion"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_cleaning_agents(self, text: str) -> bool:
        """Detect bleach/ammonia/cleaning agents."""
        keywords = [
            "bleach", "chlorine", "ammonia", "cleaning agent", "cleaner",
            "disinfectant", "sanitizer"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_pesticides(self, text: str) -> bool:
        """Detect pesticides/herbicides."""
        keywords = [
            "pesticide", "herbicide", "insecticide", "fungicide",
            "weed killer", "bug spray", "lawn chemical"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_damp_mold(self, text: str) -> bool:
        """Detect damp/moldy places."""
        keywords = [
            "musty", "water damage", "moldy", "mold", "mildew",
            "damp", "moisture", "wet basement"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_reactions(self, text: str) -> Dict[str, bool]:
        """Detect reaction types."""
        reactions = {
            "headache": False,
            "nausea": False,
            "rash": False,
            "respiratory": False,
            "cognitive": False
        }
        
        if any(kw in text for kw in ["headache", "migraine"]):
            reactions["headache"] = True
        if any(kw in text for kw in ["nausea", "vomit", "sick"]):
            reactions["nausea"] = True
        if any(kw in text for kw in ["rash", "hive", "flush", "itch"]):
            reactions["rash"] = True
        if any(kw in text for kw in ["cough", "wheeze", "dyspnea", "breath", "asthma"]):
            reactions["respiratory"] = True
        if any(kw in text for kw in ["brain fog", "dizz", "confusion", "disoriented"]):
            reactions["cognitive"] = True
        
        return reactions
    
    def _detect_frequency(self, text: str) -> str:
        """Detect frequency/dose cues."""
        if any(kw in text for kw in ["daily", "every day", "constant"]):
            return "daily"
        elif any(kw in text for kw in ["most days", "frequent", "often"]):
            return "frequent"
        elif any(kw in text for kw in ["brief", "whiff", "minutes", "short"]):
            return "brief"
        return "unknown"

    def get_chemical_sensitivity_weights(
        self,
        choice: str,
        triggers_text: str = ""
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for chemical sensitivity.

        Args:
            choice: Radio selection (Yes | No)
            triggers_text: Optional free text listing triggers and reactions

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Validate choice
        choice_norm = choice.strip() if choice else ""
        if choice_norm not in ["Yes", "No"]:
            return {}, []

        # A) Base branch by radio
        if choice_norm == "No":
            return {}, []

        # Yes → apply baseline
        for domain, weight in self.BASELINE_WEIGHTS.items():
            weights[domain] = weights.get(domain, 0) + weight
        flags.append("Chemical sensitivity (IEI/MCS signal): Baseline weights applied")

        # Normalize triggers text
        text_norm = self._normalize_text(triggers_text)

        if not text_norm:
            # If Yes but no triggers text, return baseline only
            return weights, flags

        # B) Exposure category add-ons
        if self._detect_fragrances(text_norm):
            for domain, weight in self.CATEGORY_WEIGHTS["fragrances"].items():
                weights[domain] = weights.get(domain, 0) + weight
            flags.append("Fragrances/VOCs: Perfume, air fresheners, scented products → DTX +0.20, SKN +0.10, IMM +0.10, COG +0.10, GA +0.10")

        if self._detect_paint_solvents(text_norm):
            for domain, weight in self.CATEGORY_WEIGHTS["paint_solvents"].items():
                weights[domain] = weights.get(domain, 0) + weight
            flags.append("Paint/Solvents: Paint, formaldehyde, new carpet → DTX +0.20, IMM +0.10, COG +0.10, GA +0.10, SKN +0.10")

        if self._detect_combustion(text_norm):
            for domain, weight in self.CATEGORY_WEIGHTS["combustion"].items():
                weights[domain] = weights.get(domain, 0) + weight
            flags.append("Combustion: Smoke, exhaust, gas stove → IMM +0.20, DTX +0.15, CM +0.10, COG +0.10, GA +0.05")

        if self._detect_cleaning_agents(text_norm):
            for domain, weight in self.CATEGORY_WEIGHTS["cleaning_agents"].items():
                weights[domain] = weights.get(domain, 0) + weight
            flags.append("Cleaning agents: Bleach, ammonia → DTX +0.15, IMM +0.10, SKN +0.10, GA +0.05, COG +0.05")

        if self._detect_pesticides(text_norm):
            for domain, weight in self.CATEGORY_WEIGHTS["pesticides"].items():
                weights[domain] = weights.get(domain, 0) + weight
            flags.append("Pesticides/Herbicides: Lawn chemicals → DTX +0.20, IMM +0.15, MITO +0.10, COG +0.10, GA +0.10")

        if self._detect_damp_mold(text_norm):
            for domain, weight in self.CATEGORY_WEIGHTS["damp_mold"].items():
                weights[domain] = weights.get(domain, 0) + weight
            flags.append("Damp/Mold: Musty, water-damaged places → IMM +0.25, GA +0.20, DTX +0.15, SKN +0.10, COG +0.10")

        # C) Reaction modifiers
        reactions = self._detect_reactions(text_norm)
        if reactions["headache"]:
            weights["COG"] = weights.get("COG", 0) + 0.10
            flags.append("Reaction: Headache/migraine → COG +0.10")
        if reactions["nausea"]:
            weights["GA"] = weights.get("GA", 0) + 0.10
            flags.append("Reaction: Nausea → GA +0.10")
        if reactions["rash"]:
            weights["SKN"] = weights.get("SKN", 0) + 0.10
            weights["IMM"] = weights.get("IMM", 0) + 0.05
            flags.append("Reaction: Rash/hives → SKN +0.10, IMM +0.05")
        if reactions["respiratory"]:
            weights["IMM"] = weights.get("IMM", 0) + 0.15
            flags.append("Reaction: Respiratory symptoms → IMM +0.15")
        if reactions["cognitive"]:
            weights["COG"] = weights.get("COG", 0) + 0.10
            flags.append("Reaction: Brain fog/dizziness → COG +0.10")

        # D) Frequency/dose modifiers
        frequency = self._detect_frequency(text_norm)
        if frequency == "daily":
            # Daily exposure → increase all weights by 10%
            for domain in weights:
                weights[domain] *= 1.10
            flags.append("Frequency: Daily exposure → All weights +10%")
        elif frequency == "brief":
            # Brief exposure still triggers symptoms → increase sensitivity signal
            weights["STR"] = weights.get("STR", 0) + 0.10
            flags.append("Dose sensitivity: Brief exposure triggers symptoms → STR +0.10")

        # Apply per-field cap
        for domain in weights:
            if weights[domain] > self.MAX_WEIGHT:
                weights[domain] = self.MAX_WEIGHT

        # Remove zero/negative weights
        weights = {k: v for k, v in weights.items() if v > 0}

        return weights, flags

