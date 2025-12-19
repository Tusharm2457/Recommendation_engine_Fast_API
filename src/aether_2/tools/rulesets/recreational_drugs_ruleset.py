"""
Recreational Drugs Ruleset

Parses free-text substance use and calculates focus area scores based on:
1. Substance type (cannabis, opioids, stimulants, MDMA, hallucinogens, ketamine, inhalants, synthetic cannabinoids)
2. Frequency (occasional ≤monthly, weekly, daily)
3. Route modifiers (smoked/vaped, injection)
4. Symptom modifiers (nausea, constipation, etc.)

Evidence-based scoring from NIDA, PubMed, CDC, and SME clinical observations.

Substance Categories:
A) Cannabis: COG, STR base; route/symptom modifiers for IMM, SKN, GA
B) Opioids: STR, DTX, MITO base; GA for constipation; IMM/DTX for injection
C) Stimulants: STR, MITO, CM, DTX base; GA for GI symptoms
D) MDMA: STR, MITO, DTX per use
E) Hallucinogens: STR, COG (minimal)
F) Ketamine: DTX, STR (urinary concerns)
G) Inhalants: DTX, MITO, CM, COG (high toxicity)
H) Synthetic cannabinoids: DTX, STR, COG (higher risk than cannabis)
"""

from typing import Dict, Tuple, Optional, List
import re
from .constants import FOCUS_AREAS


