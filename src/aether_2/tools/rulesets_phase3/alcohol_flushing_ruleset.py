"""
Ruleset for Field 32: Alcohol Flushing

Field name: Alcohol Flushing
Assistant prompt: "Does a small amount of alcohol make you flush or feel unwell?"
Accepted values: Yes | No | I rarely drink
Follow-up: Free text (optional) - "Explain/Anything else you'd like to share?"

Scoring approach:
- Decision tree based on user's choice (Yes, No, I rarely drink)
- Context-driven add-ons based on reaction patterns and beverage types
- Cross-field synergies with ancestry, medical history
- Additive, monotonic scoring (transparent like clinical scores)

Evidence base:
- ALDH2 phenotype proxy (acetaldehyde detox load)
- Gastric irritation, permeability/gut-liver axis
- Alcohol can raise estrogen levels
- Facial flush = vasodilatory/skin-barrier signal
- Histamine/biogenic-amine reactions common with some drinks
- Higher acetaldehyde exposure and elevated ESCC/head-neck cancer risk
"""

from typing import Dict, List, Tuple, Any
import re


class AlcoholFlushingRuleset:
    """Ruleset for evaluating alcohol flushing (radio + optional free text with context-driven scoring)."""
    
    # Per-field cap (all domains)
    MAX_WEIGHT = 1.5
    
    def __init__(self):
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        if not text:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _detect_flush_redness(self, text: str) -> bool:
        """Detect flush/turn red in text."""
        return bool(re.search(r'\b(flush|flushing|turn red|red face|facial red|redness)\b', text))
    
    def _detect_palpitations(self, text: str) -> bool:
        """Detect palpitations/heart racing in text."""
        return bool(re.search(r'\b(palpitations?|heart rac(e|ing)|rapid heart|tachycardia)\b', text))
    
    def _detect_headache(self, text: str) -> bool:
        """Detect headache/migraine in text."""
        return bool(re.search(r'\b(headache|migraine|head pain)\b', text))
    
    def _detect_gi_symptoms(self, text: str) -> bool:
        """Detect nausea/vomiting/abdominal burning/diarrhea in text."""
        return bool(re.search(r'\b(nausea|vomit(ing)?|abdominal burn(ing)?|diarrhea|stomach burn(ing)?|burning stomach)\b', text))
    
    def _detect_allergic_symptoms(self, text: str) -> bool:
        """Detect congestion/sneezing/wheeze/itch/hives in text."""
        return bool(re.search(r'\b(congestion|sneez(e|ing)|wheez(e|ing)|itch(y|ing)?|hives|runny nose)\b', text))
    
    def _detect_red_wine(self, text: str) -> bool:
        """Detect red wine triggers in text."""
        return bool(re.search(r'\bred wine\b', text))
    
    def _detect_beer(self, text: str) -> bool:
        """Detect beer triggers in text."""
        return bool(re.search(r'\bbeer\b', text))
    
    def _detect_spirits(self, text: str) -> bool:
        """Detect spirits/high-proof shots in text."""
        return bool(re.search(r'\b(spirits?|vodka|whiskey|rum|gin|tequila|shots?|high.?proof)\b', text))
    
    def _detect_few_sips(self, text: str) -> bool:
        """Detect reaction after 'a few sips' in text."""
        return bool(re.search(r'\b(few sips?|small amount|tiny amount|one sip|half.?glass)\b', text))
    
    def _detect_immediate_reaction(self, text: str) -> bool:
        """Detect immediate (minutes) reaction in text."""
        return bool(re.search(r'\b(immediate(ly)?|within minutes?|right away|instantly|seconds?)\b', text))
    
    def _detect_intolerance_reason(self, text: str) -> bool:
        """Detect if 'rarely drink' is due to intolerance/flush."""
        return bool(re.search(r'\b(intoleran(ce|t)|flush|unwell|sick|nausea|headache|reaction|avoid|can\'?t handle)\b', text))
    
    def _detect_aldh2_mention(self, text: str) -> bool:
        """Detect ALDH2/rs671 mention in text."""
        return bool(re.search(r'\b(aldh2|rs671|asian flush|asian glow)\b', text))

    def get_alcohol_flushing_weights(
        self,
        alcohol_flushing: Any,
        followup_text: str = "",
        ancestry: str = "",
        diagnoses: List[str] = None,
        diagnoses_other: str = ""
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for alcohol flushing.

        Args:
            alcohol_flushing: User's alcohol flushing choice (Yes | No | I rarely drink)
            followup_text: Optional free text explanation
            ancestry: User's ancestry (for East Asian detection)
            diagnoses: List of diagnoses from medical history (for migraine, asthma detection)
            diagnoses_other: Other diagnoses from medical history (for GERD/Barrett's detection)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []

        # Validate input
        if not alcohol_flushing:
            return weights, flags

        # Normalize choice
        choice = self._normalize_text(str(alcohol_flushing))

        # Validate choice
        valid_choices = ["yes", "no", "i rarely drink", "rarely drink"]
        if choice not in valid_choices:
            flags.append(f"Invalid choice: '{alcohol_flushing}' (expected: Yes | No | I rarely drink)")
            return weights, flags

        # Normalize cross-field data
        followup_norm = self._normalize_text(followup_text)
        ancestry_norm = self._normalize_text(ancestry)
        diagnoses_other_norm = self._normalize_text(diagnoses_other)

        # Normalize diagnoses list
        if diagnoses is None:
            diagnoses = []
        diagnoses_norm = [self._normalize_text(str(d)) for d in diagnoses]

        # A1) Yes (flush/unwell with small amounts)
        if choice == "yes":
            # Baseline weights
            weights["DTX"] = weights.get("DTX", 0.0) + 0.35  # Acetaldehyde detox load
            weights["GA"] = weights.get("GA", 0.0) + 0.25   # Gastric irritation
            weights["HRM"] = weights.get("HRM", 0.0) + 0.10  # Hormonal-transport flag
            weights["SKN"] = weights.get("SKN", 0.0) + 0.10  # Facial flush
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10  # Histamine/biogenic-amine reactions

            flags.append("Alcohol flushing/intolerance detected (Yes)")

            # Reaction-pattern add-ons (from free text)
            if followup_norm:
                # Flush/turn red
                if self._detect_flush_redness(followup_norm):
                    weights["SKN"] = weights.get("SKN", 0.0) + 0.10
                    flags.append("Reaction pattern: Flush/turn red → SKN +0.10")

                # Palpitations/heart racing
                if self._detect_palpitations(followup_norm):
                    weights["CM"] = weights.get("CM", 0.0) + 0.10
                    weights["STR"] = weights.get("STR", 0.0) + 0.05
                    flags.append("Reaction pattern: Palpitations/heart racing → CM +0.10, STR +0.05")

                # Headache/migraine
                if self._detect_headache(followup_norm):
                    weights["COG"] = weights.get("COG", 0.0) + 0.10
                    flags.append("Reaction pattern: Headache/migraine → COG +0.10")

                # Nausea/vomiting/abdominal burning/diarrhea
                if self._detect_gi_symptoms(followup_norm):
                    weights["GA"] = weights.get("GA", 0.0) + 0.20
                    flags.append("Reaction pattern: GI symptoms (nausea/vomiting/burning/diarrhea) → GA +0.20")

                # Congestion/sneezing/wheeze/itch/hives
                if self._detect_allergic_symptoms(followup_norm):
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.10
                    weights["SKN"] = weights.get("SKN", 0.0) + 0.05
                    flags.append("Reaction pattern: Allergic symptoms (congestion/sneezing/wheeze/itch/hives) → IMM +0.10, SKN +0.05")

                # Beverage-specific add-ons
                # Red wine triggers
                if self._detect_red_wine(followup_norm):
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.10
                    weights["GA"] = weights.get("GA", 0.0) + 0.10
                    weights["COG"] = weights.get("COG", 0.0) + 0.05
                    flags.append("Beverage trigger: Red wine → IMM +0.10, GA +0.10, COG +0.05")

                # Beer triggers
                if self._detect_beer(followup_norm):
                    weights["GA"] = weights.get("GA", 0.0) + 0.10
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.05
                    flags.append("Beverage trigger: Beer → GA +0.10, IMM +0.05")

                # Spirits/high-proof shots
                if self._detect_spirits(followup_norm):
                    weights["DTX"] = weights.get("DTX", 0.0) + 0.10
                    weights["GA"] = weights.get("GA", 0.0) + 0.10
                    flags.append("Beverage trigger: Spirits/high-proof → DTX +0.10, GA +0.10")

                # Dose/latency severity nudges
                # Reaction after "a few sips"
                if self._detect_few_sips(followup_norm):
                    weights["DTX"] = weights.get("DTX", 0.0) + 0.10
                    flags.append("Severity: Reaction after few sips (strong phenotype) → DTX +0.10")

                # Immediate (minutes) reaction
                if self._detect_immediate_reaction(followup_norm):
                    weights["SKN"] = weights.get("SKN", 0.0) + 0.05
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.05
                    flags.append("Severity: Immediate reaction (pseudoallergic/amine pattern) → SKN +0.05, IMM +0.05")

            # Cancer-risk awareness tag (ALDH2-flushing)
            # Check for East Asian ancestry or ALDH2/rs671 mention
            is_east_asian = bool(re.search(r'\b(east asian|chinese|japanese|korean|taiwanese|asian)\b', ancestry_norm))
            has_aldh2_mention = self._detect_aldh2_mention(followup_norm)

            if is_east_asian or has_aldh2_mention:
                weights["DTX"] = weights.get("DTX", 0.0) + 0.10
                flags.append("⚠️ ALDH2-flushing phenotype detected (East Asian ancestry or ALDH2 mention)")
                flags.append("⚠️ CANCER RISK: Higher acetaldehyde exposure → elevated ESCC/head-neck cancer risk if drinking continues")

        # A2) I rarely drink
        elif choice in ["i rarely drink", "rarely drink"]:
            # Check if reason is intolerance/flush
            if followup_norm and self._detect_intolerance_reason(followup_norm):
                # Apply 80% of A1 baseline + applicable add-ons
                weights["DTX"] = weights.get("DTX", 0.0) + 0.28  # 0.35 * 0.8
                weights["GA"] = weights.get("GA", 0.0) + 0.20   # 0.25 * 0.8
                weights["HRM"] = weights.get("HRM", 0.0) + 0.08  # 0.10 * 0.8
                weights["SKN"] = weights.get("SKN", 0.0) + 0.08  # 0.10 * 0.8
                weights["IMM"] = weights.get("IMM", 0.0) + 0.08  # 0.10 * 0.8

                flags.append("Rarely drink due to intolerance/flush (80% baseline applied)")

                # Apply same add-ons as A1 (at 80% strength)
                # Reaction-pattern add-ons
                if self._detect_flush_redness(followup_norm):
                    weights["SKN"] = weights.get("SKN", 0.0) + 0.08  # 0.10 * 0.8
                    flags.append("Reaction pattern: Flush/turn red → SKN +0.08 (80%)")

                if self._detect_palpitations(followup_norm):
                    weights["CM"] = weights.get("CM", 0.0) + 0.08  # 0.10 * 0.8
                    weights["STR"] = weights.get("STR", 0.0) + 0.04  # 0.05 * 0.8
                    flags.append("Reaction pattern: Palpitations → CM +0.08, STR +0.04 (80%)")

                if self._detect_headache(followup_norm):
                    weights["COG"] = weights.get("COG", 0.0) + 0.08  # 0.10 * 0.8
                    flags.append("Reaction pattern: Headache → COG +0.08 (80%)")

                if self._detect_gi_symptoms(followup_norm):
                    weights["GA"] = weights.get("GA", 0.0) + 0.16  # 0.20 * 0.8
                    flags.append("Reaction pattern: GI symptoms → GA +0.16 (80%)")

                if self._detect_allergic_symptoms(followup_norm):
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.08  # 0.10 * 0.8
                    weights["SKN"] = weights.get("SKN", 0.0) + 0.04  # 0.05 * 0.8
                    flags.append("Reaction pattern: Allergic symptoms → IMM +0.08, SKN +0.04 (80%)")

                # Beverage-specific add-ons (at 80%)
                if self._detect_red_wine(followup_norm):
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.08
                    weights["GA"] = weights.get("GA", 0.0) + 0.08
                    weights["COG"] = weights.get("COG", 0.0) + 0.04
                    flags.append("Beverage trigger: Red wine → IMM +0.08, GA +0.08, COG +0.04 (80%)")

                if self._detect_beer(followup_norm):
                    weights["GA"] = weights.get("GA", 0.0) + 0.08
                    weights["IMM"] = weights.get("IMM", 0.0) + 0.04
                    flags.append("Beverage trigger: Beer → GA +0.08, IMM +0.04 (80%)")

                if self._detect_spirits(followup_norm):
                    weights["DTX"] = weights.get("DTX", 0.0) + 0.08
                    weights["GA"] = weights.get("GA", 0.0) + 0.08
                    flags.append("Beverage trigger: Spirits → DTX +0.08, GA +0.08 (80%)")
            else:
                # Preference/religious (no symptoms) → no change
                flags.append("Rarely drink by preference (no symptoms detected)")

        # A3) No → no change
        elif choice == "no":
            flags.append("No alcohol flushing (no weights applied)")

        # Cross-field synergies (apply to all choices if applicable)
        # East Asian ancestry
        is_east_asian = bool(re.search(r'\b(east asian|chinese|japanese|korean|taiwanese|asian)\b', ancestry_norm))
        if is_east_asian and choice != "no":
            weights["DTX"] = weights.get("DTX", 0.0) + 0.10
            weights["GA"] = weights.get("GA", 0.0) + 0.05
            flags.append("Cross-field synergy: East Asian ancestry → DTX +0.10, GA +0.05 (ALDH2 phenotype likelihood)")

        # Known GERD/Barrett's
        if re.search(r'\b(gerd|barrett|barretts)\b', diagnoses_other_norm):
            weights["GA"] = weights.get("GA", 0.0) + 0.10
            flags.append("Cross-field synergy: GERD/Barrett's + alcohol → GA +0.10 (mucosal irritation)")

        # History of migraine
        has_migraine = any(re.search(r'\bmigraine\b', d) for d in diagnoses_norm)
        if has_migraine:
            weights["COG"] = weights.get("COG", 0.0) + 0.10
            flags.append("Cross-field synergy: Migraine history + alcohol → COG +0.10")

        # Asthma/allergic rhinitis with wine/beer triggers
        has_asthma = any(re.search(r'\basthma\b', d) for d in diagnoses_norm)
        has_allergic_rhinitis = any(re.search(r'\b(allergic rhinitis|hay fever)\b', d) for d in diagnoses_norm)
        has_wine_beer_triggers = bool(re.search(r'\b(wine|beer)\b', followup_norm))

        if (has_asthma or has_allergic_rhinitis) and has_wine_beer_triggers:
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10
            flags.append("Cross-field synergy: Asthma/allergic rhinitis + wine/beer triggers → IMM +0.10 (histamine/sulfite intolerance)")

        # Apply per-field cap
        for domain in weights:
            if weights[domain] > self.MAX_WEIGHT:
                flags.append(f"Per-field cap applied: {domain} capped at +{self.MAX_WEIGHT:.2f}")
                weights[domain] = self.MAX_WEIGHT

        # Remove zero/negative weights
        weights = {k: v for k, v in weights.items() if v > 0}

        return weights, flags

