"""
Ruleset for Field 35: Seasonal Allergies (radio + optional free text).

Prompt: "Do you get seasonal allergies?"
Record as: Yes / No
If Yes (free text): "Please list the allergen and symptoms (e.g., pollen → sinus block)."

This ruleset evaluates seasonal allergic rhinitis and its impact on immune function,
barrier health, gut-mucosal cross-talk, and cognitive/sleep quality.

Key features:
- Baseline weights for allergic inflammation
- Severity & phenotype modifiers (wheeze, eczema, sleep disruption, oral-allergy syndrome)
- Allergen-specific cross-reactivity (PFAS) logic for pollen-food allergies
- Histamine-sensitive pattern detection
- Risk reducers (nasal saline, HEPA filtration)
- Per-field caps: IMM ≤ +0.80, SKN ≤ +0.50, GA ≤ +0.40, STR ≤ +0.30, COG ≤ +0.30
"""

from typing import Dict, List, Tuple


class SeasonalAllergiesRuleset:
    """Ruleset for evaluating seasonal allergies and pollen-food cross-reactivity."""
    
    # Per-field caps
    MAX_IMM = 0.80
    MAX_SKN = 0.50
    MAX_GA = 0.40
    MAX_STR = 0.30
    MAX_COG = 0.30
    
    # Baseline weights (fire once if Yes)
    BASELINE_WEIGHTS = {
        "IMM": 0.50,  # Core allergic inflammation
        "SKN": 0.20,  # Barrier/mucosal involvement
        "GA": 0.20,   # Mucosal immune network; histamine-triggered food responses
        "STR": 0.10,  # Stress/sleep fragmentation
        "COG": 0.10,  # Brain-fog, attention hits from AR
    }
    
    # Allergen groups for PFAS (pollen-food allergy syndrome) detection
    ALLERGEN_GROUPS = {
        "birch_tree": ["birch", "tree pollen", "alder", "hazel"],
        "grass": ["grass", "timothy", "rye grass", "bermuda"],
        "ragweed": ["ragweed", "ambrosia"],
        "mugwort": ["mugwort", "artemisia", "wormwood"],
        "cedar_juniper": ["cedar", "juniper", "mountain cedar"],
        "mold": ["mold", "mould", "fungus", "spore"],
    }
    
    # PFAS cross-reactive foods by allergen group
    PFAS_FOODS = {
        "birch_tree": ["apple", "pear", "peach", "stone fruit", "carrot", "celery", "hazelnut", "almond", "cherry"],
        "grass": ["melon", "tomato", "orange", "potato"],
        "ragweed": ["banana", "melon", "zucchini", "cucumber", "cantaloupe"],
        "mugwort": ["celery", "carrot", "parsley", "dill", "coriander", "sunflower seed", "spice"],
    }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        if not text:
            return ""
        text = text.lower().strip()
        # Collapse multiple spaces/newlines
        import re
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _detect_allergens(self, text: str) -> List[str]:
        """
        Detect allergen groups from free text.
        Returns list of detected allergen group keys.
        """
        detected = []
        for group_key, keywords in self.ALLERGEN_GROUPS.items():
            if any(kw in text for kw in keywords):
                detected.append(group_key)
        return detected
    
    def _detect_severe_symptoms(self, text: str) -> bool:
        """Detect severe symptom keywords."""
        import re
        keywords = [
            "wheeze", "wheezing", "asthma attack",
            "emergency room", "urgent care",
            "systemic hive", "hives all over", "full body hive",
            "anaphylaxis", "anaphylactic", "epipen", "epi-pen"
        ]
        # Check for "ER" with word boundaries
        if re.search(r'\ber\b', text):
            return True
        return any(kw in text for kw in keywords)
    
    def _detect_eczema_flare(self, text: str) -> bool:
        """Detect eczema/atopic dermatitis flares with season."""
        keywords = [
            "eczema", "atopic dermatitis", "skin flare", "rash worse",
            "itchy skin", "dry skin worse"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_sleep_disruption(self, text: str) -> bool:
        """Detect sleep disruption ≥3 nights/week in season."""
        keywords = [
            "can't sleep", "cannot sleep", "sleep disruption", "wake up",
            "insomnia", "poor sleep", "restless night", "toss and turn",
            "congestion at night", "stuffy nose at night"
        ]
        # Check for frequency indicators
        frequency_keywords = [
            "every night", "nightly", "most nights", "several nights",
            "3 nights", "4 nights", "5 nights", "many nights"
        ]
        has_sleep_issue = any(kw in text for kw in keywords)
        has_frequency = any(kw in text for kw in frequency_keywords)
        return has_sleep_issue and has_frequency
    
    def _detect_oral_allergy_syndrome(self, text: str) -> bool:
        """Detect oral-itch after raw fruits/veg (PFAS)."""
        keywords = [
            "oral itch", "mouth itch", "tongue itch", "lip itch",
            "throat itch", "tingling mouth", "tingling lips",
            "raw fruit", "raw vegetable", "raw apple", "raw carrot"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_food_triggers(self, text: str) -> bool:
        """Detect food triggers mentioned in free text."""
        keywords = [
            "food trigger", "food reaction", "food allergy",
            "after eating", "when i eat", "certain foods"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_histamine_pattern(self, text: str) -> bool:
        """Detect histamine-sensitive pattern (wine/beer/fermented/aged foods)."""
        keywords = [
            "wine", "beer", "alcohol", "fermented", "aged cheese",
            "aged food", "sauerkraut", "kimchi", "kombucha",
            "histamine", "aged meat", "cured meat"
        ]
        return any(kw in text for kw in keywords)

    def _detect_nasal_saline(self, text: str) -> bool:
        """Detect regular nasal saline irrigation."""
        keywords = [
            "nasal saline", "saline rinse", "neti pot", "nasal irrigation",
            "sinus rinse", "nasal wash", "saline spray"
        ]
        return any(kw in text for kw in keywords)

    def _detect_hepa_filtration(self, text: str) -> bool:
        """Detect home HEPA filtration used nightly."""
        keywords = [
            "hepa", "air purifier", "air filter", "air cleaner",
            "filtration", "purifier"
        ]
        return any(kw in text for kw in keywords)

    def _detect_pfas_aware_behaviors(self, text: str) -> bool:
        """Detect PFAS-aware behaviors (cooks/peels reactive produce)."""
        keywords = [
            "cook", "cooked", "peel", "peeled", "peeling",
            "heat", "heated", "boil", "boiled"
        ]
        # Must mention both cooking/peeling AND tolerance
        has_cooking = any(kw in text for kw in keywords)
        has_tolerance = any(kw in text for kw in ["tolerate", "tolerates", "ok if", "fine if", "no problem if"])
        return has_cooking and has_tolerance

    def get_seasonal_allergies_weights(
        self,
        choice: str,
        allergen_symptoms_text: str = ""
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for seasonal allergies.

        Args:
            choice: Radio selection (Yes | No)
            allergen_symptoms_text: Optional free text listing allergens and symptoms

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []

        # Normalize inputs
        choice_norm = self._normalize_text(choice)
        text_norm = self._normalize_text(allergen_symptoms_text)

        # 0) Guard rails
        if not choice_norm or choice_norm == "no":
            return {}, []

        if choice_norm != "yes":
            # Invalid choice
            return {}, []

        # 1) Baseline weights (fire once if Yes)
        for domain, weight in self.BASELINE_WEIGHTS.items():
            weights[domain] = weights.get(domain, 0) + weight

        flags.append("Seasonal allergies detected: Baseline weights applied")

        # If no free text, return baseline only
        if not text_norm:
            # Apply caps
            weights["IMM"] = min(weights.get("IMM", 0), self.MAX_IMM)
            weights["SKN"] = min(weights.get("SKN", 0), self.MAX_SKN)
            weights["GA"] = min(weights.get("GA", 0), self.MAX_GA)
            weights["STR"] = min(weights.get("STR", 0), self.MAX_STR)
            weights["COG"] = min(weights.get("COG", 0), self.MAX_COG)

            # Remove zero/negative weights
            weights = {k: v for k, v in weights.items() if v > 0}
            return weights, flags

        # 2) Severity & phenotype modifiers (apply all that match)
        if self._detect_severe_symptoms(text_norm):
            weights["IMM"] = weights.get("IMM", 0) + 0.20
            flags.append("Severe symptoms: Wheeze/ER/systemic hives/anaphylaxis → IMM +0.20")

        if self._detect_eczema_flare(text_norm):
            weights["SKN"] = weights.get("SKN", 0) + 0.20
            flags.append("Eczema/atopic dermatitis flares with season → SKN +0.20")

        if self._detect_sleep_disruption(text_norm):
            weights["STR"] = weights.get("STR", 0) + 0.20
            weights["COG"] = weights.get("COG", 0) + 0.10
            flags.append("Sleep disruption ≥3 nights/week in season → STR +0.20, COG +0.10")

        if self._detect_oral_allergy_syndrome(text_norm):
            weights["GA"] = weights.get("GA", 0) + 0.10
            weights["SKN"] = weights.get("SKN", 0) + 0.10
            flags.append("Oral-itch after raw fruits/veg (PFAS) → GA +0.10, SKN +0.10")

        # 3) Allergen-specific cross-reactivity (PFAS) logic
        detected_allergens = self._detect_allergens(text_norm)
        has_food_triggers = self._detect_food_triggers(text_norm) or self._detect_oral_allergy_syndrome(text_norm)

        pfas_tags = []
        for allergen_group in detected_allergens:
            if allergen_group in self.PFAS_FOODS:
                cross_foods = self.PFAS_FOODS[allergen_group]
                pfas_tags.append(f"PFAS-{allergen_group.replace('_', '-').title()}")

                # Add GA +0.10 only if food triggers or oral itching mentioned
                if has_food_triggers:
                    weights["GA"] = weights.get("GA", 0) + 0.10
                    flags.append(f"PFAS cross-reactivity: {allergen_group.replace('_', ' ').title()} → {', '.join(cross_foods[:3])}... → GA +0.10")
                else:
                    flags.append(f"PFAS cross-reactivity detected: {allergen_group.replace('_', ' ').title()} → {', '.join(cross_foods[:3])}... (no food triggers mentioned)")

        # 4) Histamine-related pattern
        if self._detect_histamine_pattern(text_norm):
            weights["GA"] = weights.get("GA", 0) + 0.10
            flags.append("Histamine-sensitive pattern: Wine/beer/fermented/aged foods → GA +0.10")

        # 5) Risk reducers (subtractors; applied last)
        if self._detect_nasal_saline(text_norm):
            weights["IMM"] = weights.get("IMM", 0) - 0.05
            weights["STR"] = weights.get("STR", 0) - 0.05
            flags.append("Risk reducer: Regular nasal saline irrigation → IMM -0.05, STR -0.05")

        if self._detect_hepa_filtration(text_norm):
            weights["IMM"] = weights.get("IMM", 0) - 0.05
            flags.append("Risk reducer: Home HEPA filtration → IMM -0.05")

        # Apply per-field caps
        weights["IMM"] = min(weights.get("IMM", 0), self.MAX_IMM)
        weights["SKN"] = min(weights.get("SKN", 0), self.MAX_SKN)
        weights["GA"] = min(weights.get("GA", 0), self.MAX_GA)
        weights["STR"] = min(weights.get("STR", 0), self.MAX_STR)
        weights["COG"] = min(weights.get("COG", 0), self.MAX_COG)

        # Remove zero/negative weights
        weights = {k: v for k, v in weights.items() if v > 0}

        return weights, flags

