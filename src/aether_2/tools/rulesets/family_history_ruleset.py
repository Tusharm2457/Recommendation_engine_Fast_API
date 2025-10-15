"""
Family history to health domain mapping ruleset.

This module implements evidence-based mappings from family medical history
to health focus areas, including sex-based and premature condition modifiers.
"""

from typing import Dict, List, Tuple


class FamilyHistoryRuleset:
    """
    Handles family history-based adjustments to health focus areas.
    
    Implements comprehensive family condition-to-domain mapping with:
    - Base weights by family condition type
    - Sex-based modifiers (male/female specific adjustments)
    - Premature condition modifiers (early onset conditions)
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
    
    def get_family_history_weights(self, family_history_data: Dict, patient_sex: str = None) -> Dict[str, float]:
        """
        Calculate family history-based weights for health focus areas.
        
        Args:
            family_history_data: Dictionary containing family history information
            patient_sex: Patient's biological sex for sex-based modifiers
            
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        if not family_history_data:
            return weights
        
        # Extract family conditions from the data structure
        family_conditions = self._extract_family_conditions(family_history_data)
        
        # Apply base weights for each family condition
        for condition, details in family_conditions.items():
            base_weights = self._get_family_condition_weights(condition, details)
            
            # Apply sex-based modifiers
            sex_modifiers = self._get_sex_modifiers(condition, patient_sex)
            
            # Apply premature condition modifiers
            premature_modifiers = self._get_premature_modifiers(condition, details)
            
            # Combine all weights
            for code in weights:
                weights[code] += base_weights[code] + sex_modifiers[code] + premature_modifiers[code]
        
        # Clamp weights at 1.0 to avoid over-weighting
        for code in weights:
            weights[code] = min(weights[code], 1.0)
        
        return weights
    
    def _extract_family_conditions(self, family_history_data: Dict) -> Dict[str, Dict]:
        """Extract family conditions from the data structure."""
        conditions = {}
        
        # Check for conditions_detail field
        conditions_detail = family_history_data.get("conditions_detail", {})
        
        for condition, family_members in conditions_detail.items():
            if family_members:  # Only include conditions that have family members listed
                conditions[condition] = {
                    "family_members": family_members,
                    "is_premature": self._check_premature_condition(condition, family_members)
                }
        
        return conditions
    
    def _get_family_condition_weights(self, condition: str, details: Dict) -> Dict[str, float]:
        """Get base weights for specific family condition."""
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        condition_lower = condition.lower()
        
        # Anxiety Disorder
        if condition_lower == "anxiety_disorder":
            weights["STR"] += 0.10
            weights["COG"] += 0.05
            
        # Arthritis (family)
        elif condition_lower == "arthritis":
            # Check if RA/psoriatic noted in details
            family_members = details.get("family_members", [])
            if any("ra" in str(member).lower() or "psoriatic" in str(member).lower() for member in family_members):
                weights["IMM"] += 0.20
            else:  # OA only
                weights["MITO"] += 0.05
                
        # Asthma
        elif condition_lower == "asthma":
            weights["IMM"] += 0.20
            
        # Bleeding Disorder
        elif condition_lower == "bleeding_disorder":
            weights["IMM"] += 0.10
            weights["DTX"] += 0.05
            
        # Blood Clots (DVT)
        elif condition_lower == "blood_clots_or_dvt":
            weights["CM"] += 0.20
            
        # Cancer (unspecified)
        elif condition_lower == "cancer":
            weights["DTX"] += 0.10
            weights["IMM"] += 0.10
            
        # Coronary Artery Disease
        elif condition_lower == "coronary_artery_disease":
            weights["CM"] += 0.25
            
        # Claustrophobic
        elif condition_lower == "claustrophobic":
            weights["STR"] += 0.05
            weights["COG"] += 0.05
            
        # Diabetes – Insulin (likely T1D)
        elif condition_lower == "diabetes_insulin":
            weights["IMM"] += 0.15
            weights["CM"] += 0.15
            
        # Diabetes – Non-Insulin (T2D)
        elif condition_lower == "diabetes_non_insulin":
            weights["CM"] += 0.25
            
        # Dialysis (CKD proxy)
        elif condition_lower == "dialysis":
            weights["CM"] += 0.15
            weights["DTX"] += 0.10
            
        # Diverticulitis
        elif condition_lower == "diverticulitis":
            weights["GA"] += 0.10
            
        # Fibromyalgia
        elif condition_lower == "fibromyalgia":
            weights["STR"] += 0.10
            weights["COG"] += 0.05
            weights["MITO"] += 0.05
            
        # Gout
        elif condition_lower == "gout":
            weights["CM"] += 0.15
            weights["DTX"] += 0.05
            weights["GA"] += 0.05
            
        # Has Pacemaker (arrhythmia)
        elif condition_lower == "has_pacemaker":
            weights["CM"] += 0.20
            
        # Heart Attack
        elif condition_lower == "heart_attack":
            weights["CM"] += 0.25
            
        # Heart Murmur (valvular)
        elif condition_lower == "heart_murmur":
            weights["CM"] += 0.15
            
        # Hiatal Hernia or Reflux Disease
        elif condition_lower == "hiatal_hernia_or_reflux_disease":
            weights["GA"] += 0.15
            
        # HIV or AIDS
        elif condition_lower == "hiv_or_aids":
            # Record only, no weights
            pass
            
        # High Cholesterol
        elif condition_lower == "high_cholesterol":
            weights["CM"] += 0.25
            
        # High Blood Pressure
        elif condition_lower == "high_blood_pressure":
            weights["CM"] += 0.15
            
        # Overactive Thyroid (Graves proxy) - Note: This might be missing from the form
        elif "overactive_thyroid" in condition_lower or "graves" in condition_lower:
            weights["IMM"] += 0.15
            weights["HRM"] += 0.20
            
        # Kidney Disease
        elif condition_lower == "kidney_disease":
            weights["CM"] += 0.15
            weights["DTX"] += 0.10
            
        # Kidney Stones
        elif condition_lower == "kidney_stones":
            weights["GA"] += 0.15
            
        # Leg/Foot Ulcers
        elif condition_lower == "leg_foot_ulcers":
            weights["SKN"] += 0.10
            weights["CM"] += 0.10
            
        # Liver Disease
        elif condition_lower == "liver_disease":
            weights["DTX"] += 0.20
            weights["CM"] += 0.10
            
        # Osteoporosis (parental hip fracture)
        elif condition_lower == "osteoporosis":
            weights["HRM"] += 0.20
            
        # Polio
        elif condition_lower == "polio":
            # Record only, no weights
            pass
            
        # Pulmonary Embolism
        elif condition_lower == "pulmonary_embolism":
            weights["CM"] += 0.20
            
        # Reflux or Ulcers
        elif condition_lower == "reflux_or_ulcers":
            weights["GA"] += 0.15
            
        # Stroke
        elif condition_lower == "stroke":
            weights["COG"] += 0.20
            weights["CM"] += 0.10
            
        # Tuberculosis
        elif condition_lower == "tuberculosis":
            # Record only, no weights
            pass
            
        # Other conditions - try to map to nearest rule
        else:
            other_weights = self._map_other_conditions(condition_lower)
            for code, weight in other_weights.items():
                weights[code] += weight
        
        return weights
    
    def _get_sex_modifiers(self, condition: str, patient_sex: str) -> Dict[str, float]:
        """Get sex-based modifiers for family conditions."""
        modifiers = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        if not patient_sex:
            return modifiers
        
        condition_lower = condition.lower()
        sex_lower = patient_sex.lower()
        
        # Gout - 10% increase if male patient
        if condition_lower == "gout" and sex_lower == "male":
            modifiers["CM"] += 0.015  # 10% of 0.15
            modifiers["DTX"] += 0.005  # 10% of 0.05
            modifiers["GA"] += 0.005   # 10% of 0.05
            
        # Overactive Thyroid - 10% increase if female patient
        elif ("overactive_thyroid" in condition_lower or "graves" in condition_lower) and sex_lower == "female":
            modifiers["IMM"] += 0.015  # 10% of 0.15
            modifiers["HRM"] += 0.020  # 10% of 0.20
            
        # Osteoporosis - 10% increase if female patient
        elif condition_lower == "osteoporosis" and sex_lower == "female":
            modifiers["HRM"] += 0.020  # 10% of 0.20
            
        # Kidney Stones - 5% increase if male patient
        elif condition_lower == "kidney_stones" and sex_lower == "male":
            modifiers["GA"] += 0.0075  # 5% of 0.15
        
        return modifiers
    
    def _get_premature_modifiers(self, condition: str, details: Dict) -> Dict[str, float]:
        """Get premature condition modifiers."""
        modifiers = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        if not details.get("is_premature", False):
            return modifiers
        
        condition_lower = condition.lower()
        
        # Coronary Artery Disease - premature adds +0.10
        if condition_lower == "coronary_artery_disease":
            modifiers["CM"] += 0.10
            
        # Heart Attack - premature adds +0.10
        elif condition_lower == "heart_attack":
            modifiers["CM"] += 0.10
        
        return modifiers
    
    def _check_premature_condition(self, condition: str, family_members: List) -> bool:
        """Check if condition is premature based on family member details."""
        # This is a simplified check - in a real implementation, you'd parse
        # age information from family member details
        condition_lower = condition.lower()
        
        # Define premature age thresholds
        premature_conditions = {
            "coronary_artery_disease": 55,  # CAD before 55
            "heart_attack": 55,  # MI before 55
            "stroke": 65,  # Stroke before 65
            "diabetes_insulin": 40,  # T1D before 40
            "diabetes_non_insulin": 40,  # T2D before 40
        }
        
        for condition_key, age_threshold in premature_conditions.items():
            if condition_key in condition_lower:
                # In a real implementation, you'd extract age from family_members
                # For now, we'll assume some conditions are premature
                return True
        
        return False
    
    def _map_other_conditions(self, condition: str) -> Dict[str, float]:
        """Map other conditions to nearest rules."""
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Celiac/IBD/Polyps/Barrett's → GA rules
        if any(keyword in condition for keyword in ["celiac", "ibd", "crohn", "ulcerative colitis", "polyps", "barrett"]):
            weights["GA"] += 0.15
            
        # Autoimmune conditions → IMM rules
        elif any(keyword in condition for keyword in ["autoimmune", "lupus", "scleroderma", "sjogren"]):
            weights["IMM"] += 0.20
            
        # Neurological conditions → COG rules
        elif any(keyword in condition for keyword in ["alzheimer", "dementia", "parkinson", "ms", "multiple sclerosis"]):
            weights["COG"] += 0.20
            
        # Metabolic conditions → CM rules
        elif any(keyword in condition for keyword in ["metabolic", "syndrome", "obesity"]):
            weights["CM"] += 0.20
        
        return weights
    
    def get_explainability_trace(self, family_history_data: Dict, patient_sex: str = None) -> List[str]:
        """
        Generate human-readable explanations for family history mappings.
        
        Args:
            family_history_data: Dictionary containing family history information
            patient_sex: Patient's biological sex
            
        Returns:
            List of explanation strings
        """
        explanations = []
        
        if not family_history_data:
            return explanations
        
        family_conditions = self._extract_family_conditions(family_history_data)
        
        for condition, details in family_conditions.items():
            family_members = details.get("family_members", [])
            is_premature = details.get("is_premature", False)
            
            # Generate explanation based on condition type
            if condition.lower() == "anxiety_disorder":
                explanations.append(f"Family anxiety → STR↑ COG↑")
                
            elif condition.lower() == "arthritis":
                if any("ra" in str(member).lower() or "psoriatic" in str(member).lower() for member in family_members):
                    explanations.append(f"Family RA/psoriatic arthritis → IMM↑")
                else:
                    explanations.append(f"Family arthritis → MITO↑")
                    
            elif condition.lower() == "asthma":
                explanations.append(f"Family asthma → IMM↑")
                
            elif condition.lower() == "diabetes_insulin":
                explanations.append(f"Family T1D → IMM↑ CM↑")
                    
            elif condition.lower() == "diabetes_non_insulin":
                explanations.append(f"Family T2D → CM↑")
                    
            elif condition.lower() == "heart_attack":
                if is_premature:
                    explanations.append(f"Family premature MI → CM↑ (premature modifier)")
                else:
                    explanations.append(f"Family MI → CM↑")
                    
            elif condition.lower() == "stroke":
                explanations.append(f"Family stroke → COG↑ CM↑")
                
            elif condition.lower() == "cancer":
                explanations.append(f"Family cancer → DTX↑ IMM↑")
                
            elif condition.lower() == "high_cholesterol":
                explanations.append(f"Family high cholesterol → CM↑")
                
            elif condition.lower() == "high_blood_pressure":
                explanations.append(f"Family high blood pressure → CM↑")
                
            elif condition.lower() == "osteoporosis":
                if patient_sex and patient_sex.lower() == "female":
                    explanations.append(f"Family osteoporosis → HRM↑ (female modifier)")
                else:
                    explanations.append(f"Family osteoporosis → HRM↑")
                    
            elif condition.lower() == "gout":
                if patient_sex and patient_sex.lower() == "male":
                    explanations.append(f"Family gout → CM↑ DTX↑ GA↑ (male modifier)")
                else:
                    explanations.append(f"Family gout → CM↑ DTX↑ GA↑")
                    
            else:
                explanations.append(f"Family {condition} → domain adjustments applied")
        
        return explanations