class RecreationalDrugsRuleset:
    """Ruleset for recreational substance use scoring with text parsing."""
    
    def get_recreational_drugs_weights(
        self,
        uses_substances: bool,
        substance_details: Optional[str],
        digestive_symptoms: Optional[str] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on recreational substance use.
        
        Args:
            uses_substances: Boolean indicating if user uses recreational substances
            substance_details: Free-text description of substance use
            digestive_symptoms: Optional digestive symptoms for context
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no substance use, return zeros
        if not uses_substances or not substance_details:
            return (scores, "")
        
        text_lower = substance_details.lower()
        detected_substances = []
        
        # Detect and score each substance type
        # A) Cannabis
        if any(word in text_lower for word in ['cannabis', 'marijuana', 'weed', 'thc', 'pot', 'joint']):
            cannabis_scores, cannabis_desc = self._score_cannabis(text_lower, digestive_symptoms)
            for focus_area, weight in cannabis_scores.items():
                scores[focus_area] += weight
            detected_substances.append(cannabis_desc)
        
        # B) Opioids
        if any(word in text_lower for word in ['opioid', 'heroin', 'fentanyl', 'oxy', 'oxycodone', 'hydrocodone', 'morphine', 'opiate']):
            opioid_scores, opioid_desc = self._score_opioids(text_lower, digestive_symptoms)
            for focus_area, weight in opioid_scores.items():
                scores[focus_area] += weight
            detected_substances.append(opioid_desc)
        
        # C) Stimulants
        if any(word in text_lower for word in ['cocaine', 'coke', 'meth', 'methamphetamine', 'amphetamine', 'adderall', 'ritalin', 'stimulant']):
            stimulant_scores, stimulant_desc = self._score_stimulants(text_lower, digestive_symptoms)
            for focus_area, weight in stimulant_scores.items():
                scores[focus_area] += weight
            detected_substances.append(stimulant_desc)
        
        # D) MDMA
        if any(word in text_lower for word in ['mdma', 'ecstasy', 'molly', 'x']):
            mdma_scores, mdma_desc = self._score_mdma(text_lower)
            for focus_area, weight in mdma_scores.items():
                scores[focus_area] += weight
            detected_substances.append(mdma_desc)
        
        # E) Hallucinogens
        if any(word in text_lower for word in ['lsd', 'acid', 'psilocybin', 'mushroom', 'shroom', 'psychedelic', 'hallucinogen']):
            hallucinogen_scores, hallucinogen_desc = self._score_hallucinogens(text_lower)
            for focus_area, weight in hallucinogen_scores.items():
                scores[focus_area] += weight
            detected_substances.append(hallucinogen_desc)
        
        # F) Ketamine
        if any(word in text_lower for word in ['ketamine', 'ket', 'special k']):
            ketamine_scores, ketamine_desc = self._score_ketamine(text_lower)
            for focus_area, weight in ketamine_scores.items():
                scores[focus_area] += weight
            detected_substances.append(ketamine_desc)
        
        # G) Inhalants
        if any(word in text_lower for word in ['inhalant', 'solvent', 'aerosol', 'nitrite', 'popper', 'huff', 'glue', 'gas']):
            inhalant_scores, inhalant_desc = self._score_inhalants(text_lower)
            for focus_area, weight in inhalant_scores.items():
                scores[focus_area] += weight
            detected_substances.append(inhalant_desc)
        
        # H) Synthetic cannabinoids
        if any(word in text_lower for word in ['spice', 'k2', 'synthetic cannabinoid', 'synthetic weed']):
            synthetic_scores, synthetic_desc = self._score_synthetic_cannabinoids(text_lower)
            for focus_area, weight in synthetic_scores.items():
                scores[focus_area] += weight
            detected_substances.append(synthetic_desc)
        
        # Create combined description
        if detected_substances:
            description = "; ".join(detected_substances)
        else:
            # Generic substance use if no specific substance detected
            description = "Unspecified substance"
            scores["STR"] = 0.10
            scores["DTX"] = 0.10
        
        return (scores, description)
    
    def _detect_frequency(self, text: str) -> str:
        """
        Detect frequency from text.

        Returns: "daily", "weekly", or "occasional"
        """
        if any(word in text for word in ['daily', 'every day', 'everyday', 'all day']):
            return "daily"
        elif any(word in text for word in ['week', 'weekly', 'weekend', 'weekends', 'saturday', 'friday']):
            return "weekly"
        else:
            # Default to occasional if no clear frequency
            return "occasional"

    def _score_cannabis(self, text: str, digestive_symptoms: Optional[str]) -> Tuple[Dict[str, float], str]:
        """Score cannabis use based on frequency and route."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        frequency = self._detect_frequency(text)

        # Base scores by frequency
        if frequency == "daily":
            scores["COG"] = 0.15
            scores["STR"] = 0.15
            scores["IMM"] = 0.10
            scores["MITO"] = 0.10
        elif frequency == "weekly":
            scores["COG"] = 0.10
            scores["STR"] = 0.10
        else:  # occasional
            scores["COG"] = 0.05
            scores["STR"] = 0.05

        # Route modifiers
        is_smoked = any(word in text for word in ['smok', 'joint', 'blunt', 'vape', 'vaping'])

        if is_smoked:
            if frequency == "daily":
                scores["IMM"] += 0.15
                scores["SKN"] = 0.10
            elif frequency == "weekly":
                scores["IMM"] += 0.10
                scores["SKN"] = 0.05
            else:  # occasional
                scores["IMM"] += 0.05
                scores["SKN"] = 0.05

        # Symptom modifiers
        has_gi_symptoms = False
        if digestive_symptoms:
            has_gi_symptoms = any(word in digestive_symptoms.lower() for word in ['nausea', 'heartburn', 'vomit'])

        # Check text for CHS indicators
        has_chs_indicators = any(word in text for word in ['vomit', 'nausea', 'hot shower', 'cyclic'])

        if frequency == "daily" and has_chs_indicators:
            scores["GA"] = 0.20  # Cannabis hyperemesis syndrome
        elif frequency == "weekly" and (has_gi_symptoms or 'nausea' in text or 'heartburn' in text):
            scores["GA"] = 0.10

        # Create description
        route_str = "smoked/vaped" if is_smoked else "other route"
        description = f"Cannabis ({frequency}, {route_str})"

        return (scores, description)

    def _score_opioids(self, text: str, digestive_symptoms: Optional[str]) -> Tuple[Dict[str, float], str]:
        """Score opioid use based on frequency and route."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        frequency = self._detect_frequency(text)

        # Base scores by frequency
        if frequency == "daily":
            scores["STR"] = 0.40
            scores["MITO"] = 0.20
            scores["DTX"] = 0.30
            scores["COG"] = 0.10
            scores["GA"] = 0.60  # Opioid-induced constipation
        elif frequency == "weekly":
            scores["STR"] = 0.30
            scores["MITO"] = 0.10
            scores["DTX"] = 0.20
            scores["GA"] = 0.30
        else:  # occasional
            scores["STR"] = 0.20
            scores["DTX"] = 0.10
            # Check for constipation
            has_constipation = False
            if digestive_symptoms:
                has_constipation = 'constipation' in digestive_symptoms.lower()
            if has_constipation or 'constipation' in text:
                scores["GA"] = 0.20

        # Route modifiers
        is_injection = any(word in text for word in ['inject', 'iv', 'needle', 'shoot'])
        if is_injection:
            scores["IMM"] += 0.20
            scores["DTX"] += 0.20

        # Create description
        route_str = "injection" if is_injection else "other route"
        description = f"Opioids ({frequency}, {route_str})"

        return (scores, description)

    def _score_stimulants(self, text: str, digestive_symptoms: Optional[str]) -> Tuple[Dict[str, float], str]:
        """Score stimulant use (cocaine, meth, amphetamines)."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        frequency = self._detect_frequency(text)

        # Base scores by frequency
        if frequency == "daily":
            scores["STR"] = 0.50
            scores["MITO"] = 0.30
            scores["CM"] = 0.20
            scores["DTX"] = 0.20
            scores["COG"] = 0.10
            scores["GA"] = 0.20
        elif frequency == "weekly":
            scores["STR"] = 0.30
            scores["MITO"] = 0.20
            scores["CM"] = 0.10
            scores["DTX"] = 0.10
            scores["GA"] = 0.20
        else:  # occasional
            scores["STR"] = 0.20
            scores["MITO"] = 0.10
            scores["CM"] = 0.05
            scores["DTX"] = 0.10
            # Check for GI symptoms
            has_gi_symptoms = False
            if digestive_symptoms:
                has_gi_symptoms = any(word in digestive_symptoms.lower() for word in ['heartburn', 'dyspepsia'])
            if has_gi_symptoms or any(word in text for word in ['heartburn', 'dyspepsia']):
                scores["GA"] = 0.10

        # Determine substance type
        substance_type = "stimulants"
        if any(word in text for word in ['cocaine', 'coke']):
            substance_type = "cocaine"
        elif any(word in text for word in ['meth', 'methamphetamine']):
            substance_type = "methamphetamine"
        elif any(word in text for word in ['amphetamine', 'adderall']):
            substance_type = "amphetamines"

        description = f"{substance_type.capitalize()} ({frequency})"

        return (scores, description)

    def _score_mdma(self, text: str) -> Tuple[Dict[str, float], str]:
        """Score MDMA use (any frequency)."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Per use scores (any frequency)
        scores["STR"] = 0.20
        scores["MITO"] = 0.20
        scores["DTX"] = 0.10

        description = "MDMA"

        return (scores, description)

    def _score_hallucinogens(self, text: str) -> Tuple[Dict[str, float], str]:
        """Score hallucinogen use (LSD, psilocybin)."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Any use
        scores["STR"] = 0.10

        # Check for HPPD indicators
        has_hppd = any(word in text for word in ['visual trail', 'hppd', 'lingering visual', 'flashback'])
        if has_hppd:
            scores["COG"] = 0.05

        # Determine substance type
        substance_type = "hallucinogens"
        if any(word in text for word in ['lsd', 'acid']):
            substance_type = "LSD"
        elif any(word in text for word in ['psilocybin', 'mushroom', 'shroom']):
            substance_type = "psilocybin"

        description = substance_type.capitalize()

        return (scores, description)

    def _score_ketamine(self, text: str) -> Tuple[Dict[str, float], str]:
        """Score ketamine use based on frequency."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        frequency = self._detect_frequency(text)

        # Scores by frequency
        if frequency == "daily":
            scores["DTX"] = 0.20
            scores["STR"] = 0.20
        elif frequency == "weekly":
            scores["DTX"] = 0.10
            scores["STR"] = 0.10
        else:  # occasional - minimal scoring
            scores["DTX"] = 0.05
            scores["STR"] = 0.05

        description = f"Ketamine ({frequency})"

        return (scores, description)

    def _score_inhalants(self, text: str) -> Tuple[Dict[str, float], str]:
        """Score inhalant use (high toxicity)."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Any current use - high toxicity
        scores["DTX"] = 0.80
        scores["MITO"] = 0.20
        scores["CM"] = 0.10
        scores["COG"] = 0.10

        description = "Inhalants (high toxicity)"

        return (scores, description)

    def _score_synthetic_cannabinoids(self, text: str) -> Tuple[Dict[str, float], str]:
        """Score synthetic cannabinoid use (Spice, K2)."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Any use - higher risk than cannabis
        scores["DTX"] = 0.40
        scores["STR"] = 0.20
        scores["COG"] = 0.10

        description = "Synthetic cannabinoids (Spice/K2)"

        return (scores, description)

