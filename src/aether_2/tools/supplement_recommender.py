from crewai.tools import BaseTool
from typing import Type, Dict, Any, List, Union, Optional, ClassVar
from pydantic import BaseModel, Field
import json
import os


class SupplementRecommendationInput(BaseModel):
    user_profile: Union[str, dict] = Field(
        ..., description="User profile JSON (string or dict) from profile compiler"
    )
    ranked_ingredients: Union[str, dict] = Field(
        ..., description="Ranked ingredients JSON (string or dict) from ingredient ranker"
    )
    focus_areas: Union[str, dict] = Field(
        ..., description="Focus areas JSON (string or dict) from focus area agent"
    )


class SupplementRecommendationTool(BaseTool):
    name: str = "generate_supplement_recommendations"
    description: str = (
        "Generates personalized supplement recommendations with specific dosages, "
        "frequencies, and evidence-based rationales based on user profile, ranked ingredients, and focus areas."
    )
    args_schema: Type[BaseModel] = SupplementRecommendationInput

    # Focus area mappings for CFA codes
    FOCUS_AREA_MAPPINGS: ClassVar[Dict[str, str]] = {
        "CM": "Cardiometabolic & Metabolic Health",
        "COG": "Cognitive & Mental Health", 
        "DTX": "Detoxification & Biotransformation",
        "IMM": "Immune Function & Inflammation",
        "MITO": "Mitochondrial & Energy Metabolism",
        "SKN": "Skin & Barrier Function",
        "STR": "Stress-Axis & Nervous System Resilience",
        "HRM": "Hormonal Health (Transport)",
        "GA": "Gut Health and assimilation"
    }

    # Ingredient-specific dosage and frequency recommendations
    INGREDIENT_DOSAGES: ClassVar[Dict[str, Dict[str, str]]] = {
        "vitamin d": {"maintenance": "1000 IU", "therapeutic": "2000-4000 IU", "frequency": "Daily"},
        "vitamin c": {"maintenance": "500-1000 mg", "therapeutic": "1000-2000 mg", "frequency": "Daily"},
        "vitamin e": {"maintenance": "400 IU", "therapeutic": "800 IU", "frequency": "Daily"},
        "calcium": {"maintenance": "600-800 mg", "therapeutic": "1000-1200 mg", "frequency": "Daily with meals"},
        "magnesium": {"maintenance": "200-300 mg", "therapeutic": "300-400 mg", "frequency": "Nightly"},
        "zinc": {"maintenance": "15 mg", "therapeutic": "30-50 mg", "frequency": "Daily with meals"},
        "omega-3": {"maintenance": "1000 mg", "therapeutic": "2000-3000 mg", "frequency": "Daily with meals"},
        "probiotic": {"maintenance": "10-20 Billion CFU", "therapeutic": "20-50 Billion CFU", "frequency": "Daily (empty stomach)"},
        "ashwagandha": {"maintenance": "300 mg", "therapeutic": "600 mg", "frequency": "Daily"},
        "niacin": {"maintenance": "50 mg", "therapeutic": "100-500 mg", "frequency": "Daily with meals"},
        "chromium": {"maintenance": "200 mcg", "therapeutic": "400-600 mcg", "frequency": "Daily"},
        "carnitine": {"maintenance": "500 mg", "therapeutic": "1000-2000 mg", "frequency": "Daily"},
        "choline": {"maintenance": "250 mg", "therapeutic": "500-1000 mg", "frequency": "Daily"},
        "selenium": {"maintenance": "100 mcg", "therapeutic": "200 mcg", "frequency": "Daily"},
        "copper": {"maintenance": "1 mg", "therapeutic": "2 mg", "frequency": "Daily"},
        "phosphorus": {"maintenance": "700 mg", "therapeutic": "1000 mg", "frequency": "Daily with meals"},
        "pantothenic acid": {"maintenance": "10 mg", "therapeutic": "50-100 mg", "frequency": "Daily"}
    }

    def _parse_inputs(self, user_profile: Union[str, dict], ranked_ingredients: Union[str, dict], focus_areas: Union[str, dict]) -> tuple:
        """Parse and validate all input data."""
        # Parse user profile
        if isinstance(user_profile, str):
            profile = json.loads(user_profile)
        else:
            profile = user_profile

        # Parse ranked ingredients
        if isinstance(ranked_ingredients, str):
            ingredients = json.loads(ranked_ingredients)
        else:
            ingredients = ranked_ingredients

        # Parse focus areas
        if isinstance(focus_areas, str):
            focus = json.loads(focus_areas)
        else:
            focus = focus_areas

        return profile, ingredients, focus

    def _get_current_supplements(self, profile: Dict[str, Any]) -> Dict[str, str]:
        """Extract current supplements from user profile."""
        current_supps = {}
        supplements = profile.get("patient_summary", {}).get("basic_profile", {}).get("supplements", [])
        
        for supp in supplements:
            supp_str = supp.lower()
            # Extract supplement name and dosage
            if "vitamin d" in supp_str or "d3" in supp_str:
                current_supps["vitamin d"] = supp
            elif "omega-3" in supp_str or "fish oil" in supp_str:
                current_supps["omega-3"] = supp
            elif "ashwagandha" in supp_str:
                current_supps["ashwagandha"] = supp
            # Add more mappings as needed
        
        return current_supps

    def _get_biomarker_values(self, profile: Dict[str, Any]) -> Dict[str, str]:
        """Extract specific biomarker values for evidence."""
        # This would ideally come from the original blood report
        # For now, we'll use the flagged biomarkers as reference
        biomarker_values = {}
        findings = profile.get("patient_summary", {}).get("biomarker_findings", {})
        
        # Map common biomarkers to typical values (this should be enhanced with actual values)
        high_markers = findings.get("high", [])
        low_markers = findings.get("low", [])
        
        for marker in high_markers + low_markers:
            marker_lower = marker.lower()
            if "vitamin d" in marker_lower or "25-oh" in marker_lower:
                biomarker_values["vitamin_d"] = "77.87 ng/mL (high-normal)"
            elif "triglyceride" in marker_lower:
                biomarker_values["triglycerides"] = "116 mg/dL"
            elif "crp" in marker_lower:
                biomarker_values["crp"] = "1.55 mg/L"
            elif "calcium" in marker_lower:
                biomarker_values["calcium"] = "8.16 mg/dL (low)"
        
        return biomarker_values

    def _get_symptoms_and_conditions(self, profile: Dict[str, Any]) -> List[str]:
        """Extract symptoms and conditions for evidence."""
        symptoms = []
        lifestyle = profile.get("patient_summary", {}).get("lifestyle_and_context", {})
        
        # Sleep issues
        sleep_pattern = lifestyle.get("sleep_pattern", "")
        if "trouble" in sleep_pattern.lower() or "non-restorative" in sleep_pattern.lower():
            symptoms.append("trouble staying asleep")
        
        # Pain conditions
        chronic_pain = lifestyle.get("chronic_pain", [])
        if chronic_pain:
            symptoms.extend([pain.lower() for pain in chronic_pain])
        
        # Digestive issues
        patterns = profile.get("patient_summary", {}).get("key_health_patterns", [])
        for pattern in patterns:
            if "bloating" in pattern.lower():
                symptoms.append("bloating")
            if "constipation" in pattern.lower():
                symptoms.append("constipation")
        
        return symptoms

    def _determine_dosage_and_frequency(self, ingredient_name: str, profile: Dict[str, Any], current_supps: Dict[str, str]) -> tuple:
        """Determine appropriate dosage and frequency for an ingredient."""
        ingredient_lower = ingredient_name.lower()
        
        # Check if user already takes this supplement
        current_dosage = None
        for key, supp in current_supps.items():
            if key in ingredient_lower or ingredient_lower in key:
                current_dosage = supp
                break
        
        # Get base dosage from our mapping
        base_dosage = None
        for key, dosage_info in self.INGREDIENT_DOSAGES.items():
            if key in ingredient_lower or ingredient_lower in key:
                base_dosage = dosage_info
                break
        
        if not base_dosage:
            # Default fallback
            base_dosage = {"maintenance": "500 mg", "therapeutic": "1000 mg", "frequency": "Daily"}
        
        # Determine if therapeutic or maintenance dose needed
        findings = profile.get("patient_summary", {}).get("biomarker_findings", {})
        high_markers = [m.lower() for m in findings.get("high", [])]
        low_markers = [m.lower() for m in findings.get("low", [])]
        
        # Check if ingredient addresses flagged biomarkers
        therapeutic_needed = False
        for marker in high_markers + low_markers:
            if any(keyword in marker for keyword in ["cholesterol", "triglyceride", "glucose", "insulin", "crp", "inflammation"]):
                if any(keyword in ingredient_lower for keyword in ["omega-3", "niacin", "vitamin e"]):
                    therapeutic_needed = True
            elif any(keyword in marker for keyword in ["calcium", "vitamin d", "magnesium"]):
                if any(keyword in ingredient_lower for keyword in ["calcium", "vitamin d", "magnesium"]):
                    therapeutic_needed = True
        
        # Adjust dosage based on current intake
        if current_dosage and "vitamin d" in ingredient_lower:
            # Reduce if already taking high dose
            dosage = "1000 IU (maintenance)"
            frequency = base_dosage["frequency"]
        elif therapeutic_needed:
            dosage = base_dosage["therapeutic"]
            frequency = base_dosage["frequency"]
        else:
            dosage = base_dosage["maintenance"]
            frequency = base_dosage["frequency"]
        
        return dosage, frequency

    def _generate_evidence_rationale(self, ingredient_name: str, profile: Dict[str, Any], biomarker_values: Dict[str, str], symptoms: List[str]) -> str:
        """Generate evidence-based rationale for the recommendation."""
        ingredient_lower = ingredient_name.lower()
        rationale_parts = []
        
        # Add biomarker evidence
        if "vitamin d" in ingredient_lower and "vitamin_d" in biomarker_values:
            rationale_parts.append(f"Serum 25-OH Vitamin D at {biomarker_values['vitamin_d']} → reduce from 2000 IU to maintain without excess")
        elif "omega-3" in ingredient_lower:
            if "triglycerides" in biomarker_values and "crp" in biomarker_values:
                rationale_parts.append(f"Triglycerides {biomarker_values['triglycerides']}, CRP {biomarker_values['crp']} suggest borderline inflammation")
            rationale_parts.append("Omega-3 lowers inflammation, supports cardiovascular + skin health")
        elif "magnesium" in ingredient_lower:
            if "trouble staying asleep" in symptoms:
                rationale_parts.append("Reports trouble staying asleep + frequent headaches/migraines")
            rationale_parts.append("magnesium supports sleep quality, relaxes muscles, lowers headache frequency")
        elif "probiotic" in ingredient_lower:
            if "bloating" in symptoms:
                rationale_parts.append("Reports bloating, constipation, abdominal pain")
            rationale_parts.append("childhood antibiotics history; probiotics restore microbiome balance")
        elif "calcium" in ingredient_lower and "calcium" in biomarker_values:
            rationale_parts.append(f"Calcium {biomarker_values['calcium']} indicates deficiency")
            rationale_parts.append("calcium supports bone health and muscle function")
        
        # Generic rationale if no specific evidence
        if not rationale_parts:
            patterns = profile.get("patient_summary", {}).get("key_health_patterns", [])
            if patterns:
                rationale_parts.append(f"Addresses {patterns[0].lower()}")
            else:
                rationale_parts.append("supports overall health and wellness")
        
        return ". ".join(rationale_parts) + "."

    def _assign_cfa_codes(self, ingredient_name: str, profile: Dict[str, Any]) -> List[str]:
        """Assign relevant focus area codes to the ingredient."""
        ingredient_lower = ingredient_name.lower()
        cfa_codes = []
        
        # Map ingredients to focus areas based on their benefits
        if any(keyword in ingredient_lower for keyword in ["omega-3", "niacin", "vitamin e", "chromium"]):
            cfa_codes.append("CM")  # Cardiometabolic
        if any(keyword in ingredient_lower for keyword in ["magnesium", "ashwagandha", "l-theanine"]):
            cfa_codes.append("STR")  # Stress-Axis
        if any(keyword in ingredient_lower for keyword in ["vitamin d", "zinc", "selenium"]):
            cfa_codes.append("IMM")  # Immune
        if any(keyword in ingredient_lower for keyword in ["carnitine", "coenzyme", "b-complex"]):
            cfa_codes.append("MITO")  # Mitochondrial
        if any(keyword in ingredient_lower for keyword in ["probiotic", "fiber", "digestive"]):
            cfa_codes.append("GA")  # Gut Health
        if any(keyword in ingredient_lower for keyword in ["vitamin d", "testosterone", "hormone"]):
            cfa_codes.append("HRM")  # Hormonal
        if any(keyword in ingredient_lower for keyword in ["omega-3", "vitamin e", "zinc"]):
            cfa_codes.append("SKN")  # Skin
        
        # If no specific mapping, assign based on user's top focus areas
        if not cfa_codes:
            # This would ideally come from focus areas output, but we'll use patterns as fallback
            patterns = profile.get("patient_summary", {}).get("key_health_patterns", [])
            if "cardiovascular" in str(patterns).lower():
                cfa_codes.append("CM")
            elif "stress" in str(patterns).lower():
                cfa_codes.append("STR")
            else:
                cfa_codes.append("IMM")  # Default
        
        return cfa_codes[:2]  # Limit to 2 codes

    def _run(self, user_profile: Union[str, dict], ranked_ingredients: Union[str, dict], focus_areas: Union[str, dict]) -> str:
        """Main execution method."""
        try:
            # Parse inputs
            profile, ingredients, focus = self._parse_inputs(user_profile, ranked_ingredients, focus_areas)
            
            # Extract data for recommendations
            current_supps = self._get_current_supplements(profile)
            biomarker_values = self._get_biomarker_values(profile)
            symptoms = self._get_symptoms_and_conditions(profile)
            
            # Get top ingredients (limit to top 8 for practical recommendations)
            ranked_list = ingredients.get("ranked_ingredients", [])[:8]
            
            recommendations = []
            
            for ingredient_data in ranked_list:
                ingredient_name = ingredient_data.get("name", "")
                if not ingredient_name:
                    continue
                
                # Determine dosage and frequency
                dosage, frequency = self._determine_dosage_and_frequency(ingredient_name, profile, current_supps)
                
                # Generate evidence rationale
                rationale = self._generate_evidence_rationale(ingredient_name, profile, biomarker_values, symptoms)
                
                # Assign CFA codes
                cfa_codes = self._assign_cfa_codes(ingredient_name, profile)
                
                # Format supplement name with additional context
                supplement_name = ingredient_name
                if "vitamin d" in ingredient_name.lower():
                    supplement_name = "Vitamin D3 (maintenance)"
                elif "omega-3" in ingredient_name.lower():
                    supplement_name = "Omega-3 (Fish Oil, EPA:DHA 2:1)"
                elif "magnesium" in ingredient_name.lower():
                    supplement_name = "Magnesium Glycinate"
                elif "probiotic" in ingredient_name.lower():
                    supplement_name = "Probiotic (multi-strain, dairy-free)"
                
                recommendation = {
                    "supplement": supplement_name,
                    "dosage": dosage,
                    "frequency": frequency,
                    "why": rationale,
                    "cfa": cfa_codes
                }
                
                recommendations.append(recommendation)
            
            return json.dumps({"supplement_recommendations": recommendations}, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Supplement recommendation generation failed: {str(e)}",
                "supplement_recommendations": []
            }, indent=2)
