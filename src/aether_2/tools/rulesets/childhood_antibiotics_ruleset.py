"""
Childhood Antibiotics Ruleset

Decision tree for childhood antibiotic exposure (adults ≥18).

Q: "Did you take any antibiotics as a child?"

A) If No → Add nothing; stop.

B) If Yes (childhood exposure, any time ≤18 y) → Baseline 'microbiome imprint' signal:
   - GA +0.25 (antibiotics perturb early-life gut development)
   - IMM +0.20 (antibiotics perturb early-life immune development)
   - SKN +0.05 (skin microbiome impact)

Rationale: Early-life antibiotic exposure can have lasting effects on microbiome 
composition and immune system development.
"""

from typing import Dict
from .constants import FOCUS_AREAS


class ChildhoodAntibioticsRuleset:
    """Ruleset for childhood antibiotic exposure scoring."""
    
    def get_childhood_antibiotics_weights(
        self,
        took_antibiotics_as_child: bool
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on childhood antibiotic exposure.
        
        Args:
            took_antibiotics_as_child: Boolean indicating if patient took antibiotics as a child
            
        Returns:
            Dictionary mapping focus area codes to weight scores
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no childhood antibiotics, return zero scores
        if not took_antibiotics_as_child:
            return scores
        
        # Baseline 'microbiome imprint' signal
        scores["GA"] = 0.25   # Gut development impact
        scores["IMM"] = 0.20  # Immune development impact
        scores["SKN"] = 0.05  # Skin microbiome impact
        
        return scores

