"""
Trouble Staying Asleep Ruleset

Scores focus areas based on sleep maintenance difficulty (maintenance insomnia).

Evidence:
- Chronic awakenings: Associated with hyperarousal (↑sympathetic/↑cortisol) and worse cardiometabolic control
- Frequency scaling: More frequent awakenings indicate greater sleep fragmentation and stress-axis dysregulation

Decision tree:
A) No trouble staying asleep → Protective: STR -0.05, COG -0.05
B) Yes (maintenance insomnia) → Base: STR +0.20, COG +0.10, CM +0.05, IMM +0.05, MITO +0.05
   B1) Frequency scaling: Add STR +0.05 × wakings_per_night, capped at +0.25
   B2) Reflux/URTI overlay: If reflux/heartburn OR URTI-cough → GA +0.25
   B3) Severe reflux: If wakings ≥2 AND (throat burn OR cough OR acid taste) → GA +0.35
   B4) Nocturia (male): If sex=male AND night_wake_frequency>0 → STR +0.05

References: ScienceDirect, CDC

Author: Aether AI Engine
Date: 2025-11-19
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class TroubleStayingAsleepRuleset:
    """Ruleset for sleep maintenance difficulty scoring."""
    
    TOP_N_CONTRIBUTORS = 1
    
    def get_trouble_staying_asleep_weights(
        self,
        trouble_staying_asleep: Optional[bool],
        night_wake_frequency: Optional[int] = None,
        night_urination_frequency: Optional[int] = None,
        digestive_symptoms: Optional[str] = None,
        biological_sex: Optional[str] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on sleep maintenance difficulty.

        Args:
            trouble_staying_asleep: True if has difficulty staying asleep, False otherwise
            night_wake_frequency: Number of times waking per night (for frequency scaling)
            night_urination_frequency: Number of times urinating per night (alternative measure)
            digestive_symptoms: Comma-separated digestive symptoms (for reflux/URTI detection)
            biological_sex: "Male" or "Female" (for nocturia detection)

        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no data provided, return zeros
        if trouble_staying_asleep is None:
            return (scores, "")
        
        # A) No trouble staying asleep (protective)
        if not trouble_staying_asleep:
            scores["STR"] = -0.05
            scores["COG"] = -0.05
            return (scores, "No")
        
        # B) Yes - maintenance insomnia core
        scores["STR"] = 0.20
        scores["COG"] = 0.10
        scores["CM"] = 0.05
        scores["IMM"] = 0.05
        scores["MITO"] = 0.05
        
        description = "Yes"
        
        # B1) Frequency scaling
        # Use night_wake_frequency if available, otherwise fall back to night_urination_frequency
        wakings = night_wake_frequency if night_wake_frequency is not None else night_urination_frequency

        if wakings is not None and wakings > 0:
            # Add +0.05 × wakings_per_night to STR, capped at +0.25
            frequency_add = min(0.05 * wakings, 0.25)
            scores["STR"] += frequency_add

            # Add frequency to description
            description += f" ({wakings}x/night)"

        # B2) Reflux/URTI overlay
        # Check for reflux/heartburn OR URTI-cough in digestive symptoms
        has_reflux = False
        has_severe_reflux = False

        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()

            # Reflux keywords
            reflux_keywords = ['reflux', 'heartburn', 'gerd', 'acid']
            # URTI/cough keywords
            urti_keywords = ['cough', 'throat', 'urti']
            # Severe reflux keywords (for wakings ≥2 check)
            severe_keywords = ['throat burn', 'acid taste', 'cough']

            # Check for basic reflux/URTI
            for keyword in reflux_keywords + urti_keywords:
                if keyword in symptoms_lower:
                    has_reflux = True
                    break

            # Check for severe reflux symptoms (if wakings ≥2)
            if wakings is not None and wakings >= 2:
                for keyword in severe_keywords:
                    if keyword in symptoms_lower:
                        has_severe_reflux = True
                        break

        # Apply GA penalties
        if has_severe_reflux:
            # B3) Severe reflux: wakings ≥2 AND reflux symptoms
            scores["GA"] += 0.35
        elif has_reflux:
            # B2) Basic reflux/URTI
            scores["GA"] += 0.25

        # B4) Nocturia (male): If sex=male AND night_wake_frequency>0
        if biological_sex and biological_sex.lower() == "male":
            if night_wake_frequency is not None and night_wake_frequency > 0:
                scores["STR"] += 0.05

        return (scores, description)

