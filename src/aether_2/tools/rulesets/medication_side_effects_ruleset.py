"""
Medication Side Effects Ruleset for Focus Area Scoring.

Scores based on adverse drug reactions (ADRs) and medication side effects.
"""

from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class MedicationSideEffectsRuleset:
    """Ruleset for medication side effects-based focus area scoring."""
    
    def get_medication_side_effects_weights(
        self,
        has_adverse_reactions: bool,
        reaction_details: str,
        current_medications: List[Dict],
        current_supplements: List[Dict]
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on medication side effects.
        
        Args:
            has_adverse_reactions: Whether patient has adverse reactions
            reaction_details: Free-text description of reactions
            current_medications: List of current medications
            current_supplements: List of current supplements
            
        Returns:
            Tuple of (cumulative_scores, per_pattern_breakdown)
        """
        # Early exit if no adverse reactions
        if not has_adverse_reactions:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_pattern_breakdown = {}
        
        # 1) Baseline: Any adverse reaction
        baseline_scores = {code: 0.0 for code in FOCUS_AREAS}
        baseline_scores["DTX"] = 0.15
        baseline_scores["IMM"] = 0.10
        per_pattern_breakdown["Baseline ADR"] = baseline_scores.copy()
        
        for code in FOCUS_AREAS:
            cumulative_scores[code] += baseline_scores[code]
        
        # If no reaction details, return baseline only
        if not reaction_details:
            self._clamp_scores(cumulative_scores)
            return (cumulative_scores, per_pattern_breakdown)
        
        reaction_text_lower = reaction_details.lower()
        
        # 2) Immune-type reactions
        immune_scores = self._detect_immune_reactions(reaction_text_lower)
        if any(score != 0 for score in immune_scores.values()):
            per_pattern_breakdown["Immune-type Reaction"] = immune_scores.copy()
            for code in FOCUS_AREAS:
                cumulative_scores[code] += immune_scores[code]
        
        # 3) SCAR (Severe Cutaneous Adverse Reactions)
        scar_scores = self._detect_scar_reactions(reaction_text_lower)
        if any(score != 0 for score in scar_scores.values()):
            per_pattern_breakdown["SCAR (Severe Cutaneous)"] = scar_scores.copy()
            for code in FOCUS_AREAS:
                cumulative_scores[code] += scar_scores[code]
        
        # 4) Liver-pattern (DILI)
        dili_scores = self._detect_dili_reactions(reaction_text_lower)
        if any(score != 0 for score in dili_scores.values()):
            per_pattern_breakdown["DILI (Liver)"] = dili_scores.copy()
            for code in FOCUS_AREAS:
                cumulative_scores[code] += dili_scores[code]
        
        # 5) GI-pattern reactions
        gi_scores = self._detect_gi_reactions(
            reaction_text_lower, 
            current_medications, 
            current_supplements
        )
        if any(score != 0 for score in gi_scores.values()):
            per_pattern_breakdown["GI-pattern"] = gi_scores.copy()
            for code in FOCUS_AREAS:
                cumulative_scores[code] += gi_scores[code]
        
        # 6) CNS/COG pattern
        cns_scores = self._detect_cns_reactions(reaction_text_lower)
        if any(score != 0 for score in cns_scores.values()):
            per_pattern_breakdown["CNS/COG-pattern"] = cns_scores.copy()
            for code in FOCUS_AREAS:
                cumulative_scores[code] += cns_scores[code]
        
        # 7) Multiple products check
        multi_product_scores = self._detect_multiple_products(reaction_text_lower)
        if any(score != 0 for score in multi_product_scores.values()):
            per_pattern_breakdown["Multiple Products"] = multi_product_scores.copy()
            for code in FOCUS_AREAS:
                cumulative_scores[code] += multi_product_scores[code]
        
        # Clamp scores
        self._clamp_scores(cumulative_scores)
        
        return (cumulative_scores, per_pattern_breakdown)
    
    def _detect_immune_reactions(self, reaction_text: str) -> Dict[str, float]:
        """Detect immune-type reactions (hives, urticaria, rash, angioedema, wheeze, anaphylaxis)."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Check for anaphylaxis (highest severity)
        if "anaphylaxis" in reaction_text or "anaphylactic" in reaction_text:
            scores["IMM"] = 0.30
            return scores
        
        # Check for immune-type keywords
        immune_keywords = [
            "hives", "urticaria", "pruritic", "rash", "angioedema", 
            "wheeze", "drug allergy", "allergic reaction"
        ]
        
        if any(keyword in reaction_text for keyword in immune_keywords):
            scores["IMM"] = 0.20
            scores["SKN"] = 0.05
            
            # Check for HLA risk or genetic test
            if any(keyword in reaction_text for keyword in ["hla", "genetic test", "abacavir", "carbamazepine"]):
                scores["IMM"] += 0.10
        
        return scores
    
    def _detect_scar_reactions(self, reaction_text: str) -> Dict[str, float]:
        """Detect SCAR (Severe Cutaneous Adverse Reactions): SJS/TEN, DRESS, AGEP."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        scar_keywords = [
            "sjs", "ten", "stevens-johnson", "stevens johnson", 
            "dress", "agep", "toxic epidermal necrolysis"
        ]
        
        if any(keyword in reaction_text for keyword in scar_keywords):
            scores["IMM"] = 0.40
            scores["SKN"] = 0.20
            scores["DTX"] = 0.10

        return scores

    def _detect_dili_reactions(self, reaction_text: str) -> Dict[str, float]:
        """Detect DILI (Drug-Induced Liver Injury) reactions."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        dili_keywords = [
            "elevated ast", "elevated alt", "hepatitis", "jaundice",
            "dark urine", "pale stool", "liver enzyme", "liver damage",
            "liver injury", "liver toxicity"
        ]

        if any(keyword in reaction_text for keyword in dili_keywords):
            scores["DTX"] = 0.40
            scores["IMM"] = 0.10

        return scores

    def _detect_gi_reactions(
        self,
        reaction_text: str,
        current_medications: List[Dict],
        current_supplements: List[Dict]
    ) -> Dict[str, float]:
        """Detect GI-pattern reactions with class-specific modifiers."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Check for GI keywords
        gi_keywords = [
            "nausea", "vomiting", "diarrhea", "constipation", "cramps",
            "bloating", "reflux", "heartburn", "stomach", "abdominal", "epigastric",
            "upset stomach", "gi upset", "black stool", "ulcer", "dyspepsia"
        ]

        has_gi_reaction = any(keyword in reaction_text for keyword in gi_keywords)

        if not has_gi_reaction:
            return scores

        # Baseline GI sensitivity
        scores["GA"] = 0.25

        # Get medication names for class-specific modifiers
        med_names_lower = []
        if current_medications:
            for med in current_medications:
                med_name = med.get("name", "").lower()
                if med_name:
                    med_names_lower.append(med_name)

        # Check reaction text for medication mentions
        reaction_med_mentions = reaction_text

        # Antibiotic-associated diarrhea
        antibiotic_keywords = [
            "antibiotic", "amoxicillin", "azithromycin", "ciprofloxacin",
            "doxycycline", "cephalexin", "clindamycin", "metronidazole",
            "levofloxacin", "augmentin", "penicillin"
        ]

        has_antibiotic = any(keyword in reaction_med_mentions for keyword in antibiotic_keywords)
        has_antibiotic_med = any(keyword in " ".join(med_names_lower) for keyword in antibiotic_keywords)

        if (has_antibiotic or has_antibiotic_med) and "diarrhea" in reaction_text:
            scores["GA"] = 0.30

        # Opioid-induced constipation
        opioid_keywords = [
            "opioid", "oxycodone", "hydrocodone", "morphine", "codeine",
            "tramadol", "fentanyl", "oxycontin", "vicodin", "percocet"
        ]

        has_opioid = any(keyword in reaction_med_mentions for keyword in opioid_keywords)
        has_opioid_med = any(keyword in " ".join(med_names_lower) for keyword in opioid_keywords)

        if (has_opioid or has_opioid_med) and "constipation" in reaction_text:
            scores["GA"] = 0.20

        # NSAID dyspepsia/ulcer
        nsaid_keywords = [
            "nsaid", "ibuprofen", "naproxen", "aspirin", "advil", "aleve",
            "motrin", "celebrex", "diclofenac", "indomethacin"
        ]

        has_nsaid = any(keyword in reaction_med_mentions for keyword in nsaid_keywords)
        has_nsaid_med = any(keyword in " ".join(med_names_lower) for keyword in nsaid_keywords)

        if has_nsaid or has_nsaid_med:
            if any(keyword in reaction_text for keyword in ["black stool", "epigastric", "ulcer", "dyspepsia"]):
                scores["GA"] = max(scores["GA"], 0.20)
                scores["DTX"] += 0.05

        # Metformin GI intolerance
        has_metformin = "metformin" in reaction_med_mentions or any("metformin" in name for name in med_names_lower)

        if has_metformin:
            scores["GA"] = 0.20

        # Probiotic/fiber helped (protective)
        probiotic_helped_keywords = [
            "probiotic helped", "fiber helped", "psyllium helped",
            "probiotic improved", "fiber improved", "better with probiotic"
        ]

        if any(keyword in reaction_text for keyword in probiotic_helped_keywords):
            scores["GA"] -= 0.10

        # Cap GA at +0.50
        if scores["GA"] > 0.50:
            scores["GA"] = 0.50

        return scores

    def _detect_cns_reactions(self, reaction_text: str) -> Dict[str, float]:
        """Detect CNS/COG pattern from pharmacogenomics."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Check for CNS/COG keywords
        cns_keywords = [
            "extreme sedation", "very sedated", "drowsy", "drowsiness",
            "jittery", "agitated", "restless", "anxiety", "panic",
            "ssri", "antidepressant", "codeine", "tramadol",
            "cyp2d6", "cyp2c19", "poor metabolizer", "ultra-rapid metabolizer"
        ]

        has_cns_reaction = any(keyword in reaction_text for keyword in cns_keywords)

        if not has_cns_reaction:
            return scores

        scores["DTX"] = 0.10

        # Determine if sedation or stimulation
        sedation_keywords = ["sedation", "sedated", "drowsy", "drowsiness", "sleepy"]
        stimulation_keywords = ["jittery", "agitated", "restless", "anxiety", "panic", "insomnia"]

        if any(keyword in reaction_text for keyword in sedation_keywords):
            scores["COG"] = 0.10
        elif any(keyword in reaction_text for keyword in stimulation_keywords):
            scores["STR"] = 0.10
        else:
            # Default to COG if unclear
            scores["COG"] = 0.10

        return scores

    def _detect_multiple_products(self, reaction_text: str) -> Dict[str, float]:
        """Detect if ≥2 different products caused similar reactions."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Keywords suggesting multiple products
        multiple_keywords = [
            "multiple medications", "several medications", "different medications",
            "multiple drugs", "several drugs", "different drugs",
            "both", "all of them", "each time"
        ]

        has_multiple = any(keyword in reaction_text for keyword in multiple_keywords)

        if not has_multiple:
            return scores

        # Determine dominant pattern
        if any(keyword in reaction_text for keyword in ["rash", "hives", "itching", "allergic"]):
            scores["IMM"] = 0.10
        elif any(keyword in reaction_text for keyword in ["nausea", "diarrhea", "stomach", "gi", "digestive"]):
            scores["GA"] = 0.10
        else:
            # Default to immune if unclear
            scores["IMM"] = 0.10

        return scores

    def _clamp_scores(self, scores: Dict[str, float]) -> None:
        """Clamp all scores at [0.0, 1.0]."""
        for code in FOCUS_AREAS:
            scores[code] = max(0.0, min(scores[code], 1.0))

