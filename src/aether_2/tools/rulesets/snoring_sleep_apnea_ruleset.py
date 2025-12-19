"""
Snoring/Sleep Apnea focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple
from .constants import FOCUS_AREAS


class SnoringApneaRuleset:
    """Ruleset for snoring/sleep apnea focus area scoring."""
    
    def get_snoring_apnea_weights(
        self,
        snoring_sleep_apnea: Optional[str],
        digestive_symptoms: Optional[str] = None,
        wake_feeling_refreshed: bool = False,
        diagnoses: Optional[str] = None,
        bmi: Optional[float] = None,
        age: Optional[int] = None,
        biological_sex: Optional[str] = None,
        night_wake_frequency: Optional[int] = None,
        alcohol_frequency: Optional[str] = None,
        tobacco_use_status: Optional[str] = None,
        shift_work: bool = False,
        trouble_staying_asleep: bool = False
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on snoring/sleep apnea status.
        
        Args:
            snoring_sleep_apnea: Snoring/sleep apnea status ("no", "not_sure", "yes")
            digestive_symptoms: Digestive symptoms string (for reflux/GERD detection)
            wake_feeling_refreshed: Whether patient wakes feeling refreshed
            diagnoses: Comma-separated diagnoses string (for hypertension detection)
            bmi: Body mass index
            age: Patient age
            biological_sex: Biological sex ("Male", "Female")
            night_wake_frequency: Number of night wakings
            alcohol_frequency: Alcohol consumption frequency
            tobacco_use_status: Tobacco use status
            shift_work: Whether patient works shifts
            trouble_staying_asleep: Whether patient has trouble staying asleep
            
        Returns:
            Tuple of (scores dict, description string)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        if not snoring_sleep_apnea:
            return (scores, "Unknown")
        
        status = snoring_sleep_apnea.lower().strip()
        
        # Detect reflux/heartburn
        has_reflux = False
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            reflux_keywords = ['reflux', 'heartburn', 'gerd', 'acid']
            has_reflux = any(keyword in symptoms_lower for keyword in reflux_keywords)
        
        # Detect severe GERD (≥2 wakings + throat burn/cough/acid taste)
        has_severe_gerd = False
        if night_wake_frequency and night_wake_frequency >= 2 and digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            gerd_keywords = ['throat', 'burn', 'cough', 'acid']
            has_severe_gerd = any(keyword in symptoms_lower for keyword in gerd_keywords)
        
        # Detect hypertension
        has_hypertension = False
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            hypertension_keywords = ['hypertension', 'high blood pressure', 'htn']
            has_hypertension = any(keyword in diagnoses_lower for keyword in hypertension_keywords)
        
        # A) No - protective
        if status == "no":
            scores["STR"] = -0.05
            scores["COG"] = -0.05
            return (scores, "No")
        
        # B) Not sure
        elif status == "not_sure":
            scores["CM"] = 0.15
            scores["STR"] = 0.10
            scores["COG"] = 0.05
            scores["MITO"] = 0.05
            
            # B1) Reflux/heartburn overlay
            if has_reflux:
                scores["GA"] += 0.15
            
            description = "Not sure"
        
        # C) Yes
        elif status == "yes":
            scores["CM"] = 0.35
            scores["COG"] = 0.15
            scores["STR"] = 0.15
            scores["MITO"] = 0.10
            
            # C1) Unrefreshing sleep overlay (only for "yes")
            if not wake_feeling_refreshed:
                scores["CM"] += 0.10
                scores["COG"] += 0.05
            
            # C2) Hypertension overlay (only for "yes")
            if has_hypertension:
                scores["CM"] += 0.15
            
            # C3) BMI ≥35 overlay (only for "yes")
            if bmi and bmi >= 35:
                scores["CM"] += 0.10
            
            # C4) Age ≥50 or male sex (only for "yes")
            if (age and age >= 50) or (biological_sex and biological_sex.lower() == "male"):
                scores["CM"] += 0.05
            
            # C5) GERD-specific refinements (only for "yes")
            if has_severe_gerd:
                scores["GA"] += 0.10
            
            description = "Yes"
        
        else:
            return (scores, "Unknown")
        
        # Universal modifiers (apply to all cases except "no")
        
        # Daily alcohol
        if alcohol_frequency and alcohol_frequency.lower() == "daily":
            scores["STR"] += 0.05
            # If GERD co-flagged, add GA penalty
            if has_reflux:
                scores["GA"] += 0.05
        
        # Tobacco/nicotine use
        if tobacco_use_status and tobacco_use_status.lower() == "yes":
            scores["STR"] += 0.05
        
        # Shift work
        if shift_work:
            scores["STR"] += 0.05
        
        # Trouble staying asleep
        if trouble_staying_asleep:
            scores["STR"] += 0.05
        
        return (scores, description)

