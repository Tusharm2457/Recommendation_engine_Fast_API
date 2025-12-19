"""
Ruleset for Field 22: Relaxation Techniques

Evaluates which relaxation techniques the patient uses and applies stress-axis
reductions with domain spillovers.

Decision tree:
1. If "None" selected → STR +0.15, GA +0.10 (absence of stress-mitigating practice)
2. For each modality present, apply STR reduction + domain spillovers
3. Stacking synergy: If ≥2 modalities → multiply net STR reduction by 1.15 (cap at -0.40)

Base weights (reductions):
- Meditation: STR -0.12, COG -0.08, IMM -0.05, GA -0.08
- Breathing: STR -0.12, GA -0.12, CM -0.04
- Yoga: STR -0.12, GA -0.12, CM -0.06, MITO -0.05
- Tai Chi/Qigong: STR -0.10, CM -0.05, COG -0.05, MITO -0.05
- Prayer: STR -0.05, CM -0.03, COG -0.03
- Other (unmapped): STR -0.10, COG -0.04
"""

from typing import Any, Dict, List, Tuple


class RelaxationTechniquesRuleset:
    """Ruleset for evaluating relaxation techniques."""

    # Base weights for each modality (negative = reduction)
    MODALITY_WEIGHTS = {
        "meditation": {
            "STR": -0.12,
            "COG": -0.08,
            "IMM": -0.05,
            "GA": -0.08
        },
        "breathing": {
            "STR": -0.12,
            "GA": -0.12,
            "CM": -0.04
        },
        "yoga": {
            "STR": -0.12,
            "GA": -0.12,
            "CM": -0.06,
            "MITO": -0.05
        },
        "tai chi": {
            "STR": -0.10,
            "CM": -0.05,
            "COG": -0.05,
            "MITO": -0.05
        },
        "qigong": {
            "STR": -0.10,
            "CM": -0.05,
            "COG": -0.05,
            "MITO": -0.05
        },
        "prayer": {
            "STR": -0.05,
            "CM": -0.03,
            "COG": -0.03
        },
        "other": {
            "STR": -0.10,
            "COG": -0.04
        }
    }

    # STR cap for reductions
    STR_CAP = -0.40

    # Stacking synergy multiplier (≥2 modalities)
    STACKING_MULTIPLIER = 1.15

    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip whitespace."""
        if not text:
            return ""
        return text.lower().strip()

    def _detect_modalities(self, relaxation_data: str) -> List[str]:
        """
        Detect which relaxation modalities are present using substring matching.
        
        Returns list of detected modalities (normalized keys).
        """
        if not relaxation_data:
            return []
        
        normalized = self._normalize_text(relaxation_data)
        
        # Check for "None" first
        if normalized == "none" or normalized == "":
            return ["none"]
        
        modalities = []
        
        # Substring matching for each modality
        if "meditation" in normalized:
            modalities.append("meditation")
        if "breathing" in normalized:
            modalities.append("breathing")
        if "yoga" in normalized:
            modalities.append("yoga")
        if "tai chi" in normalized or "taichi" in normalized:
            modalities.append("tai chi")
        if "qigong" in normalized or "qi gong" in normalized:
            modalities.append("qigong")
        if "prayer" in normalized:
            modalities.append("prayer")
        if "other" in normalized:
            modalities.append("other")
        
        return modalities

    def get_relaxation_techniques_weights(
        self,
        relaxation_data: Any
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on relaxation techniques.
        
        Args:
            relaxation_data: Relaxation techniques data (string with comma/semicolon separated values)
        
        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []
        
        # Convert to string
        if relaxation_data is None:
            relaxation_data = ""
        text = str(relaxation_data).strip()
        
        # Detect modalities
        modalities = self._detect_modalities(text)
        
        # Shortcut: If "None" selected
        if "none" in modalities or len(modalities) == 0:
            weights["STR"] = weights.get("STR", 0) + 0.15
            weights["GA"] = weights.get("GA", 0) + 0.10
            return weights, flags
        
        # Apply base weights for each modality
        for modality in modalities:
            modality_weights = self.MODALITY_WEIGHTS.get(modality, {})
            for domain, weight in modality_weights.items():
                weights[domain] = weights.get(domain, 0) + weight
        
        # Stacking synergy: If ≥2 modalities, multiply net STR reduction by 1.15
        if len(modalities) >= 2 and "STR" in weights:
            weights["STR"] = weights["STR"] * self.STACKING_MULTIPLIER
            # Apply STR cap
            if weights["STR"] < self.STR_CAP:
                weights["STR"] = self.STR_CAP
        
        return weights, flags

