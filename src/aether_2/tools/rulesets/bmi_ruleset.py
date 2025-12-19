"""
BMI-based focus area scoring ruleset.
"""

from typing import Dict, Optional
from .constants import FOCUS_AREAS


class BMIRuleset:
    """Ruleset for BMI-based focus area scoring."""

    def get_bmi_weights(self, bmi: Optional[float]) -> Dict[str, float]:
        """
        Calculate focus area weights based on BMI.

        Args:
            bmi: Body Mass Index

        Returns:
            Dictionary of focus area scores
        """
        if bmi is None:
            return {code: 0.0 for code in FOCUS_AREAS}

        if bmi < 18.5:  # Underweight
            return {"CM": 0.20, "COG": 0.30, "DTX": 0.30, "IMM": 0.50,
                    "MITO": 0.50, "SKN": 0.30, "STR": 0.30, "HRM": 0.30, "GA": 0.60}
        elif bmi < 25:  # Healthy
            return {"CM": 0.20, "COG": 0.20, "DTX": 0.20, "IMM": 0.20,
                    "MITO": 0.20, "SKN": 0.20, "STR": 0.25, "HRM": 0.20, "GA": 0.20}
        elif bmi < 30:  # Overweight
            return {"CM": 0.50, "COG": 0.30, "DTX": 0.35, "IMM": 0.35,
                    "MITO": 0.40, "SKN": 0.30, "STR": 0.30, "HRM": 0.40, "GA": 0.30}
        elif bmi < 35:  # Obesity I
            return {"CM": 0.60, "COG": 0.40, "DTX": 0.50, "IMM": 0.45,
                    "MITO": 0.50, "SKN": 0.40, "STR": 0.35, "HRM": 0.50, "GA": 0.40}
        elif bmi < 40:  # Obesity II
            return {"CM": 0.70, "COG": 0.45, "DTX": 0.55, "IMM": 0.50,
                    "MITO": 0.60, "SKN": 0.50, "STR": 0.35, "HRM": 0.50, "GA": 0.45}
        else:  # Obesity III
            return {"CM": 0.80, "COG": 0.50, "DTX": 0.60, "IMM": 0.60,
                    "MITO": 0.70, "SKN": 0.60, "STR": 0.35, "HRM": 0.50, "GA": 0.50}
