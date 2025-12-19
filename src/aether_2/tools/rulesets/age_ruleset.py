"""
Age-based focus area scoring ruleset.
"""

from typing import Dict, Optional
from .constants import FOCUS_AREAS


class AgeRuleset:
    """Ruleset for age-based focus area scoring."""

    def get_age_weights(self, age: Optional[int]) -> Dict[str, float]:
        """
        Calculate focus area weights based on age.

        Args:
            age: Patient age in years

        Returns:
            Dictionary of focus area scores
        """
        if age is None:
            return {code: 0.0 for code in FOCUS_AREAS}

        if 18 <= age <= 25:
            return {"CM": 0.30, "COG": 0.50, "DTX": 0.30, "IMM": 0.30,
                    "MITO": 0.30, "SKN": 0.40, "STR": 0.40, "HRM": 0.50, "GA": 0.30}
        elif 26 <= age <= 39:
            return {"CM": 0.40, "COG": 0.30, "DTX": 0.30, "IMM": 0.20,
                    "MITO": 0.30, "SKN": 0.20, "STR": 0.50, "HRM": 0.40, "GA": 0.30}
        elif 40 <= age <= 49:
            return {"CM": 0.50, "COG": 0.30, "DTX": 0.30, "IMM": 0.30,
                    "MITO": 0.40, "SKN": 0.30, "STR": 0.50, "HRM": 0.50, "GA": 0.30}
        elif 50 <= age <= 59:
            return {"CM": 0.60, "COG": 0.40, "DTX": 0.40, "IMM": 0.30,
                    "MITO": 0.50, "SKN": 0.40, "STR": 0.40, "HRM": 0.60, "GA": 0.40}
        elif 60 <= age <= 69:
            return {"CM": 0.70, "COG": 0.60, "DTX": 0.50, "IMM": 0.50,
                    "MITO": 0.60, "SKN": 0.50, "STR": 0.40, "HRM": 0.30, "GA": 0.50}
        elif age >= 70:
            return {"CM": 0.80, "COG": 0.70, "DTX": 0.60, "IMM": 0.60,
                    "MITO": 0.70, "SKN": 0.60, "STR": 0.30, "HRM": 0.20, "GA": 0.60}
        else:
            from . import FOCUS_AREAS
            return {code: 0.0 for code in FOCUS_AREAS}
