from crewai.tools import BaseTool
from typing import Type, Dict, List, Any, Union
from pydantic import BaseModel, Field
import json


class UserProfileCompilerInput(BaseModel):
    patient_and_blood_data: Union[str, dict] = Field(
        ..., description="JSON string OR dict with keys: patient_form, blood_report"
    )
    flagged_biomarkers: Union[str, dict] = Field(
        ..., description="JSON string OR dict containing flagged biomarkers from biomarker evaluation"
    )


class UserProfileCompilerTool(BaseTool):
    name: str = "compile_user_profile"
    description: str = (
        "Compiles patient data and flagged biomarkers into a comprehensive, structured user profile "
        "with health patterns, lifestyle factors, and functional goals."
    )
    args_schema: Type[BaseModel] = UserProfileCompilerInput

    def _extract_basic_profile(self, patient_form: dict) -> Dict[str, Any]:
        """Extract basic demographic and lifestyle information."""
        demographics = patient_form["patient_data"]["phase1_basic_intake"]["demographics"]
        lifestyle = patient_form["patient_data"]["phase2_detailed_intake"]["lifestyle_factors"]
        physical_activity = patient_form["patient_data"]["phase2_detailed_intake"]["physical_activity"]
        dietary_habits = patient_form["patient_data"]["phase2_detailed_intake"]["dietary_habits"]
        medications = patient_form["patient_data"]["phase1_basic_intake"]["medications"]
        supplements = patient_form["patient_data"]["phase1_basic_intake"]["supplements"]
        
        # Calculate BMI
        height_ft = demographics.get("height_feet", 0)
        height_in = demographics.get("height_inches", 0)
        weight_lbs = demographics.get("weight_lbs", 0)
        
        total_height_in = height_ft * 12 + height_in if height_ft and height_in else None
        bmi = None
        if total_height_in and weight_lbs:
            bmi = round((weight_lbs / (total_height_in**2)) * 703, 1)
        
        # Extract activity level
        exercise_days = physical_activity.get("exercise_days_per_week", 0)
        if exercise_days >= 5:
            activity_level = f"high ({exercise_days} days/week exercise)"
        elif exercise_days >= 3:
            activity_level = f"moderate ({exercise_days} days/week exercise)"
        elif exercise_days >= 1:
            activity_level = f"low ({exercise_days} days/week exercise)"
        else:
            activity_level = "sedentary (no regular exercise)"
        
        # Extract diet style
        diet_style = dietary_habits.get("diet_style", [])
        if not diet_style:
            diet_style = ["standard"]
        
        # Extract medications
        current_meds = medications.get("current_medications", [])
        medication_list = []
        for med in current_meds:
            med_str = f"{med.get('name', 'Unknown')} {med.get('dose', '')} {med.get('frequency', '')}"
            if med.get('purpose'):
                med_str += f" (for {med['purpose']})"
            medication_list.append(med_str)
        
        # Extract supplements
        current_supps = supplements.get("current_supplements", [])
        supplement_list = []
        for supp in current_supps:
            supp_str = f"{supp.get('name', 'Unknown')} {supp.get('dose', '')} {supp.get('frequency', '')}"
            if supp.get('purpose'):
                supp_str += f" (for {supp['purpose']})"
            supplement_list.append(supp_str)
        
        return {
            "age": demographics.get("age"),
            "sex": demographics.get("biological_sex", "").lower(),
            "BMI": bmi,
            "ancestry": demographics.get("ancestry", []),
            "activity_level": activity_level,
            "diet_style": diet_style,
            "supplements": supplement_list,
            "medications": medication_list
        }

    def _extract_biomarker_findings(self, flagged_biomarkers: dict) -> Dict[str, List[str]]:
        """Extract high and low biomarker findings."""
        flagged_list = flagged_biomarkers.get("flagged_biomarkers", [])
        
        high_biomarkers = []
        low_biomarkers = []
        
        for biomarker in flagged_list:
            category = biomarker.get("category", "").lower()
            name = biomarker.get("name", "")
            
            if any(keyword in category for keyword in ["high", "very_high", "critical", "elevated"]):
                high_biomarkers.append(name)
            elif any(keyword in category for keyword in ["low", "very_low", "severe", "deficiency"]):
                low_biomarkers.append(name)
        
        return {
            "high": high_biomarkers,
            "low": low_biomarkers
        }

    def _identify_health_patterns(self, patient_form: dict, flagged_biomarkers: dict) -> List[str]:
        """Identify key health patterns from the data."""
        patterns = []
        
        # Extract biomarker patterns
        flagged_list = flagged_biomarkers.get("flagged_biomarkers", [])
        biomarker_names = [b.get("name", "") for b in flagged_list]
        
        # Hormonal patterns
        hormonal_biomarkers = [name for name in biomarker_names if any(hormone in name.lower() 
                          for hormone in ["testosterone", "dhea", "shbg", "estradiol", "cortisol"])]
        if len(hormonal_biomarkers) >= 2:
            patterns.append(f"Hormonal imbalance ({', '.join(hormonal_biomarkers[:2])})")
        
        # Cardiovascular patterns
        cardio_biomarkers = [name for name in biomarker_names if any(cardio in name.lower() 
                          for cardio in ["cholesterol", "triglyceride", "hdl", "ldl", "apob", "apoa1"])]
        if cardio_biomarkers:
            patterns.append(f"Cardiovascular risk indicators ({', '.join(cardio_biomarkers[:2])})")
        
        # Protein/nutrition patterns
        protein_biomarkers = [name for name in biomarker_names if any(protein in name.lower() 
                          for protein in ["protein", "albumin", "calcium"])]
        if protein_biomarkers:
            patterns.append(f"Protein and mineral deficiency ({', '.join(protein_biomarkers[:2])})")
        
        # Metabolic patterns
        metabolic_biomarkers = [name for name in biomarker_names if any(metabolic in name.lower() 
                          for metabolic in ["glucose", "insulin", "hba1c", "triglyceride"])]
        if metabolic_biomarkers:
            patterns.append(f"Metabolic dysfunction ({', '.join(metabolic_biomarkers[:2])})")
        
        # Inflammation patterns
        inflam_biomarkers = [name for name in biomarker_names if any(inflam in name.lower() 
                          for inflam in ["crp", "homocysteine", "ferritin"])]
        if inflam_biomarkers:
            patterns.append(f"Inflammation markers ({', '.join(inflam_biomarkers[:2])})")
        
        return patterns

    def _extract_lifestyle_context(self, patient_form: dict) -> Dict[str, Any]:
        """Extract lifestyle and contextual information."""
        medical_history = patient_form["patient_data"]["phase1_basic_intake"]["medical_history"]
        family_history = patient_form["patient_data"]["phase2_detailed_intake"]["family_medical_history"]
        occupation = patient_form["patient_data"]["phase2_detailed_intake"]["occupation_wellness"]
        sleep = patient_form["patient_data"]["phase2_detailed_intake"]["sleep_patterns"]
        environmental = patient_form["patient_data"]["phase2_detailed_intake"]["environmental_exposures"]
        allergies = patient_form["patient_data"]["phase1_basic_intake"]["allergies"]
        pain_skin = patient_form["patient_data"]["phase2_detailed_intake"]["pain_and_skin_health"]
        
        # Extract medical conditions
        diagnoses = medical_history.get("diagnoses", [])
        
        # Extract family history
        family_conditions = []
        if family_history.get("has_family_history"):
            conditions_detail = family_history.get("conditions_detail", {})
            family_conditions = list(conditions_detail.keys())
        
        # Extract stress level
        stress_level = occupation.get("work_stress_level", 0)
        
        # Extract sleep pattern
        hours_category = sleep.get("hours_category", "unknown")
        trouble_sleep = sleep.get("trouble_falling_asleep", False) or sleep.get("trouble_staying_asleep", False)
        wake_refreshed = sleep.get("wake_feeling_refreshed", True)
        
        sleep_description = f"{hours_category.replace('_', '–')} hrs"
        if trouble_sleep:
            sleep_description += " with frequent night waking and non-restorative sleep"
        elif not wake_refreshed:
            sleep_description += " with non-restorative sleep"
        
        # Extract environmental exposures
        chemical_exposures = environmental.get("chemical_exposures", [])
        
        # Extract allergies
        known_allergies = allergies.get("known_allergies", [])
        
        # Extract skin conditions
        skin_issues = pain_skin.get("skin_health", {}).get("has_skin_issues", False)
        skin_conditions = []
        if skin_issues:
            skin_detail = pain_skin.get("skin_health", {}).get("skin_condition_details", "")
            if skin_detail:
                skin_conditions.append(skin_detail)
        
        # Extract chronic pain
        chronic_pain = pain_skin.get("chronic_pain", {}).get("has_chronic_pain", False)
        pain_conditions = []
        if chronic_pain:
            pain_detail = pain_skin.get("chronic_pain", {}).get("pain_details", "")
            if pain_detail:
                pain_conditions.append(pain_detail)
        
        return {
            "medical_conditions": diagnoses,
            "family_history": family_conditions,
            "stress_level": stress_level,
            "sleep_pattern": sleep_description,
            "environmental_exposures": chemical_exposures,
            "known_allergies": known_allergies,
            "skin_conditions": skin_conditions,
            "chronic_pain": pain_conditions
        }

    def _generate_functional_goals(self, patterns: List[str], basic_profile: Dict[str, Any]) -> List[str]:
        """Generate functional goals based on identified patterns and profile."""
        goals = []
        
        # Goals based on patterns
        for pattern in patterns:
            if "hormonal" in pattern.lower():
                goals.append("Balance hormone levels and improve endocrine regulation")
            elif "cardiovascular" in pattern.lower():
                goals.append("Enhance lipid metabolism and cardiovascular health")
            elif "protein" in pattern.lower() or "mineral" in pattern.lower():
                goals.append("Rebuild protein and mineral reserves")
            elif "metabolic" in pattern.lower():
                goals.append("Optimize glucose metabolism and insulin sensitivity")
            elif "inflammation" in pattern.lower():
                goals.append("Reduce inflammation and support immune function")
        
        # Goals based on basic profile
        if basic_profile.get("BMI", 0) > 25:
            goals.append("Support healthy weight management and metabolic function")
        
        if basic_profile.get("activity_level", "").startswith("sedentary"):
            goals.append("Increase physical activity and energy metabolism")
        
        if any("stress" in supp.lower() for supp in basic_profile.get("supplements", [])):
            goals.append("Enhance stress resilience and nervous system support")
        
        # General goals
        goals.append("Support overall detoxification and antioxidant defense")
        goals.append("Improve sleep quality and recovery")
        
        return goals[:5]  # Limit to top 5 goals

    def _run(self, patient_and_blood_data: Union[str, dict], flagged_biomarkers: Union[str, dict]) -> str:
        """Main execution method."""
        try:
            # Parse inputs
            if isinstance(patient_and_blood_data, str):
                patient_data = json.loads(patient_and_blood_data)
            else:
                patient_data = patient_and_blood_data
                
            if isinstance(flagged_biomarkers, str):
                flagged_data = json.loads(flagged_biomarkers)
            else:
                flagged_data = flagged_biomarkers
            
            # Extract components
            patient_form = patient_data["patient_form"]
            
            # Build profile components
            basic_profile = self._extract_basic_profile(patient_form)
            biomarker_findings = self._extract_biomarker_findings(flagged_data)
            health_patterns = self._identify_health_patterns(patient_form, flagged_data)
            lifestyle_context = self._extract_lifestyle_context(patient_form)
            functional_goals = self._generate_functional_goals(health_patterns, basic_profile)
            
            # Compile final profile
            user_profile = {
                "patient_summary": {
                    "basic_profile": basic_profile,
                    "biomarker_findings": biomarker_findings,
                    "key_health_patterns": health_patterns,
                    "lifestyle_and_context": lifestyle_context,
                    "functional_goals": functional_goals
                }
            }
            
            return json.dumps(user_profile, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Profile compilation failed: {str(e)}",
                "patient_summary": {
                    "basic_profile": {},
                    "biomarker_findings": {"high": [], "low": []},
                    "key_health_patterns": [],
                    "lifestyle_and_context": {},
                    "functional_goals": []
                }
            }, indent=2)
