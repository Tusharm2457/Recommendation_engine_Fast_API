"""
Current Stress Ruleset (Field 20): "On a scale of 1-10, how high is your current stress?"

Linear scaling with piecewise spillover weights for secondary focus areas.
"""

from typing import Dict, List, Tuple, Any


class CurrentStressRuleset:
    """
    Evaluates current stress level (1-10 scale) and returns focus area weights.
    
    Primary weight:
    - STR: Linear scaling 0.08 × (s - 1), ranges 0.00 to 0.72
    
    Secondary spillover weights (piecewise):
    - Low stress (1-3): No spillover
    - Moderate stress (4-7): Linear spillover to COG, CM, GA, MITO; threshold at 7 for IMM/HRM
    - High stress (8-10): Additional boosts to COG, CM, GA, IMM, HRM
    
    Cross-field synergies:
    - Sleep <6h or irregular + stress ≥7 → STR +0.10, COG +0.10
    - Shift work or work stress ≥8 → GA +0.10
    """
    
    def __init__(self):
        pass
    
    def _validate_stress_score(self, stress_data: Any) -> Tuple[int, List[str]]:
        """
        Validate and normalize stress score to integer 1-10.
        
        Returns:
            Tuple of (validated score, warnings list)
        """
        warnings = []
        
        # Handle None, empty, or non-numeric
        if stress_data is None or stress_data == "" or stress_data in ["None", "N/A", "NA"]:
            warnings.append("VALIDATION: Stress score is blank - cannot score")
            return None, warnings
        
        # Convert to integer
        try:
            score = int(float(str(stress_data).strip()))
        except (ValueError, TypeError):
            warnings.append(f"VALIDATION: Stress score '{stress_data}' is non-numeric - cannot score")
            return None, warnings
        
        # Clamp to 1-10 range
        if score < 1:
            warnings.append(f"VALIDATION: Stress score {score} < 1, clamped to 1")
            score = 1
        elif score > 10:
            warnings.append(f"VALIDATION: Stress score {score} > 10, clamped to 10")
            score = 10
        
        return score, warnings
    
    def get_current_stress_weights(
        self,
        stress_data: Any,
        age: int = None,
        sleep_hours: float = None,
        sleep_irregular: bool = False,
        shift_work: bool = False,
        work_stress_level: int = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on current stress level (1-10).
        
        Args:
            stress_data: Stress score (1-10 integer)
            age: Patient age (must be ≥18)
            sleep_hours: Hours of sleep per night (for cross-field synergy)
            sleep_irregular: Whether sleep schedule is irregular (for cross-field synergy)
            shift_work: Whether patient does shift work (for cross-field synergy)
            work_stress_level: Work stress level from Phase 2 (for cross-field synergy)
        
        Returns:
            Tuple of (weights dict, flags/warnings list)
        """
        weights = {}
        flags = []
        
        # Adults only (age ≥18)
        if age is not None and age < 18:
            flags.append("VALIDATION: Age < 18, stress scoring not applicable")
            return weights, flags
        
        # Validate stress score
        s, warnings = self._validate_stress_score(stress_data)
        flags.extend(warnings)
        
        if s is None:
            return weights, flags
        
        # 1) Primary STR weight (linear, monotonic)
        # w_STR = 0.08 × (s - 1), ranges 0.00 (at s=1) to 0.72 (at s=10)
        weights["STR"] = 0.08 * (s - 1)
        
        # 2) Secondary spillover weights (piecewise)
        
        if s <= 3:
            # Low stress: no spillover
            pass
        
        elif 4 <= s <= 7:
            # Moderate stress: linear spillover
            weights["COG"] = weights.get("COG", 0) + 0.03 * (s - 4)
            weights["CM"] = weights.get("CM", 0) + 0.025 * (s - 4)
            weights["GA"] = weights.get("GA", 0) + 0.02 * (s - 4)
            weights["MITO"] = weights.get("MITO", 0) + 0.015 * (s - 4)
            
            # Threshold at s=7 for IMM/HRM
            if s >= 7:
                weights["IMM"] = weights.get("IMM", 0) + 0.02 * (s - 6)
                weights["HRM"] = weights.get("HRM", 0) + 0.02 * (s - 6)
        
        else:  # s >= 8
            # High stress: moderate spillover + additional boosts
            weights["COG"] = weights.get("COG", 0) + 0.03 * (s - 4) + 0.10
            weights["CM"] = weights.get("CM", 0) + 0.025 * (s - 4) + 0.10
            weights["GA"] = weights.get("GA", 0) + 0.02 * (s - 4) + 0.15
            weights["IMM"] = weights.get("IMM", 0) + 0.02 * (s - 6) + 0.10
            weights["HRM"] = weights.get("HRM", 0) + 0.02 * (s - 6) + 0.10
            weights["MITO"] = weights.get("MITO", 0) + 0.015 * (s - 4)
        
        # 3) Cross-field synergies
        
        # Sleep <6h or irregular + stress ≥7 → STR +0.10, COG +0.10
        sleep_short_or_irregular = (sleep_hours is not None and sleep_hours < 6) or sleep_irregular
        if sleep_short_or_irregular and s >= 7:
            weights["STR"] = weights.get("STR", 0) + 0.10
            weights["COG"] = weights.get("COG", 0) + 0.10
        
        # Shift work or work stress ≥8 → GA +0.10
        high_work_stress = work_stress_level is not None and work_stress_level >= 8
        if shift_work or high_work_stress:
            weights["GA"] = weights.get("GA", 0) + 0.10
        
        # Remove zero scores
        weights = {k: v for k, v in weights.items() if v != 0}
        
        return weights, flags

