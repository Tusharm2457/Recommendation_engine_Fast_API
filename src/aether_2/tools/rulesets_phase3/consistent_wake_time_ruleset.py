"""
Consistent Wake Time Ruleset for Phase 3 Focus Area Evaluation

Field: "Do you wake up around the same time every day?"
Answer: Yes / No

Scoring Logic:
- If "No" (irregular wake time):
  - STR +0.30 (HPA/cortisol awakening response instability)
  - COG +0.15 (greater mood/cognitive symptoms)
  - GA +0.20 (circadian-enteric misalignment)
  - Escalators:
    - Shift work → STR +0.10, GA +0.05, CM +0.10
    - Alcohol daily/weekly → GA +0.10
    - Social jetlag → STR +0.05
    - Short sleep (<6h) → STR +0.05, CM +0.05

- If "Yes" (consistent wake time):
  - STR -0.15 (steadier HPA tone)
  - COG -0.05 (better cognition)
  - GA -0.05 (better gut motility)
  - If shift work → halve shift work escalators

Age gating: Only score if age >= 18
"""

from typing import Dict, Any


class ConsistentWakeTimeRuleset:
    """Ruleset for evaluating consistent wake time impact on focus areas."""

    # Per-domain caps
    CAPS = {
        "STR": 0.40,
        "COG": 0.30,
        "GA": 0.30,
        "CM": 0.20,
    }

    # Protective caps (negative scores)
    PROTECTIVE_CAPS = {
        "STR": -0.20,
        "COG": -0.20,
        "GA": -0.20,
        "CM": -0.20,
    }

    def get_consistent_wake_time_weights(
        self,
        wake_time_data: Any,
        age: int = None,
        shift_work_flag: bool = False,
        alcohol_frequency: str = None,
        social_jetlag_flag: bool = False,
        short_sleep_flag: bool = False
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on wake time consistency.

        Args:
            wake_time_data: "Yes" or "No"
            age: Patient age (must be >= 18)
            shift_work_flag: Whether patient does shift work (from Phase 2)
            alcohol_frequency: Alcohol frequency from Phase 2 ("daily", "weekly", etc.)
            social_jetlag_flag: Whether patient has social jetlag (big weekday-weekend swings)
            short_sleep_flag: Whether patient sleeps <6 hours (from Phase 2)

        Returns:
            Dict mapping focus area codes to weight adjustments
        """
        weights = {
            "STR": 0.0,
            "COG": 0.0,
            "GA": 0.0,
            "CM": 0.0,
        }

        # Age gating
        if age is None or age < 18:
            return weights

        # Parse answer
        if not wake_time_data:
            return weights

        answer = str(wake_time_data).strip().lower()

        # Branch A: Irregular wake time (No)
        if answer == "no":
            weights["STR"] += 0.30
            weights["COG"] += 0.15
            weights["GA"] += 0.20

            # Escalators
            if shift_work_flag:
                weights["STR"] += 0.10
                weights["GA"] += 0.05
                weights["CM"] += 0.10

            if alcohol_frequency and alcohol_frequency.lower() in ["daily", "weekly"]:
                weights["GA"] += 0.10

            if social_jetlag_flag:
                weights["STR"] += 0.05

            if short_sleep_flag:
                weights["STR"] += 0.05
                weights["CM"] += 0.05

        # Branch B: Consistent wake time (Yes)
        elif answer == "yes":
            weights["STR"] -= 0.15
            weights["COG"] -= 0.05
            weights["GA"] -= 0.05

            # If shift work but maintains fixed wake time, halve shift work escalators
            # (This would be applied in the sleep schedule ruleset, not here)

        # Apply caps
        for code in weights:
            if weights[code] > 0:
                weights[code] = min(weights[code], self.CAPS.get(code, 0.0))
            else:
                weights[code] = max(weights[code], self.PROTECTIVE_CAPS.get(code, 0.0))

        return weights

