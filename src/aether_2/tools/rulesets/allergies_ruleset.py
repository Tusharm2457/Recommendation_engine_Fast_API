"""
Allergies-based focus area scoring ruleset.
"""

from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class AllergiesRuleset:
    """Ruleset for allergies-based focus area scoring."""
    
    def get_allergies_weights(
        self,
        has_allergies: bool,
        allergen_list: List[str],
        reaction_list: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on allergies.
        
        Args:
            has_allergies: Whether patient has allergies
            allergen_list: List of allergen names
            reaction_list: List of corresponding reactions
            
        Returns:
            Tuple of:
                - Cumulative scores dict (all allergens combined, clamped at 1.0)
                - Per-allergen breakdown dict {allergen_name: {focus_area: score}}
        """
        # Early exit if no allergies
        if not has_allergies or not allergen_list:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_allergen_breakdown = {}
        
        # Process each allergen
        for allergen_name, reaction in zip(allergen_list, reaction_list):
            allergen_scores = self._score_single_allergen(allergen_name, reaction)
            
            # Add to cumulative
            for code in FOCUS_AREAS:
                cumulative_scores[code] += allergen_scores[code]
            
            # Store per-allergen breakdown
            per_allergen_breakdown[allergen_name] = allergen_scores
        
        # Clamp each focus area at 1.0
        for code in FOCUS_AREAS:
            cumulative_scores[code] = min(cumulative_scores[code], 1.0)
        
        return (cumulative_scores, per_allergen_breakdown)
    
    def _score_single_allergen(self, allergen_name: str, reaction: str) -> Dict[str, float]:
        """Score a single allergen based on type and severity."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Classify allergen type
        allergen_type = self._classify_allergen(allergen_name, reaction)
        
        # Detect severity modifiers
        severity = self._detect_severity_modifiers(reaction)
        
        # Apply base weights by allergen type
        if allergen_type == "food":
            scores["GA"] += 0.40  # Mucosal immune reactivity
            scores["STR"] += 0.05  # Food-related vigilance
            scores["IMM"] += 0.45  # Immediate-type allergy
            scores["SKN"] += 0.20  # Histamine-mediated
            
        elif allergen_type == "drug":
            scores["DTX"] += 0.25  # Med-safety & alternatives burden
            scores["IMM"] += 0.15
            
        elif allergen_type == "nsaid":
            scores["DTX"] += 0.20
            scores["IMM"] += 0.15
            
        elif allergen_type == "latex":
            scores["SKN"] += 0.30
            scores["IMM"] += 0.20
            # Check for latex-fruit syndrome
            if self._has_latex_fruit_syndrome(allergen_name, reaction):
                scores["GA"] += 0.10
            
        elif allergen_type == "venom":
            scores["IMM"] += 0.30
            scores["STR"] += 0.10  # Risk awareness/anxiety
            
        elif allergen_type == "alpha-gal":
            scores["IMM"] += 0.50
            scores["GA"] += 0.40
            scores["DTX"] += 0.10
            
        elif allergen_type == "environmental":
            scores["IMM"] += 0.25
            scores["SKN"] += 0.20
            scores["STR"] += 0.10  # Sleep/cognitive load from rhinitis
            
        elif allergen_type == "oral-allergy":
            scores["IMM"] += 0.20
            scores["GA"] += 0.20
            scores["SKN"] += 0.10
            
        else:  # Unknown - apply generic immediate-type allergy weights
            scores["IMM"] += 0.45
            scores["SKN"] += 0.20
        
        # Apply severity modifiers
        if severity["anaphylaxis"]:
            scores["IMM"] += 0.30
            scores["STR"] += 0.10
            scores["COG"] += 0.05  # Fear/avoidance
            
        if severity["epipen"]:
            scores["IMM"] += 0.05

        return scores

    def _classify_allergen(self, allergen_name: str, reaction: str) -> str:
        """
        Classify allergen into type category.

        Returns: 'food', 'drug', 'environmental', 'latex', 'venom',
                 'alpha-gal', 'oral-allergy', 'nsaid', 'unknown'
        """
        allergen_lower = allergen_name.lower()
        reaction_lower = reaction.lower()

        # Food allergens
        food_keywords = [
            "nuts", "peanut", "tree nut", "almond", "cashew", "walnut",
            "dairy", "milk", "cheese", "lactose",
            "egg", "gluten", "wheat", "soy", "fish", "shellfish",
            "shrimp", "crab", "lobster", "sesame", "corn", "gelatin"
        ]
        if any(kw in allergen_lower for kw in food_keywords):
            return "food"

        # NSAID (check before general drug)
        nsaid_keywords = ["aspirin", "ibuprofen", "naproxen", "nsaid", "advil", "motrin", "aleve"]
        if any(kw in allergen_lower or kw in reaction_lower for kw in nsaid_keywords):
            return "nsaid"

        # Drug allergens
        drug_keywords = [
            "penicillin", "sulfa", "antibiotic", "medication", "medicine",
            "amoxicillin", "cephalosporin", "contrast", "iodine"
        ]
        if any(kw in allergen_lower or kw in reaction_lower for kw in drug_keywords):
            return "drug"

        # Latex
        if "latex" in allergen_lower or "rubber" in allergen_lower:
            return "latex"

        # Venom
        venom_keywords = ["bee", "wasp", "hornet", "venom", "sting", "yellow jacket"]
        if any(kw in allergen_lower for kw in venom_keywords):
            return "venom"

        # Alpha-gal
        if "alpha" in allergen_lower or "red meat" in allergen_lower or "mammal" in allergen_lower:
            return "alpha-gal"

        # Oral allergy syndrome
        oas_keywords = [
            "apple", "cherry", "peach", "pear", "plum", "apricot",
            "carrot", "celery", "parsley", "hazelnut", "almond"
        ]
        if any(kw in allergen_lower for kw in oas_keywords):
            return "oral-allergy"

        # Environmental
        env_keywords = [
            "pollen", "mite", "mold", "dander", "dust", "pet",
            "grass", "tree", "ragweed", "cat", "dog", "animal"
        ]
        if any(kw in allergen_lower or kw in reaction_lower for kw in env_keywords):
            return "environmental"

        return "unknown"

    def _detect_severity_modifiers(self, reaction: str) -> Dict[str, bool]:
        """Check reaction text for severity indicators."""
        reaction_lower = reaction.lower()

        return {
            "anaphylaxis": "anaphylaxis" in reaction_lower or "anaphylactic" in reaction_lower,
            "epipen": "epipen" in reaction_lower or "epinephrine" in reaction_lower or "epi-pen" in reaction_lower,
            "severe_swelling": "swelling" in reaction_lower or "angioedema" in reaction_lower,
            "hives": "hives" in reaction_lower or "urticaria" in reaction_lower
        }

    def _has_latex_fruit_syndrome(self, allergen_name: str, reaction: str) -> bool:
        """Check for latex-fruit cross-reactivity."""
        combined = (allergen_name + " " + reaction).lower()
        latex_fruit_keywords = ["banana", "avocado", "kiwi", "papaya", "chestnut", "fig"]
        return any(kw in combined for kw in latex_fruit_keywords)

