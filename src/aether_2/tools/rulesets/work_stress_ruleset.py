"""
Work and Stress Ruleset

Calculates focus area scores based on:
1. Work stress level (1-10 scale)
2. Shift work detection from job title
3. Shift work tenure (≥3 years)
4. Sleep quality interactions
5. Skin condition stress flares

Stress Categories:
- Low: 1-3
- Moderate: 4-7
- High: 8-10

Shift Work Occupations:
- Healthcare: nurse, physician/ED, EMT, resident
- Emergency services: security, police, firefighter
- Hospitality: hotel, restaurant, chef
- Industrial: factory/plant, warehouse, logistics, driver
- Aviation: airline crew
- Support: customer support/call center, BPO
- Other: media, maintenance, utilities, mining, oil/gas
- Keywords: "night", "rotating", "graveyard"

Evidence-based scoring from:
- Psychoneuroimmunology (stress-immune dysregulation)
- Brain-gut axis (IBS/FD in shift workers)
- Circadian misalignment (cardiometabolic risk)
- Cognitive fatigue (working memory impact)
- Mitochondrial stress (energy load)
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class WorkStressRuleset:
    """Ruleset for work stress and shift work scoring."""

    def get_work_stress_weights(
        self,
        work_stress_level: Optional[int],
        shift_work: bool = False,
        has_poor_sleep: bool = False,
        has_skin_conditions: bool = False
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on work stress and shift work.

        Args:
            work_stress_level: Stress level 1-10
            shift_work: Whether user does shift work (detected from job title)
            has_poor_sleep: Whether user has poor sleep quality
            has_skin_conditions: Whether user has stress-reactive skin conditions

        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # If no stress level provided, return zeros
        if work_stress_level is None:
            return (scores, "")

        # Validate stress level
        if work_stress_level < 1 or work_stress_level > 10:
            return (scores, "")
        
        # Detect shift tenure (≥3 years) - would need additional data, defaulting to False for now
        shift_tenure_long = False  # TODO: Add shift tenure detection if data available

        # Categorize stress level
        if work_stress_level <= 3:
            stress_category = "low"
        elif work_stress_level <= 7:
            stress_category = "moderate"
        else:  # 8-10
            stress_category = "high"

        # Apply base stress scoring
        if stress_category == "low" and not shift_work:
            # Step A: Low stress, no shift work
            scores["STR"] = 0.05
            if has_poor_sleep:
                scores["COG"] = 0.05

        elif stress_category == "moderate" and not shift_work:
            # Step B: Moderate stress, no shift work
            scores["STR"] = 0.15
            scores["COG"] = 0.10
            scores["MITO"] = 0.10
            scores["CM"] = 0.10
            scores["IMM"] = 0.10
            scores["GA"] = 0.10

        elif stress_category == "high" and not shift_work:
            # Step C: High stress, no shift work
            scores["STR"] = 0.40
            scores["COG"] = 0.20
            scores["CM"] = 0.20
            scores["GA"] = 0.30
            scores["IMM"] = 0.20
            scores["MITO"] = 0.15

        # Step D: Add shift work overlay
        if shift_work:
            # Base shift work adds
            scores["STR"] += 0.20
            scores["CM"] += 0.10
            scores["IMM"] += 0.10
            scores["COG"] += 0.10

            # GI overlay
            if work_stress_level >= 8 or shift_work:
                if shift_tenure_long:
                    scores["GA"] = max(scores["GA"], 0.50)  # Escalate to cap
                else:
                    scores["GA"] += 0.30

        # Step E: Compound risk (shift work + high stress)
        if shift_work and work_stress_level >= 8:
            # STR likely at cap, add if not
            if scores["STR"] < 0.60:
                scores["STR"] = min(0.60, scores["STR"] + 0.10)
            scores["CM"] += 0.10
            scores["IMM"] += 0.10

        # Step G: Skin stress flares
        if has_skin_conditions:
            scores["SKN"] = min(0.10, scores["SKN"] + 0.05)  # Cap at 0.10

        # Create description
        description = self._create_description(
            stress_category,
            shift_work,
            shift_tenure_long
        )

        return (scores, description)

    def _create_description(
        self,
        stress_category: str,
        shift_work: bool,
        shift_tenure_long: bool
    ) -> str:
        """Create human-readable description for reasons file."""
        # Base description
        description = f"Stress ({stress_category})"

        # Add shift work info
        if shift_work:
            if shift_tenure_long:
                description += ", shift work (≥3y)"
            else:
                description += ", shift work"

        return description

