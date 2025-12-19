from typing import Dict, Any, List, Tuple
from src.aether_2.utils.text_processing import split_by_delimiters
from .constants import FOCUS_AREAS


class LifestyleWillingnessRuleset:
    """
    Ruleset for evaluating lifestyle change willingness.

    Returns adherence multiplier (AM) based on:
    - Yes/No response to willingness question
    - Number of concrete goals (from field 0)
    - Work stress level
    """
    
    # AM (Adherence Multiplier) bounds
    AM_MIN = 0.60
    AM_MAX = 1.10
    
    def get_lifestyle_willingness_am(
        self,
        willingness_response: str,
        age: int = None,
        top_goals_text: str = "",
        occupation_data: Dict[str, Any] = None
    ) -> float:
        """
        Calculate adherence multiplier (AM) based on lifestyle willingness.
        
        Args:
            willingness_response: "Yes" or "No" (or variations)
            age: Patient age (must be >= 18)
            top_goals_text: Text from field 0 (top health goals)
            occupation_data: Dict with work_stress_level
        
        Returns:
            Adherence multiplier (AM) clamped between 0.60 and 1.10
        """
        # Age check: only evaluate if age >= 18
        if age and age < 18:
            return 1.0  # Default AM for under 18
        
        # Normalize response
        response_lower = str(willingness_response).lower().strip()
        
        # Base rule
        if response_lower in ["yes", "y", "true", "1"]:
            am = 1.00
        elif response_lower in ["no", "n", "false", "0"]:
            am = 0.75
        else:
            # Unknown response - default to neutral
            am = 0.875  # Midpoint between Yes and No
        
        # Bonus: If ≥2 concrete lifestyle goals
        if top_goals_text:
            goals_list = split_by_delimiters(top_goals_text)
            if len(goals_list) >= 2:
                am += 0.05
        
        # Bonus: If work stress level >= 8
        if occupation_data:
            work_stress_level = occupation_data.get("work_stress_level", 0)
            try:
                stress_level = int(work_stress_level) if work_stress_level else 0
                if stress_level >= 8:
                    # Note: Spec doesn't specify the bonus amount, using +0.05 as default
                    am += 0.05
            except (ValueError, TypeError):
                pass
        
        # Clamp AM between 0.60 and 1.10
        am = max(self.AM_MIN, min(am, self.AM_MAX))
        
        return am
    
    def get_lifestyle_willingness_weights(
        self,
        willingness_response: str,
        age: int = None,
        top_goals_text: str = "",
        occupation_data: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on lifestyle willingness.
        
        This applies the AM as a multiplier to all focus areas equally,
        or returns zero scores if you want to handle AM separately.
        
        For now, returns zero scores as AM is typically used as a separate multiplier.
        """
        # AM is typically used as a separate multiplier, not as focus area scores
        # If you want to apply AM to all domains, you can do that in the caller
        return {code: 0.0 for code in FOCUS_AREAS}




