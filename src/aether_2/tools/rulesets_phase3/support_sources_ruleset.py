"""
Ruleset for Field 23: Support Sources

Evaluates who or what the patient leans on for support and applies stress-axis
and cognitive health weights based on social support diversity and quality.

Decision tree:
1. Tier by count of distinct supports (k):
   - None (k=0): STR +0.35, COG +0.25, IMM +0.10, GA +0.20
   - Limited (k=1): STR +0.15, COG +0.10, GA +0.10
   - Moderate (k=2): No change
   - Diversified (k≥3): STR -0.10, COG -0.05, GA -0.05

2. Per-category quality modifiers:
   - Therapist: STR -0.10, COG -0.10 (+ extra COG -0.05 if CBT/ACT/therapy weekly)
   - Spiritual: STR -0.10, COG -0.05, CM -0.05
   - Pets: STR -0.05, COG -0.02
   - Negative support (toxic/abusive): STR +0.15, COG +0.10, IMM +0.05

3. Cross-field synergies:
   - (k≤1) + high stress (≥8/10): STR +0.10, COG +0.05, GA +0.05
   - (k≤1) + irregular sleep: STR +0.05, COG +0.05
   - Therapist + GI symptoms: GA -0.05

Per-field caps: STR ∈ [-0.15, +0.50], COG ∈ [-0.10, +0.30], GA ∈ [-0.10, +0.25], IMM ≤ +0.10
"""

from typing import Any, Dict, List, Tuple, Set


