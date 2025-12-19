"""
High Sugar Childhood Diet focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple
from .constants import FOCUS_AREAS


class HighSugarChildhoodDietRuleset:
    """Ruleset for high sugar childhood diet focus area scoring."""
    
    def get_high_sugar_childhood_diet_weights(
        self,
        high_sugar_childhood_diet: Optional[str]
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on high sugar childhood diet status.
        
        Args:
            high_sugar_childhood_diet: High sugar childhood diet status ("yes", "no", "not_sure")
            
        Returns:
            Tuple of (scores dict, description string)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        if not high_sugar_childhood_diet:
            return (scores, "Unknown")
        
        status = high_sugar_childhood_diet.lower().strip()
        
        # A) No - protective
        if status == "no":
            scores["CM"] = -0.05
            scores["GA"] = -0.05
            description = "No"
        
        # B) Not sure
        elif status == "not_sure":
            scores["CM"] = 0.10
            scores["GA"] = 0.10
            description = "Not sure"
        
        # C) Yes
        elif status == "yes":
            scores["CM"] = 0.25
            scores["GA"] = 0.20
            scores["HRM"] = 0.05
            scores["MITO"] = 0.05
            description = "Yes"
        
        else:
            # Unknown status
            description = "Unknown"
        
        return (scores, description)

