"""
Sleep Hours Ruleset

Scores focus areas based on sleep duration category.

Evidence:
- Short sleep (<6h): Raises stress-axis tone, reduces insulin sensitivity, increases infection risk
  Europe PMC, ScienceDirect
- Adequate (6-8h): CDC recommendation, better metabolic/immune/mental outcomes
  CDC
- Restorative (8-10h): Within/above recommended range, restorative when regular
  CDC
- Long sleep (>10h): Associated with fatigue, hypomotility, age-sensitive cognitive effects
  Frontiers

Categories:
- less_than_6: Short sleep
- 6_to_8: Adequate for many adults
- 8_to_10: Restorative window
- more_than_10: Long sleep

Modifiers:
- Shift work: Adds STR +0.10 for irregular schedules
- Age ≥65 + long sleep: Adds COG +0.10
- Fatigue/hypersomnolence + long sleep: GA +0.20 (vs +0.10 base)

Author: Aether AI Engine
Date: 2025-11-19
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class SleepHoursRuleset:
    """Ruleset for sleep duration scoring."""
    
    TOP_N_CONTRIBUTORS = 1
    
    def get_sleep_hours_weights(
        self,
        sleep_hours_category: Optional[str],
        age: Optional[int],
        shift_work: bool = False,
        has_fatigue: bool = False
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on sleep duration.
        
        Args:
            sleep_hours_category: One of: less_than_6, 6_to_8, 8_to_10, more_than_10
            age: User's age in years
            shift_work: Whether user does shift work (circadian mismatch)
            has_fatigue: Whether user reports fatigue/hypersomnolence
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no category provided, return zeros
        if not sleep_hours_category:
            return (scores, "")
        
        # Normalize category
        category = sleep_hours_category.strip().lower()
        
        # A) <6 hours (short sleep)
        if category == "less_than_6":
            scores["STR"] = 0.40
            scores["CM"] = 0.20
            scores["MITO"] = 0.15
            scores["IMM"] = 0.15
            scores["GA"] = 0.15
            scores["COG"] = 0.05
            
            description = "Short sleep (<6h)"
        
        # B) 6-8 hours (adequate for many adults)
        elif category == "6_to_8":
            scores["STR"] = -0.05
            scores["CM"] = -0.05
            scores["IMM"] = -0.05
            scores["GA"] = -0.05
            
            description = "Adequate (6-8h)"
        
        # C) 8-10 hours (restorative window)
        elif category == "8_to_10":
            scores["STR"] = -0.10
            scores["CM"] = -0.10
            scores["IMM"] = -0.05
            scores["GA"] = -0.05
            scores["COG"] = -0.05
            
            description = "Restorative (8-10h)"
        
        # D) >10 hours (long sleep)
        elif category == "more_than_10":
            scores["MITO"] = 0.20
            scores["STR"] = 0.05
            scores["CM"] = 0.05
            
            # GI rule: fatigue/hypersomnolence signal
            if has_fatigue:
                scores["GA"] = 0.20
            else:
                scores["GA"] = 0.10
            
            # Cognition (age-sensitive): Age ≥65
            if age and age >= 65:
                scores["COG"] = 0.10
            
            description = "Long sleep (>10h)"
        
        else:
            # Unknown category
            return (scores, "")
        
        # Shift work modifier: irregular schedule adds STR +0.10
        if shift_work:
            scores["STR"] += 0.10
        
        return (scores, description)

