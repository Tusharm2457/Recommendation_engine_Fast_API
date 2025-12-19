"""
Current supplements-based focus area scoring ruleset.
"""

import re
from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class SupplementsRuleset:
    """Ruleset for current supplements-based focus area scoring."""
    
    def get_supplements_weights(
        self,
        current_supplements: List[Dict],
        digestive_symptoms: str
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on current supplements.
        
        Args:
            current_supplements: List of supplement objects with 'name', 'dosage', 'frequency', 'purpose'
            digestive_symptoms: Free-text digestive symptoms for adverse reaction detection
            
        Returns:
            Tuple of:
                - Cumulative scores dict (all supplements combined, clamped at [0.0, 1.0])
                - Per-supplement breakdown dict {supplement_name: {focus_area: score}}
        """
        # Early exit if no supplements
        if not current_supplements:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_supplement_breakdown = {}
        
        # Track GA benefit for capping at -0.30
        ga_benefit_total = 0.0
        
        # Process each supplement
        for supp in current_supplements:
            supp_name = supp.get("name", "")
            if not supp_name:
                continue
            
            dosage = supp.get("dosage", "")
            purpose = supp.get("purpose", "")
            
            # Classify and score
            supp_type = self._classify_supplement(supp_name)
            
            # Skip unknown supplements
            if supp_type == "unknown":
                continue
            
            supp_scores = self._score_single_supplement(
                supp_type,
                dosage,
                purpose,
                digestive_symptoms,
                supp_name
            )
            
            # Track GA benefit separately for capping
            if supp_scores.get("GA", 0) < 0:
                ga_benefit_total += supp_scores["GA"]
            
            # Add to cumulative (before capping)
            for code in FOCUS_AREAS:
                cumulative_scores[code] += supp_scores[code]
            
            # Store per-supplement breakdown (use original name)
            per_supplement_breakdown[supp_name] = supp_scores
        
        # Apply GA benefit cap at -0.30
        if cumulative_scores["GA"] < -0.30:
            cumulative_scores["GA"] = -0.30
        
        # Clamp each focus area at [0.0, 1.0] (handle negative weights)
        for code in FOCUS_AREAS:
            cumulative_scores[code] = max(0.0, min(cumulative_scores[code], 1.0))
        
        return (cumulative_scores, per_supplement_breakdown)
    
    def _classify_supplement(self, supp_name: str) -> str:
        """
        Classify supplement into type using keyword matching.
        
        Returns:
            Supplement type: 'omega3', 'vitamin_d', 'magnesium', 'probiotic', 
                            'prebiotic', 'fiber', 'digestive_enzyme', 'bitters',
                            'iron', 'vitamin_a', 'berberine', 'oregano_oil',
                            'green_tea', 'turmeric', 'kava', 'melatonin',
                            'ashwagandha', 'gut_directed', 'unknown'
        """
        supp_lower = supp_name.lower()
        
        # A) Omega-3
        if any(keyword in supp_lower for keyword in [
            "omega-3", "omega 3", "omega3", "fish oil", "epa", "dha", "algal oil", 
            "krill oil", "cod liver oil", "icosapent", "vascepa", "lovaza"
        ]):
            return "omega3"
        
        # B) Vitamin D
        if any(keyword in supp_lower for keyword in [
            "vitamin d", "vit d", "cholecalciferol", "ergocalciferol", "d3", "d2"
        ]):
            return "vitamin_d"
        
        # C) Magnesium
        if any(keyword in supp_lower for keyword in [
            "magnesium", "mag ", "mg oxide", "mg citrate", "mg glycinate", "mg threonate",
            "mag oxide", "mag citrate", "mag glycinate"
        ]):
            return "magnesium"
        
        # D) Probiotics
        if any(keyword in supp_lower for keyword in [
            "probiotic", "lactobacillus", "bifidobacterium", "saccharomyces boulardii",
            "acidophilus", "culturelle", "align", "florastor"
        ]):
            return "probiotic"
        
        # D) Prebiotics
        if any(keyword in supp_lower for keyword in [
            "prebiotic", "inulin", "gos", "fos", "galactooligosaccharide", "fructooligosaccharide"
        ]):
            return "prebiotic"
        
        # D) Fiber
        if any(keyword in supp_lower for keyword in [
            "psyllium", "metamucil", "fiber", "methylcellulose", "citrucel"
        ]):
            return "fiber"
        
        # D) Digestive enzymes
        if any(keyword in supp_lower for keyword in [
            "digestive enzyme", "pancreatic enzyme", "lipase", "protease", "amylase",
            "bromelain", "papain", "creon", "pancreaze"
        ]):
            return "digestive_enzyme"
        
        # D) Digestive bitters
        if any(keyword in supp_lower for keyword in [
            "bitter", "gentian", "artemisia", "wormwood", "digestive bitter"
        ]):
            return "bitters"

        # E) Iron
        if any(keyword in supp_lower for keyword in [
            "iron", "ferrous", "ferric", "fe ", "feosol", "slow fe"
        ]):
            return "iron"

        # E) Vitamin A
        if any(keyword in supp_lower for keyword in [
            "vitamin a", "vit a", "retinol", "beta-carotene", "beta carotene"
        ]):
            return "vitamin_a"

        # F) Berberine
        if "berberine" in supp_lower:
            return "berberine"

        # F) Oregano oil
        if any(keyword in supp_lower for keyword in [
            "oregano oil", "oregano essential oil", "oil of oregano"
        ]):
            return "oregano_oil"

        # G) Green tea extract
        if any(keyword in supp_lower for keyword in [
            "green tea extract", "egcg", "green tea catechin", "gte"
        ]):
            return "green_tea"

        # G) Turmeric/Curcumin
        if any(keyword in supp_lower for keyword in [
            "turmeric", "curcumin", "piperine", "bioperine"
        ]):
            return "turmeric"

        # G) Kava
        if "kava" in supp_lower:
            return "kava"

        # H) Melatonin
        if "melatonin" in supp_lower:
            return "melatonin"

        # H) Ashwagandha
        if "ashwagandha" in supp_lower or "withania" in supp_lower:
            return "ashwagandha"

        # I) Other gut-directed (general prebiotics, bitters, teas)
        if any(keyword in supp_lower for keyword in [
            "digestive tea", "gut health", "gut support", "digestive support",
            "gi support", "bowel support"
        ]):
            return "gut_directed"

        return "unknown"

    def _parse_dose_numeric(self, dosage: str) -> float:
        """
        Extract numeric dose from free-text dosage field.

        Examples:
            "1000mg" -> 1000.0
            "2 capsules" -> 2.0
            "1 tsp" -> 1.0
            "500-1000mg" -> 750.0 (average)

        Returns:
            Numeric dose value, or 0.0 if unable to parse
        """
        if not dosage:
            return 0.0

        # Try to find numeric values
        numbers = re.findall(r'\d+\.?\d*', dosage)

        if not numbers:
            return 0.0

        # If range (e.g., "500-1000mg"), take average
        if len(numbers) >= 2 and '-' in dosage:
            return (float(numbers[0]) + float(numbers[1])) / 2.0

        # Otherwise take first number
        return float(numbers[0])

    def _check_adverse_reaction(self, digestive_symptoms: str, keywords: List[str]) -> bool:
        """Check if digestive symptoms contain any of the adverse reaction keywords."""
        if not digestive_symptoms:
            return False

        symptoms_lower = digestive_symptoms.lower()
        return any(keyword in symptoms_lower for keyword in keywords)

    def _check_reported_benefit(self, purpose: str, keywords: List[str]) -> bool:
        """Check if purpose field indicates reported benefit."""
        if not purpose:
            return False

        purpose_lower = purpose.lower()
        return any(keyword in purpose_lower for keyword in keywords)

    def _score_single_supplement(
        self,
        supp_type: str,
        dosage: str,
        purpose: str,
        digestive_symptoms: str,
        supp_name: str = ""
    ) -> Dict[str, float]:
        """Score a single supplement based on type, dose, purpose, and adverse reactions."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        dose_numeric = self._parse_dose_numeric(dosage)

        # A) Omega-3
        if supp_type == "omega3":
            # High dose (≥1000mg combined EPA+DHA)
            if dose_numeric >= 1000:
                scores["CM"] -= 0.25
                scores["IMM"] -= 0.05
                scores["MITO"] -= 0.05
            # Low dose (<1000mg or unknown)
            else:
                scores["CM"] -= 0.10

            # Adverse reactions (reflux, fishy burps, easy bruising)
            if self._check_adverse_reaction(digestive_symptoms, ["reflux", "burp", "fishy", "heartburn"]):
                scores["GA"] += 0.05

        # B) Vitamin D
        elif supp_type == "vitamin_d":
            # Routine dose (800-2000 IU)
            if 800 <= dose_numeric <= 2000 or dose_numeric == 0:  # 0 = unknown
                scores["IMM"] -= 0.10
            # High dose (>4000 IU)
            elif dose_numeric > 4000:
                scores["DTX"] += 0.15
                scores["CM"] += 0.05

        # C) Magnesium
        elif supp_type == "magnesium":
            # Check if for constipation and reported benefit
            if self._check_reported_benefit(purpose, ["constipation", "bowel", "regularity"]):
                scores["GA"] -= 0.10

            # High-dose with diarrhea
            if dose_numeric > 400 and self._check_adverse_reaction(digestive_symptoms, ["diarrhea", "loose stool"]):
                scores["GA"] += 0.08

        # D) Fiber (psyllium)
        elif supp_type == "fiber":
            # Used for bowel symptoms
            if self._check_reported_benefit(purpose, ["bowel", "constipation", "ibs", "regularity", "fiber"]):
                scores["GA"] -= 0.20

        # D) Probiotics
        elif supp_type == "probiotic":
            # Reported GI improvement
            if self._check_reported_benefit(purpose, ["gut", "digestive", "bowel", "ibs", "bloating", "gas"]):
                scores["GA"] -= 0.10
                scores["IMM"] -= 0.05

            # Bloating/worsening
            if self._check_adverse_reaction(digestive_symptoms, ["bloating", "gas", "worse", "worsening"]):
                scores["GA"] += 0.05

        # D) Prebiotics
        elif supp_type == "prebiotic":
            # Reported benefit
            if self._check_reported_benefit(purpose, ["gut", "digestive", "bowel", "fiber"]):
                scores["GA"] -= 0.05

        # D) Digestive enzymes
        elif supp_type == "digestive_enzyme":
            # Known/suspected pancreatic insufficiency or clear benefit
            if self._check_reported_benefit(purpose, ["pancreatic", "malabsorption", "fat", "enzyme", "digestion"]):
                scores["GA"] -= 0.20

        # D) Digestive bitters
        elif supp_type == "bitters":
            # Reported benefit
            if self._check_reported_benefit(purpose, ["appetite", "motility", "digestion", "bitter"]):
                scores["GA"] -= 0.05

            # Nausea/heartburn
            if self._check_adverse_reaction(digestive_symptoms, ["nausea", "heartburn"]):
                scores["GA"] += 0.03

        # E) Iron
        elif supp_type == "iron":
            # GI upset
            if self._check_adverse_reaction(digestive_symptoms, ["nausea", "constipation", "upset"]):
                scores["GA"] += 0.08

        # E) Vitamin A (high-dose)
        elif supp_type == "vitamin_a":
            # High-dose (>10,000 IU or >3000 mcg RAE)
            if dose_numeric > 10000 or dose_numeric > 3000:
                scores["DTX"] += 0.15

        # F) Berberine
        elif supp_type == "berberine":
            # Used for glycemic/lipid control and well-tolerated
            if self._check_reported_benefit(purpose, ["blood sugar", "glucose", "diabetes", "cholesterol", "lipid", "metabolic"]):
                scores["CM"] -= 0.10

            # GI upset
            if self._check_adverse_reaction(digestive_symptoms, ["upset", "nausea", "diarrhea"]):
                scores["GA"] += 0.05

        # F) Oregano oil
        elif supp_type == "oregano_oil":
            # GI irritation
            if self._check_adverse_reaction(digestive_symptoms, ["nausea", "heartburn", "irritation"]):
                scores["GA"] += 0.06

        # G) Green tea extract
        elif supp_type == "green_tea":
            # High-EGCG or weight-loss formulas
            scores["DTX"] += 0.15

        # G) Turmeric/Curcumin
        elif supp_type == "turmeric":
            # Enhanced bioavailability (piperine/bioperine) - check name, dosage, and purpose
            if any(keyword in text.lower() for text in [supp_name, dosage, purpose] for keyword in ["piperine", "bioperine"]):
                scores["DTX"] += 0.12
            else:
                scores["DTX"] += 0.08  # Conservative default

        # G) Kava
        elif supp_type == "kava":
            scores["DTX"] += 0.15
            scores["STR"] -= 0.05

        # H) Melatonin
        elif supp_type == "melatonin":
            # Chronic insomnia use (small/uncertain benefit)
            if self._check_reported_benefit(purpose, ["sleep", "insomnia", "melatonin"]):
                scores["STR"] -= 0.02

        # H) Ashwagandha
        elif supp_type == "ashwagandha":
            # Check for hyperthyroid symptoms (rare thyrotoxicosis)
            # Note: We don't have thyroid symptoms field, so skip this check
            pass

        # I) Other gut-directed
        elif supp_type == "gut_directed":
            # Reported benefit
            if self._check_reported_benefit(purpose, ["gut", "digestive", "bowel"]):
                scores["GA"] -= 0.05

        return scores

