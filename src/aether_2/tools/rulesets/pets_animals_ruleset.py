"""
Pets/Animals focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple
from .constants import FOCUS_AREAS


class PetsAnimalsRuleset:
    """Ruleset for pets/animals focus area scoring."""
    
    def get_pets_animals_weights(
        self,
        has_pets: Optional[bool] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on pet ownership.
        
        Args:
            has_pets: Boolean indicating if user has pets
            
        Returns:
            Tuple of (scores dict, description string)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        description = ""
        
        # A) If No
        if not has_pets:
            return (scores, description)
        
        # B) If Yes - Base (applies regardless of animal type)
        scores["IMM"] += 0.15
        scores["SKN"] += 0.10
        scores["GA"] += 0.10
        description = "Has pets (antigen exposure, microbiota shifts)"
        
        return (scores, description)

