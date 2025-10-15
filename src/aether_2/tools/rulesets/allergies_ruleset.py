"""
Allergies to health domain mapping ruleset.

This module implements evidence-based mappings from allergies to health focus areas,
including base weights by allergy type, severity modifiers, and integrative add-ons.
"""

from typing import Dict, List, Tuple


class AllergiesRuleset:
    """
    Handles allergy-based adjustments to health focus areas.
    
    Implements comprehensive allergy-to-domain mapping with:
    - Base weights by allergy type (immediate, food, drug, environmental, etc.)
    - Severity & context modifiers (anaphylaxis, multiple allergens, EpiPen)
    - Integrative/functional-medicine add-ons (PPI use, Vit-D deficiency, omega-3)
    """
    
    FOCUS_AREAS = {
        "CM": "Cardiometabolic & Metabolic Health",
        "COG": "Cognitive & Mental Health",
        "DTX": "Detoxification & Biotransformation",
        "IMM": "Immune Function & Inflammation",
        "MITO": "Mitochondrial & Energy Metabolism",
        "SKN": "Skin & Barrier Function",
        "STR": "Stress-Axis & Nervous System Resilience",
        "HRM": "Hormonal Health (Transport)",
        "GA": "Gut Health and assimilation",
    }
    
    # Allergy type keywords for classification
    IMMEDIATE_ALLERGY_KEYWORDS = ["hives", "urticaria", "angioedema", "swelling", "rash", "itching", "wheezing", "shortness of breath", "anaphylaxis", "epinephrine", "epipen"]
    FOOD_ALLERGY_KEYWORDS = ["peanut", "tree nut", "almond", "walnut", "cashew", "milk", "dairy", "egg", "soy", "wheat", "gluten", "sesame", "fish", "shellfish", "shrimp", "crab", "lobster"]
    DRUG_ALLERGY_KEYWORDS = ["penicillin", "sulfa", "sulfonamide", "antibiotic", "medication", "drug", "contrast", "iodine"]
    NSAID_ALLERGY_KEYWORDS = ["aspirin", "ibuprofen", "naproxen", "nsaid", "advil", "motrin", "aleve"]
    LATEX_ALLERGY_KEYWORDS = ["latex", "rubber", "condom", "glove"]
    LATEX_FRUIT_KEYWORDS = ["banana", "avocado", "kiwi", "papaya", "chestnut"]
    ENVIRONMENTAL_ALLERGY_KEYWORDS = ["pollen", "dust", "mite", "mold", "dander", "pet", "cat", "dog", "grass", "tree", "weed"]
    VENOM_ALLERGY_KEYWORDS = ["bee", "wasp", "hornet", "yellow jacket", "sting", "venom"]
    ALPHA_GAL_KEYWORDS = ["alpha-gal", "red meat", "beef", "pork", "lamb", "mammal", "tick", "delayed reaction"]
    EOE_KEYWORDS = ["eosinophilic esophagitis", "eoe", "esophageal", "swallowing difficulty"]
    
    def get_allergy_weights(self, allergies_data: List[Dict]) -> Dict[str, float]:
        """
        Calculate allergy-based weights for health focus areas.
        
        Args:
            allergies_data: List of allergy dictionaries with 'allergen' and 'reaction' keys
            
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        if not allergies_data:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        severity_modifiers = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        anaphylaxis_count = 0
        immediate_allergen_count = 0
        epipen_carried = False
        
        for allergy in allergies_data:
            allergen = allergy.get("allergen", "").lower()
            reaction = allergy.get("reaction", "").lower()
            
            # Check for anaphylaxis
            if "anaphylaxis" in reaction or "epinephrine" in reaction or "epipen" in reaction:
                anaphylaxis_count += 1
                epipen_carried = True
            
            # Classify and apply base weights
            allergy_type = self._classify_allergy_type(allergen, reaction)
            base_weights = self._get_base_weights(allergy_type, allergen, reaction)
            
            # Add base weights
            for code, weight in base_weights.items():
                weights[code] += weight
                
            # Count immediate-type allergens for modifier
            if allergy_type in ["immediate", "food", "drug", "nsaid", "latex", "environmental", "venom", "alpha_gal"]:
                immediate_allergen_count += 1
        
        # Apply severity modifiers
        severity_modifiers = self._get_severity_modifiers(
            anaphylaxis_count, immediate_allergen_count, epipen_carried
        )
        
        # Combine base weights and modifiers
        for code in weights:
            weights[code] += severity_modifiers[code]
            weights[code] = min(weights[code], 1.0)  # Clamp at 1.0
        
        return weights
    
    def _classify_allergy_type(self, allergen: str, reaction: str) -> str:
        """Classify allergy type based on allergen and reaction keywords."""
        combined_text = f"{allergen} {reaction}".lower()
        
        if any(keyword in combined_text for keyword in self.ALPHA_GAL_KEYWORDS):
            return "alpha_gal"
        elif any(keyword in combined_text for keyword in self.VENOM_ALLERGY_KEYWORDS):
            return "venom"
        elif any(keyword in combined_text for keyword in self.ENVIRONMENTAL_ALLERGY_KEYWORDS):
            return "environmental"
        elif any(keyword in combined_text for keyword in self.LATEX_ALLERGY_KEYWORDS):
            return "latex"
        elif any(keyword in combined_text for keyword in self.NSAID_ALLERGY_KEYWORDS):
            return "nsaid"
        elif any(keyword in combined_text for keyword in self.DRUG_ALLERGY_KEYWORDS):
            return "drug"
        elif any(keyword in combined_text for keyword in self.FOOD_ALLERGY_KEYWORDS):
            return "food"
        elif any(keyword in combined_text for keyword in self.IMMEDIATE_ALLERGY_KEYWORDS):
            return "immediate"
        else:
            return "unknown"
    
    def _get_base_weights(self, allergy_type: str, allergen: str, reaction: str) -> Dict[str, float]:
        """Get base weights for specific allergy type."""
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        combined_text = f"{allergen} {reaction}".lower()
        
        if allergy_type == "immediate":
            # Immediate-type (IgE-pattern) allergy present
            weights["IMM"] += 0.45
            weights["SKN"] += 0.20
            
        elif allergy_type == "food":
            # Food allergy
            weights["GA"] += 0.40
            weights["STR"] += 0.05
            
            # Check for EoE
            if any(keyword in combined_text for keyword in self.EOE_KEYWORDS):
                weights["GA"] = 0.50  # Override base GA weight
                weights["IMM"] += 0.10
                
        elif allergy_type == "drug":
            # Drug allergy
            weights["DTX"] += 0.25
            weights["IMM"] += 0.15
            
        elif allergy_type == "nsaid":
            # NSAID hypersensitivity
            weights["DTX"] += 0.20
            weights["IMM"] += 0.15
            
        elif allergy_type == "latex":
            # Latex allergy
            weights["SKN"] += 0.30
            weights["IMM"] += 0.20
            
            # Check for latex-fruit syndrome
            if any(keyword in combined_text for keyword in self.LATEX_FRUIT_KEYWORDS):
                weights["GA"] += 0.10
                
        elif allergy_type == "environmental":
            # Environmental allergy
            weights["IMM"] += 0.25
            weights["SKN"] += 0.20
            weights["STR"] += 0.10
            
        elif allergy_type == "venom":
            # Venom allergy
            weights["IMM"] += 0.30
            weights["STR"] += 0.10
            
        elif allergy_type == "alpha_gal":
            # Alpha-gal syndrome
            weights["IMM"] += 0.50
            weights["GA"] += 0.40
            weights["DTX"] += 0.10
            
        elif allergy_type == "unknown":
            # Oral-allergy syndrome / Pollen-Food Allergy Syndrome (default for unknown)
            weights["IMM"] += 0.20
            weights["GA"] += 0.20
            weights["SKN"] += 0.10
        
        return weights
    
    def _get_severity_modifiers(self, anaphylaxis_count: int, immediate_allergen_count: int, epipen_carried: bool) -> Dict[str, float]:
        """Get severity and context modifiers."""
        modifiers = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Anaphylaxis history
        if anaphylaxis_count > 0:
            modifiers["IMM"] += 0.30
            modifiers["STR"] += 0.10
            modifiers["COG"] += 0.05
            
            # EpiPen carried
            if epipen_carried:
                modifiers["IMM"] += 0.05
        
        # Multiple distinct immediate-type allergens
        if immediate_allergen_count > 1:
            additional_imm = min(0.05 * (immediate_allergen_count - 1), 0.15)
            modifiers["IMM"] += additional_imm
        
        return modifiers
    
    def get_integrative_addons(self, medications: List[str], lab_results: Dict = None, diet_info: Dict = None) -> Dict[str, float]:
        """
        Get integrative/functional-medicine add-ons based on medications, labs, and diet.
        
        Args:
            medications: List of current medications
            lab_results: Dictionary of lab results (optional)
            diet_info: Dictionary of diet information (optional)
            
        Returns:
            Dictionary mapping focus area codes to integrative add-on adjustments
        """
        addons = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        if not medications:
            medications = []
        
        meds_lower = [med.lower() for med in medications]
        
        # Long-term acid suppression (PPI/H2RA)
        acid_suppression_meds = ["omeprazole", "pantoprazole", "lansoprazole", "esomeprazole", 
                               "rabeprazole", "famotidine", "ranitidine", "cimetidine", "ppi", "h2ra"]
        
        if any(any(med in med_lower for med in acid_suppression_meds) for med_lower in meds_lower):
            addons["GA"] += 0.05
            addons["IMM"] += 0.05
        
        # Vitamin-D deficiency (if lab results provided)
        if lab_results:
            vit_d = lab_results.get("vitamin_d", lab_results.get("25_oh_d", lab_results.get("25-hydroxyvitamin_d")))
            if vit_d and isinstance(vit_d, (int, float)) and vit_d < 30:  # ng/mL threshold
                addons["IMM"] += 0.05
        
        # Very low omega-3 intake (if diet info provided)
        if diet_info:
            omega_3_intake = diet_info.get("omega_3_intake", diet_info.get("fish_intake", diet_info.get("epa_dha")))
            if omega_3_intake and isinstance(omega_3_intake, (int, float)) and omega_3_intake < 250:  # mg/day threshold
                addons["IMM"] += 0.05
        
        return addons
    
    def get_explainability_trace(self, allergies_data: List[Dict]) -> List[str]:
        """
        Generate human-readable decision tree explanations for allergy mappings.
        
        Args:
            allergies_data: List of allergy dictionaries
            
        Returns:
            List of explanation strings
        """
        explanations = []
        
        if not allergies_data:
            return explanations
        
        for allergy in allergies_data:
            allergen = allergy.get("allergen", "")
            reaction = allergy.get("reaction", "")
            combined_text = f"{allergen} {reaction}".lower()
            
            # Generate explanation based on allergy type and severity
            if "anaphylaxis" in combined_text or "epinephrine" in combined_text:
                if any(keyword in combined_text for keyword in self.FOOD_ALLERGY_KEYWORDS):
                    explanations.append(f"{allergen} anaphylaxis → IMM↑ STR↑ GA↑")
                else:
                    explanations.append(f"{allergen} anaphylaxis → IMM↑ STR↑")
                    
            elif any(keyword in combined_text for keyword in self.DRUG_ALLERGY_KEYWORDS):
                if "penicillin" in combined_text:
                    explanations.append(f"Penicillin ({reaction}) → DTX↑; consider de-labeling")
                else:
                    explanations.append(f"{allergen} allergy → DTX↑ IMM↑")
                    
            elif any(keyword in combined_text for keyword in self.LATEX_ALLERGY_KEYWORDS):
                if any(keyword in combined_text for keyword in self.LATEX_FRUIT_KEYWORDS):
                    explanations.append(f"Latex + fruit reactions → SKN↑ IMM↑ GA↑ (latex–fruit cross-reactivity)")
                else:
                    explanations.append(f"Latex allergy → SKN↑ IMM↑")
                    
            elif any(keyword in combined_text for keyword in self.ALPHA_GAL_KEYWORDS):
                explanations.append(f"Alpha-gal syndrome → IMM↑ GA↑ DTX↑ (delayed mammal product reactions)")
                
            elif any(keyword in combined_text for keyword in self.EOE_KEYWORDS):
                explanations.append(f"EoE + food allergy → GA↑ IMM↑ (mucosal immune reactivity)")
                
            else:
                # Generic explanation
                allergy_type = self._classify_allergy_type(allergen, reaction)
                if allergy_type != "unknown":
                    explanations.append(f"{allergen} allergy → domain adjustments applied")
        
        return explanations
