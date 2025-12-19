"""
Sex-based focus area scoring ruleset.
"""

from typing import Dict, Optional
from .constants import FOCUS_AREAS


class SexRuleset:
    """Ruleset for biological sex-based focus area scoring."""

    def get_sex_weights(self, sex: Optional[str]) -> Dict[str, float]:
        """
        Calculate focus area weights based on biological sex.

        Args:
            sex: Biological sex (female/male/other)

        Returns:
            Dictionary of focus area scores
        """
        if sex is None:
            return {code: 0.0 for code in FOCUS_AREAS}

        sex_lower = sex.lower()

        if sex_lower == "female":
            # Higher IBS prevalence, stronger HPA reactivity, sex-biased immune patterns,
            # dominant estrogen/progesterone axis
            return {"CM": 0.20, "COG": 0.20, "DTX": 0.20, "IMM": 0.25,
                    "MITO": 0.20, "SKN": 0.20, "STR": 0.25, "HRM": 0.35, "GA": 0.25}
        elif sex_lower == "male":
            # Earlier cardiovascular risk timing, androgen pathway (DHEA-S) generally higher
            return {"CM": 0.25, "COG": 0.20, "DTX": 0.20, "IMM": 0.20,
                    "MITO": 0.20, "SKN": 0.20, "STR": 0.20, "HRM": 0.30, "GA": 0.20}
        else:
            # Other/Intersex/Prefer to self-describe - heterogeneous physiology, minority-stress burden
            return {"CM": 0.22, "COG": 0.22, "DTX": 0.22, "IMM": 0.22,
                    "MITO": 0.22, "SKN": 0.20, "STR": 0.30, "HRM": 0.35, "GA": 0.22}
