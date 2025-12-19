"""
Height-based focus area scoring ruleset.
"""

from typing import Dict, Optional
from .constants import FOCUS_AREAS


class HeightRuleset:
    """Ruleset for height-based focus area scoring."""

    def get_height_weights(self, height_in: Optional[int]) -> Dict[str, float]:
        """
        Calculate focus area weights based on height.

        Args:
            height_in: Height in inches

        Returns:
            Dictionary of focus area scores
        """
        if height_in is None:
            return {code: 0.0 for code in FOCUS_AREAS}

        if height_in <= 60:  # Very short
            return {"CM": 0.30, "COG": 0.15, "DTX": 0.15, "IMM": 0.15,
                    "MITO": 0.20, "SKN": 0.10, "STR": 0.15, "HRM": 0.15, "GA": 0.15}
        elif 61 <= height_in <= 64:  # Short
            return {"CM": 0.25, "COG": 0.15, "DTX": 0.15, "IMM": 0.15,
                    "MITO": 0.15, "SKN": 0.10, "STR": 0.15, "HRM": 0.15, "GA": 0.10}
        elif 65 <= height_in <= 75:  # Average
            return {"CM": 0.15, "COG": 0.10, "DTX": 0.10, "IMM": 0.10,
                    "MITO": 0.10, "SKN": 0.10, "STR": 0.10, "HRM": 0.10, "GA": 0.10}
        elif 76 <= height_in <= 77:  # Tall
            return {"CM": 0.25, "COG": 0.10, "DTX": 0.10, "IMM": 0.10,
                    "MITO": 0.15, "SKN": 0.10, "STR": 0.10, "HRM": 0.10, "GA": 0.10}
        else:  # Very tall ≥78
            return {"CM": 0.30, "COG": 0.10, "DTX": 0.10, "IMM": 0.10,
                    "MITO": 0.20, "SKN": 0.10, "STR": 0.10, "HRM": 0.10, "GA": 0.10}
