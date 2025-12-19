"""
Wake Feeling Refreshed Ruleset

Scores focus areas based on sleep quality and restorative sleep.

Evidence:
- Restorative sleep: Protective for stress, cognition, and energy metabolism
- Non-restorative sleep: Associated with hyperarousal, metabolic strain, cognitive deficits

Decision tree:
A) Yes (wakes refreshed) → Protective: STR -0.05, COG -0.05, MITO -0.05
B) No (unrefreshing/non-restorative) → Base: STR +0.25, MITO +0.20, COG +0.10, CM +0.10, IMM +0.05
   B1) GI/sleep-gut axis: If bloating/IBS → GA +0.20
   B2) Hypothyroidism: If thyroid dx/abnormal TSH → HRM +0.15, CM +0.05
   B3) Shift work: STR +0.10
   B4) Daily alcohol: STR +0.05
   B5) Short sleep (<6h) + unrefreshed: CM +0.05, MITO +0.05 (dose-response)
   B6) Trouble staying asleep: STR +0.05

References: Sleep Health Journal, Diabetes Journals, OUP Academic, ScienceDirect, AHA Journals, Sleep Foundation

Author: Aether AI Engine
Date: 2025-11-19
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class WakeFeelingRefreshedRuleset:
    """Ruleset for sleep quality and restorative sleep scoring."""
    
    TOP_N_CONTRIBUTORS = 1
    
    def get_wake_feeling_refreshed_weights(
        self,
        wake_feeling_refreshed: Optional[bool],
        digestive_symptoms: Optional[str] = None,
        diagnoses: Optional[str] = None,
        shift_work: bool = False,
        alcohol_frequency: Optional[str] = None,
        sleep_hours_category: Optional[str] = None,
        trouble_staying_asleep: bool = False
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on sleep quality.
        
        Args:
            wake_feeling_refreshed: True if wakes feeling refreshed, False otherwise
            digestive_symptoms: Comma-separated digestive symptoms (for bloating/IBS detection)
            diagnoses: Comma-separated diagnoses (for hypothyroidism detection)
            shift_work: Whether user does shift work (circadian mismatch)
            alcohol_frequency: Alcohol consumption frequency (e.g., "daily")
            sleep_hours_category: Sleep duration category (for short sleep detection)
            trouble_staying_asleep: Whether user has trouble staying asleep
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no data provided, return zeros
        if wake_feeling_refreshed is None:
            return (scores, "")
        
        # A) Yes - wakes refreshed (protective)
        if wake_feeling_refreshed:
            scores["STR"] = -0.05
            scores["COG"] = -0.05
            scores["MITO"] = -0.05
            return (scores, "Yes")
        
        # B) No - unrefreshing/non-restorative sleep
        scores["STR"] = 0.25
        scores["MITO"] = 0.20
        scores["COG"] = 0.10
        scores["CM"] = 0.10
        scores["IMM"] = 0.05
        
        description = "No"
        
        # B1) GI/sleep-gut axis overlay
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            gi_keywords = ['bloating', 'ibs', 'irritable bowel']
            
            for keyword in gi_keywords:
                if keyword in symptoms_lower:
                    scores["GA"] += 0.20
                    break
        
        # B2) Hypothyroidism detection
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            thyroid_keywords = ['hypothyroid', 'thyroid', 'hashimoto', 'tsh']
            
            for keyword in thyroid_keywords:
                if keyword in diagnoses_lower:
                    scores["HRM"] += 0.15
                    scores["CM"] += 0.05
                    break
        
        # B3) Shift work modifier
        if shift_work:
            scores["STR"] += 0.10
        
        # B4) Daily alcohol modifier
        if alcohol_frequency and alcohol_frequency.lower() == "daily":
            scores["STR"] += 0.05
        
        # B5) Short sleep + unrefreshed (dose-response)
        if sleep_hours_category == "less_than_6":
            scores["CM"] += 0.05
            scores["MITO"] += 0.05
        
        # B6) Trouble staying asleep
        if trouble_staying_asleep:
            scores["STR"] += 0.05
        
        return (scores, description)

