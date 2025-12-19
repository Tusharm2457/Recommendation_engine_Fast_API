"""
Physical Activity Ruleset

Calculates focus area scores based on exercise days per week (0-7).

Activity Categories:
- Sedentary: 0 days
- Insufficiently active: 1-2 days
- Adequate: 3-4 days
- Optimal: 5-7 days

Evidence-based scoring from:
- CDC Physical Activity Guidelines
- Health.gov recommendations
- JOGH (gut motility and constipation)
- Insulin sensitivity and fitness research
- Sleep/mood/attention benefits

Key Mechanisms:
- Cardiometabolic: insulin sensitivity, cardiovascular fitness
- Mitochondrial: energy metabolism, oxidative capacity
- Stress-axis: stress reactivity, cortisol regulation
- Gut: motility, transit time, constipation
- Cognitive: sleep quality, mood, attention (optimal frequency)
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class PhysicalActivityRuleset:
    """Ruleset for physical activity scoring based on exercise frequency."""
    
    def get_physical_activity_weights(
        self,
        exercise_days_per_week: Optional[int],
        digestive_symptoms: Optional[str] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on exercise frequency.
        
        Args:
            exercise_days_per_week: Number of exercise days per week (0-7)
            digestive_symptoms: Comma-separated digestive symptoms
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no data provided, return zeros
        if exercise_days_per_week is None:
            return (scores, "")
        
        # Validate and clamp to 0-7 range
        days = max(0, min(7, round(exercise_days_per_week)))
        
        # Detect constipation from digestive symptoms
        has_constipation = self._has_constipation(digestive_symptoms)
        
        # Apply scoring based on activity level
        if days == 0:
            # Sedentary
            scores["CM"] = 0.35
            scores["MITO"] = 0.35
            scores["STR"] = 0.25
            scores["GA"] = 0.15
            
            # SME GI add-on for constipation
            if has_constipation:
                scores["GA"] += 0.05  # Total GA capped at 0.20
            
            category = "sedentary"
        
        elif days in [1, 2]:
            # Insufficiently active
            scores["CM"] = 0.15
            scores["MITO"] = 0.15
            scores["STR"] = 0.10
            scores["GA"] = 0.05
            category = "insufficient"
        
        elif days in [3, 4]:
            # Adequate
            scores["CM"] = -0.15
            scores["MITO"] = -0.15
            scores["STR"] = -0.10
            scores["GA"] = -0.05
            category = "adequate"
        
        else:  # 5-7
            # Optimal
            scores["CM"] = -0.25
            scores["MITO"] = -0.25
            scores["STR"] = -0.15
            scores["GA"] = -0.10
            scores["COG"] = -0.05
            category = "optimal"
        
        # Create description
        description = self._create_description(days, category, has_constipation)
        
        return (scores, description)
    
    def _has_constipation(self, digestive_symptoms: Optional[str]) -> bool:
        """
        Detect constipation from digestive symptoms.
        
        Returns:
            True if constipation detected, False otherwise
        """
        if not digestive_symptoms:
            return False
        
        symptoms_lower = digestive_symptoms.lower()
        return "constipation" in symptoms_lower or "constipated" in symptoms_lower
    
    def _create_description(
        self,
        days: int,
        category: str,
        has_constipation: bool
    ) -> str:
        """Create human-readable description for reasons file."""
        # Base description
        description = f"{days} days/wk ({category})"
        
        # Add constipation note for sedentary
        if days == 0 and has_constipation:
            description += ", constipation"
        
        return description