class SupportSourcesRuleset:
    """Ruleset for evaluating support sources."""

    # Valid support categories
    VALID_CATEGORIES = {
        "partner", "family", "friends", "spiritual", "pets", 
        "therapist", "therapy", "other", "none"
    }

    # Mapping keywords for "Other" text
    SPIRITUAL_KEYWORDS = [
        "church", "temple", "mosque", "sangha", "aa", "na", 
        "support group", "religious", "faith"
    ]
    
    THERAPIST_KEYWORDS = [
        "coach", "counselor", "psychologist", "psychiatrist", 
        "cbt", "therapy", "therapist"
    ]
    
    FRIENDS_KEYWORDS = [
        "online community", "discord", "reddit", "forum", "peer support"
    ]
    
    NEGATIVE_KEYWORDS = [
        "toxic", "abusive", "unsupportive", "conflict", "unhealthy"
    ]
    
    CBT_KEYWORDS = ["cbt", "act", "therapy weekly", "weekly therapy"]

    # Per-field caps
    STR_MIN = -0.15
    STR_MAX = 0.50
    COG_MIN = -0.10
    COG_MAX = 0.30
    GA_MIN = -0.10
    GA_MAX = 0.25
    IMM_MAX = 0.10

    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip whitespace."""
        if not text:
            return ""
        return text.lower().strip()

    def _parse_selections(self, support_data: str) -> Set[str]:
        """
        Parse support selections from comma/semicolon-separated string.
        
        Returns set of normalized category names.
        """
        if not support_data:
            return set()
        
        normalized = self._normalize_text(support_data)
        
        # Split by comma or semicolon
        parts = [p.strip() for p in normalized.replace(';', ',').split(',')]
        
        selections = set()
        for part in parts:
            if not part:
                continue
            # Match to valid categories using substring matching
            if "none" in part:
                selections.add("none")
            elif "partner" in part:
                selections.add("partner")
            elif "family" in part or "families" in part:
                selections.add("family")
            elif "friend" in part:
                selections.add("friends")
            elif "spiritual" in part or "religious" in part:
                selections.add("spiritual")
            elif "pet" in part:
                selections.add("pets")
            elif "therapist" in part or "therapy" in part:
                selections.add("therapist")
            elif "other" in part:
                selections.add("other")
        
        return selections

    def _map_other_text(self, selections: Set[str], other_text: str) -> Set[str]:
        """
        Map 'Other' text to existing categories based on keywords.
        
        Returns updated selections set.
        """
        if not other_text:
            return selections
        
        normalized = self._normalize_text(other_text)
        
        # Map to Spiritual
        for keyword in self.SPIRITUAL_KEYWORDS:
            if keyword in normalized:
                selections.add("spiritual")
                break
        
        # Map to Therapist
        for keyword in self.THERAPIST_KEYWORDS:
            if keyword in normalized:
                selections.add("therapist")
                break
        
        # Map to Friends
        for keyword in self.FRIENDS_KEYWORDS:
            if keyword in normalized:
                selections.add("friends")
                break
        
        return selections

    def _detect_negative_support(self, text: str) -> bool:
        """Detect negative support keywords (toxic/abusive/unsupportive)."""
        if not text:
            return False
        
        normalized = self._normalize_text(text)
        
        for keyword in self.NEGATIVE_KEYWORDS:
            if keyword in normalized:
                return True
        
        return False

    def _detect_cbt_therapy(self, text: str) -> bool:
        """Detect CBT/ACT/therapy weekly keywords."""
        if not text:
            return False

        normalized = self._normalize_text(text)

        for keyword in self.CBT_KEYWORDS:
            if keyword in normalized:
                return True

        return False

    def get_support_sources_weights(
        self,
        support_data: Any,
        age: int = None,
        stress_score: int = None,
        sleep_irregular: bool = False,
        gi_symptoms_present: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on support sources.

        Args:
            support_data: Support sources data (string with comma/semicolon separated values)
            age: Patient age (required, must be ≥18)
            stress_score: Current stress level (1-10 scale, from Field 20)
            sleep_irregular: Whether sleep is irregular (from Fields 14/15)
            gi_symptoms_present: Whether GI symptoms are present (from Phase 2)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Age validation (adults only)
        if age is None:
            flags.append("⚠️  Age unknown - cannot score support sources (adults only)")
            flags.append("needs_followup=true")
            return weights, flags

        if age < 18:
            flags.append(f"⚠️  Age {age} < 18 - support sources scoring skipped (adults only)")
            return weights, flags

        # Convert to string
        if support_data is None:
            support_data = ""
        text = str(support_data).strip()

        # Parse selections
        selections = self._parse_selections(text)

        # If empty, flag for follow-up
        if not selections:
            flags.append("⚠️  Empty support sources response")
            flags.append("needs_followup=true")
            return weights, flags

        # Extract "Other" text if present (everything after "Other")
        other_text = ""
        if "other" in text.lower():
            # Extract text after "Other"
            parts = text.lower().split("other")
            if len(parts) > 1:
                other_text = parts[1].strip()

        # Map "Other" text to categories
        selections = self._map_other_text(selections, other_text)

        # If "None" is selected with anything else, keep only "None"
        if "none" in selections and len(selections) > 1:
            selections = {"none"}
            flags.append("conflict_resolved=kept_none")

        # Detect negative support
        negative_support = self._detect_negative_support(text)

        # Count distinct supports (excluding "None" and "Other")
        k = len(selections - {"none", "other"})

        # If negative support detected, don't count those categories
        if negative_support:
            k = max(0, k - 1)  # Reduce count by 1 for negative support

        # ===================================================================
        # A. Tier by count of distinct supports
        # ===================================================================

        if "none" in selections or k == 0:
            # No support
            weights["STR"] = weights.get("STR", 0) + 0.35
            weights["COG"] = weights.get("COG", 0) + 0.25
            weights["IMM"] = weights.get("IMM", 0) + 0.10
            weights["GA"] = weights.get("GA", 0) + 0.20
        elif k == 1:
            # Limited support
            weights["STR"] = weights.get("STR", 0) + 0.15
            weights["COG"] = weights.get("COG", 0) + 0.10
            weights["GA"] = weights.get("GA", 0) + 0.10
        elif k >= 3:
            # Diversified support
            weights["STR"] = weights.get("STR", 0) - 0.10
            weights["COG"] = weights.get("COG", 0) - 0.05
            weights["GA"] = weights.get("GA", 0) - 0.05
        # k == 2: no change

        # ===================================================================
        # B. Per-category quality modifiers
        # ===================================================================

        # Therapist
        if "therapist" in selections:
            weights["STR"] = weights.get("STR", 0) - 0.10
            weights["COG"] = weights.get("COG", 0) - 0.10

            # Extra COG reduction if CBT/ACT/therapy weekly
            if self._detect_cbt_therapy(text):
                weights["COG"] = weights.get("COG", 0) - 0.05

        # Spiritual
        if "spiritual" in selections:
            weights["STR"] = weights.get("STR", 0) - 0.10
            weights["COG"] = weights.get("COG", 0) - 0.05
            weights["CM"] = weights.get("CM", 0) - 0.05

        # Pets
        if "pets" in selections:
            weights["STR"] = weights.get("STR", 0) - 0.05
            weights["COG"] = weights.get("COG", 0) - 0.02

        # Negative support
        if negative_support:
            weights["STR"] = weights.get("STR", 0) + 0.15
            weights["COG"] = weights.get("COG", 0) + 0.10
            weights["IMM"] = weights.get("IMM", 0) + 0.05
            flags.append("⚠️  Negative support detected (toxic/abusive/unsupportive)")

        # ===================================================================
        # C. Cross-field synergies
        # ===================================================================

        # (k≤1) + high stress (≥8/10)
        if k <= 1 and stress_score is not None and stress_score >= 8:
            weights["STR"] = weights.get("STR", 0) + 0.10
            weights["COG"] = weights.get("COG", 0) + 0.05
            weights["GA"] = weights.get("GA", 0) + 0.05

        # (k≤1) + irregular sleep
        if k <= 1 and sleep_irregular:
            weights["STR"] = weights.get("STR", 0) + 0.05
            weights["COG"] = weights.get("COG", 0) + 0.05

        # Therapist + GI symptoms
        if "therapist" in selections and gi_symptoms_present:
            weights["GA"] = weights.get("GA", 0) - 0.05

        # ===================================================================
        # D. Apply per-field caps
        # ===================================================================

        if "STR" in weights:
            weights["STR"] = max(self.STR_MIN, min(self.STR_MAX, weights["STR"]))

        if "COG" in weights:
            weights["COG"] = max(self.COG_MIN, min(self.COG_MAX, weights["COG"]))

        if "GA" in weights:
            weights["GA"] = max(self.GA_MIN, min(self.GA_MAX, weights["GA"]))

        if "IMM" in weights:
            weights["IMM"] = min(self.IMM_MAX, weights["IMM"])

        return weights, flags

