"""
Dietary Habits focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple, List
from .constants import FOCUS_AREAS


class DietaryHabitsRuleset:
    """Ruleset for dietary habits focus area scoring."""
    
    def get_dietary_habits_weights(
        self,
        diet_style: Optional[str],
        diet_style_other: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        biological_sex: Optional[str] = None,
        supplements: Optional[str] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on dietary habits.
        
        Args:
            diet_style: Comma-separated diet styles (e.g., "vegetarian,gluten_free")
            diet_style_other: Free-text diet style if "other" is selected
            digestive_symptoms: Digestive symptoms string (for constipation, gas, bloating detection)
            biological_sex: Biological sex (for iron vigilance in vegetarian)
            supplements: Comma-separated supplements string (for B12, iodine detection)
            
        Returns:
            Tuple of (scores dict, list of diet descriptions)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        if not diet_style:
            return (scores, descriptions)
        
        # Parse diet styles (comma-separated)
        diet_styles = [style.strip().lower() for style in diet_style.split(',') if style.strip()]
        
        # Detect digestive symptoms
        has_constipation = False
        has_gas_bloating = False
        has_gi_improvement = False
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            has_constipation = 'constipation' in symptoms_lower or 'constipated' in symptoms_lower
            has_gas_bloating = 'gas' in symptoms_lower or 'bloating' in symptoms_lower
            # Assume improvement if explicitly mentioned (placeholder for future enhancement)
            has_gi_improvement = 'improve' in symptoms_lower or 'better' in symptoms_lower
        
        # Detect B12 supplementation
        has_b12_supplement = False
        if supplements:
            supplements_lower = supplements.lower()
            has_b12_supplement = 'b12' in supplements_lower or 'b-12' in supplements_lower or 'cobalamin' in supplements_lower
        
        # Process each diet style
        for diet in diet_styles:
            
            # 1) Low-Carb/Keto
            if diet == "low_carb_keto":
                scores["CM"] -= 0.25
                scores["MITO"] += 0.10
                # GA +0.20 if constipation (fiber <15g/day proxy)
                if has_constipation:
                    scores["GA"] += 0.20
                descriptions.append("Low-carb/keto")
            
            # 2) Carnivore
            elif diet == "carnivore":
                scores["GA"] += 0.30
                scores["CM"] += 0.25
                scores["DTX"] += 0.10
                descriptions.append("Carnivore")
            
            # 3) Vegan
            elif diet == "vegan":
                scores["CM"] -= 0.15
                # DTX +0.15 if no B12 supplement (≥12 mo assumed if no supplement)
                if not has_b12_supplement:
                    scores["DTX"] += 0.15
                # GA +0.20 if gas/bloating; GA -0.10 if fiber-tolerant and improvement
                if has_gas_bloating:
                    scores["GA"] += 0.20
                elif has_gi_improvement:
                    scores["GA"] -= 0.10
                descriptions.append("Vegan")
            
            # 4) Vegetarian
            elif diet == "vegetarian":
                scores["CM"] -= 0.10
                # DTX +0.10 if no B12 intake pattern (low eggs/dairy + no supplements)
                if not has_b12_supplement:
                    scores["DTX"] += 0.10
                # GA +0.10 if high-FODMAP complaints; GA -0.10 if symptoms improve
                if has_gas_bloating:
                    scores["GA"] += 0.10
                elif has_gi_improvement:
                    scores["GA"] -= 0.10
                descriptions.append("Vegetarian")
            
            # 5) Pescatarian
            elif diet == "pescatarian":
                scores["CM"] -= 0.20
                scores["MITO"] -= 0.05
                scores["IMM"] -= 0.05
                # DTX +0.10 only if high-mercury fish (placeholder - would need fish frequency data)
                # For now, skip this modifier as we don't have fish frequency data
                descriptions.append("Pescatarian")
            
            # 6) Gluten-Free
            elif diet == "gluten_free":
                # GA -0.20 if diagnosed celiac or symptom relief (assume relief if no gas/bloating)
                # GA +0.05 if no diagnosis and no benefit (assume no benefit if gas/bloating present)
                if not has_gas_bloating:
                    scores["GA"] -= 0.20
                else:
                    scores["GA"] += 0.05
                descriptions.append("Gluten-free")
            
            # 7) AIP (Autoimmune Protocol)
            elif diet == "aip":
                scores["IMM"] -= 0.25
                # GA -0.30 if symptom relief (assume relief if no gas/bloating)
                if not has_gas_bloating:
                    scores["GA"] -= 0.30
                descriptions.append("AIP")
            
            # 8) Elimination / Low-FODMAP
            elif diet == "elimination_low_fodmap":
                # GA -0.30 if dietitian-guided and symptom relief (assume relief if no gas/bloating)
                # GA -0.10 if self-directed with partial relief
                if not has_gas_bloating:
                    scores["GA"] -= 0.30
                else:
                    scores["GA"] -= 0.10
                scores["DTX"] -= 0.05
                descriptions.append("Low-FODMAP")
            
            # 9) Dairy-Free
            elif diet == "dairy_free":
                # MITO +0.05 / HRM +0.05 if no fortified alternatives (assume no fortification)
                scores["MITO"] += 0.05
                scores["HRM"] += 0.05
                descriptions.append("Dairy-free")
            
            # 10) Paleo
            elif diet == "paleo":
                scores["CM"] -= 0.10
                scores["GA"] += 0.10
                descriptions.append("Paleo")
        
        # 11) Other (free-text parsing)
        if "other" in diet_styles and diet_style_other:
            other_lower = diet_style_other.lower()
            
            # Parse keywords
            if any(keyword in other_lower for keyword in ['raw', 'juice', 'cleanse', 'fast']):
                scores["GA"] += 0.10
                scores["DTX"] += 0.10
                descriptions.append(f"Other: {diet_style_other}")
            
            elif 'carnivore' in other_lower and 'lean' in other_lower:
                # Mirror carnivore rules at lowered magnitudes
                scores["GA"] += 0.15
                scores["CM"] += 0.12
                scores["DTX"] += 0.05
                descriptions.append(f"Other: {diet_style_other}")
            
            elif any(keyword in other_lower for keyword in ['mediterranean', 'whole food', 'whole-food']):
                scores["CM"] -= 0.20
                scores["IMM"] -= 0.05
                descriptions.append(f"Other: {diet_style_other}")
            
            else:
                # Generic "other" - no specific scoring
                descriptions.append(f"Other: {diet_style_other}")
        
        return (scores, descriptions)

