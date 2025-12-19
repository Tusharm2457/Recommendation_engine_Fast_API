"""
Digestive Symptoms focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple
from .constants import FOCUS_AREAS


class DigestiveSymptomRuleset:
    """Ruleset for digestive symptoms focus area scoring."""
    
    # Symptom weights mapping (symptom_name -> {focus_area: weight})
    SYMPTOM_WEIGHTS = {
        'bloating': {
            'GA': 0.35,
            'IMM': 0.15,
            'DTX': 0.10,
            'STR': 0.05,
            'MITO': 0.05
        },
        'constipation': {
            'GA': 0.35,
            'IMM': 0.05,
            'DTX': 0.15,
            'CM': 0.10
        },
        'diarrhea': {
            'GA': 0.35,
            'IMM': 0.20,
            'DTX': 0.10,
            'MITO': 0.05
        },
        'heartburn': {
            'GA': 0.30,
            'IMM': 0.10,
            'DTX': 0.05,
            'STR': 0.05
        },
        'abdominal_pain': {
            'GA': 0.30,
            'IMM': 0.15,
            'STR': 0.10,
            'MITO': 0.05
        },
        'nausea': {
            'GA': 0.25,
            'DTX': 0.05,
            'STR': 0.05,
            'MITO': 0.10
        },
        'flatulence': {
            'GA': 0.20,
            'IMM': 0.05,
            'DTX': 0.10
        },
        'stomach_rumbles': {
            'GA': 0.15,
            'DTX': 0.05,
            'STR': 0.05
        },
        'borborygmus': {  # Alias for stomach_rumbles
            'GA': 0.15,
            'DTX': 0.05,
            'STR': 0.05
        }
    }
    
    def get_digestive_symptom_weights(
        self,
        digestive_symptoms: Optional[str] = None
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on digestive symptoms.

        Args:
            digestive_symptoms: Comma-separated string of digestive symptoms
                               (e.g., "bloating,constipation,diarrhea")

        Returns:
            Tuple of (total_scores dict, per_symptom_breakdown dict)
            - total_scores: Combined scores across all symptoms
            - per_symptom_breakdown: Dict mapping symptom name to its individual scores
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        per_symptom_breakdown = {}

        if not digestive_symptoms:
            return (scores, per_symptom_breakdown)

        # Parse symptoms from comma-separated string
        symptoms_list = [s.strip().lower().replace(' ', '_') for s in digestive_symptoms.split(',')]

        # Remove empty strings
        symptoms_list = [s for s in symptoms_list if s]

        if not symptoms_list:
            return (scores, per_symptom_breakdown)

        # Track which symptoms were found
        found_symptoms = []

        # Apply weights for each symptom
        for symptom in symptoms_list:
            if symptom in self.SYMPTOM_WEIGHTS:
                found_symptoms.append(symptom)
                symptom_scores = self.SYMPTOM_WEIGHTS[symptom]

                # Add to total scores
                for focus_area, weight in symptom_scores.items():
                    scores[focus_area] += weight

                # Store individual symptom scores for tracking
                symptom_display = symptom.replace('_', ' ').title()
                per_symptom_breakdown[symptom_display] = {code: 0.0 for code in FOCUS_AREAS}
                for focus_area, weight in symptom_scores.items():
                    per_symptom_breakdown[symptom_display][focus_area] = weight

        # 4) Multi-symptom clustering bonus
        num_symptoms = len(found_symptoms)

        if num_symptoms >= 3 and num_symptoms <= 4:
            scores["GA"] += 0.15
            scores["IMM"] += 0.05
            # Add clustering bonus as a separate entry
            clustering_scores = {code: 0.0 for code in FOCUS_AREAS}
            clustering_scores["GA"] = 0.15
            clustering_scores["IMM"] = 0.05
            per_symptom_breakdown["Multi-symptom clustering (3-4 symptoms)"] = clustering_scores
        elif num_symptoms >= 5:
            scores["GA"] += 0.20
            scores["IMM"] += 0.10
            scores["DTX"] += 0.05
            # Add clustering bonus as a separate entry
            clustering_scores = {code: 0.0 for code in FOCUS_AREAS}
            clustering_scores["GA"] = 0.20
            clustering_scores["IMM"] = 0.10
            clustering_scores["DTX"] = 0.05
            per_symptom_breakdown["Multi-symptom clustering (≥5 symptoms)"] = clustering_scores

        return (scores, per_symptom_breakdown)

