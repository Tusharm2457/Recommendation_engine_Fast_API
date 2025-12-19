"""
Consistent Sleep Schedule Ruleset (Phase 3)

Field: "Do you go to sleep around the same time every day?"
Answer: Yes / No

Scope: Age >= 18 years only
"""

from typing import Dict, Any


class ConsistentSleepScheduleRuleset:
    """Ruleset for evaluating consistent sleep schedule impact on focus areas."""

    # Per-domain caps
    CAPS = {
        "STR": 0.30,
        "COG": 0.20,
        "GA": 0.20,
        "CM": 0.15,
    }

    def get_consistent_sleep_schedule_weights(
        self,
        sleep_schedule_data: Any,
        age: int = None,
        shift_work_flag: bool = False,
        alcohol_frequency: str = None,
        metabolic_flags: bool = False
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on sleep schedule consistency.

        Args:
            sleep_schedule_data: "Yes" or "No"
            age: Patient age (must be >= 18)
            shift_work_flag: Whether patient does shift work (from Phase 2)
            alcohol_frequency: Alcohol frequency from Phase 2 ("daily", "weekly", etc.)
            metabolic_flags: Whether patient has metabolic flags (high stress-glycemia, low activity)

        Returns:
            Dict mapping focus area codes to weight adjustments
        """
        scores = {
            "CM": 0.0,
            "COG": 0.0,
            "DTX": 0.0,
            "IMM": 0.0,
            "MITO": 0.0,
            "SKN": 0.0,
            "STR": 0.0,
            "HRM": 0.0,
            "GA": 0.0,
        }

        # Age gating: only score if age >= 18
        if age is not None and age < 18:
            return scores

        # Parse answer
        answer = str(sleep_schedule_data).strip().lower()
        is_consistent = answer in ["yes", "y", "true"]

        # A. Consistent sleep schedule (Yes)
        if is_consistent:
            scores["STR"] -= 0.15  # Aligned cortisol curve
            scores["COG"] -= 0.10  # Better attention/mood stability
            scores["CM"] -= 0.05   # Healthier metabolic signals
            scores["GA"] -= 0.05   # Clock-motility synchrony

        # B. Irregular sleep schedule (No)
        else:
            scores["STR"] += 0.30  # Hyper-arousal/circadian stress
            scores["COG"] += 0.20  # Poorer mental health/cognitive symptoms
            scores["GA"] += 0.20   # Circadian-enteric misalignment

            # Cross-field synergies (only apply if irregular)
            # 1. Shift work
            if shift_work_flag:
                scores["STR"] += 0.10  # Circadian strain

            # 2. Alcohol frequency (daily/weekly)
            if alcohol_frequency:
                freq_lower = alcohol_frequency.lower()
                if "daily" in freq_lower or "weekly" in freq_lower or "week" in freq_lower:
                    scores["GA"] += 0.10  # Nocturnal reflux risk

            # 3. Metabolic flags
            if metabolic_flags:
                scores["CM"] += 0.10  # Regularity-CM links

        # Apply per-domain caps
        for domain, cap in self.CAPS.items():
            if scores[domain] > cap:
                scores[domain] = cap
            elif scores[domain] < -cap:
                scores[domain] = -cap

        return scores

