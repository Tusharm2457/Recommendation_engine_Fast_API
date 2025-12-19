"""
Eating Out Frequency focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple
from .constants import FOCUS_AREAS


class EatingOutRuleset:
    """Ruleset for eating out frequency focus area scoring."""
    
    def get_eating_out_weights(
        self,
        eating_out_frequency: Optional[str],
        diagnoses: Optional[str] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on eating out frequency.
        
        Args:
            eating_out_frequency: Eating out frequency ("1_2_per_week" or "more_than_2_per_week")
            diagnoses: Comma-separated diagnoses string (for celiac/NCGS, lactose intolerance detection)
            
        Returns:
            Tuple of (scores dict, description string)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        if not eating_out_frequency:
            return (scores, "Unknown")
        
        frequency = eating_out_frequency.lower().strip()
        
        # Detect celiac/NCGS and lactose intolerance
        has_celiac_ncgs = False
        has_lactose_intolerance = False
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            celiac_keywords = ['celiac', 'ncgs', 'non-celiac gluten sensitivity', 'gluten sensitivity']
            lactose_keywords = ['lactose intolerance', 'lactose intolerant']
            has_celiac_ncgs = any(keyword in diagnoses_lower for keyword in celiac_keywords)
            has_lactose_intolerance = any(keyword in diagnoses_lower for keyword in lactose_keywords)
        
        # A1) 1-2×/week
        if frequency == "1_2_per_week":
            scores["CM"] = 0.25
            scores["DTX"] = 0.15
            scores["IMM"] = 0.10
            scores["SKN"] = 0.10
            scores["GA"] = 0.15
            
            # Dependencies
            if has_celiac_ncgs:
                scores["GA"] += 0.20
            if has_lactose_intolerance:
                scores["GA"] += 0.10
            
            description = "1-2 times/week"
        
        # A2) >2×/week
        elif frequency == "more_than_2_per_week":
            scores["CM"] = 0.60
            scores["DTX"] = 0.40
            scores["IMM"] = 0.30
            scores["SKN"] = 0.20
            scores["GA"] = 0.35
            
            # Dependencies
            if has_celiac_ncgs:
                scores["GA"] += 0.20
            if has_lactose_intolerance:
                scores["GA"] += 0.10
            
            description = ">2 times/week"
        
        else:
            # Unknown frequency
            description = "Unknown"
        
        return (scores, description)

