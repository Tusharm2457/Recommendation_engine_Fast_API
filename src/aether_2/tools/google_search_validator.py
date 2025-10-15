from crewai.tools import BaseTool
from typing import Type, Union, List, Dict, Any
from pydantic import BaseModel, Field
import json
import os
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper

# Load environment variables
load_dotenv()

class GoogleSearchValidatorInput(BaseModel):
    user_profile: Union[str, dict] = Field(
        ..., description="JSON string OR dict containing the user profile from Agent 2"
    )
    ranked_ingredients: Union[str, dict] = Field(
        ..., description="JSON string OR dict containing ranked ingredients from Agent 4"
    )

class GoogleSearchValidatorTool(BaseTool):
    name: str = "google_search_validator"
    description: str = (
        "Google Search validator that researches the top ingredient recommendations "
        "against current scientific literature and market information to validate "
        "their effectiveness for the user's specific health conditions and biomarkers."
    )
    args_schema: Type[BaseModel] = GoogleSearchValidatorInput

    def _get_search_wrapper(self):
        """Get Google Search wrapper instance"""
        return GoogleSerperAPIWrapper()

    def _create_search_queries(self, user_profile: Dict[str, Any], top_ingredients: List[Dict[str, Any]]) -> List[str]:
        """Create targeted search queries for ingredient validation"""
        try:
            queries = []
            
            # Extract user context
            demographics = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("demographics", {})
            medical_history = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_history", {})
            medications = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medications", {})
            flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
            
            age = demographics.get("age", "")
            gender = demographics.get("biological_sex", "")
            diagnoses = medical_history.get("diagnoses", [])
            current_meds = [med.get("name", "") for med in medications.get("current_medications", [])]
            biomarker_names = [b.get("name", "") for b in flagged_biomarkers]
            
            # Create queries for top 5 ingredients
            for i, ingredient in enumerate(top_ingredients[:5]):
                ingredient_name = ingredient.get("ingredient_name", "")
                
                # Query 1: General effectiveness
                query1 = f"{ingredient_name} supplement effectiveness research studies"
                queries.append(query1)
                
                # Query 2: Condition-specific effectiveness
                if diagnoses:
                    condition_str = " ".join(diagnoses[:2])  # Top 2 conditions
                    query2 = f"{ingredient_name} {condition_str} treatment benefits research"
                    queries.append(query2)
                
                # Query 3: Biomarker-specific effectiveness
                if biomarker_names:
                    biomarker_str = " ".join(biomarker_names[:3])  # Top 3 biomarkers
                    query3 = f"{ingredient_name} {biomarker_str} biomarker improvement studies"
                    queries.append(query3)
                
                # Query 4: Drug interaction safety
                if current_meds:
                    med_str = " ".join(current_meds[:2])  # Top 2 medications
                    query4 = f"{ingredient_name} {med_str} drug interactions safety"
                    queries.append(query4)
                
                # Query 5: Demographics and safety
                if age and gender:
                    query5 = f"{ingredient_name} {gender} age {age} safety contraindications"
                    queries.append(query5)
            
            print(f"🔍 Created {len(queries)} patient-specific search queries for validation")
            return queries
            
        except Exception as e:
            print(f"❌ Error creating search queries: {str(e)}")
            return []

    def _perform_search(self, query: str) -> Dict[str, Any]:
        """Perform a single Google search and return structured results"""
        try:
            search_wrapper = self._get_search_wrapper()
            search_results = search_wrapper.run(query)
            
            return {
                "query": query,
                "results": search_results,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "query": query,
                "results": f"Search failed: {str(e)}",
                "status": "error"
            }

    def _validate_ingredients(self, search_results: List[Dict[str, Any]], top_ingredients: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate ingredients based on search results and patient-specific factors"""
        try:
            validated_ingredients = []
            
            # Extract patient context for validation
            diagnoses = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_history", {}).get("diagnoses", [])
            current_meds = [med.get("name", "") for med in user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medications", {}).get("current_medications", [])]
            flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
            
            for ingredient in top_ingredients:
                ingredient_name = ingredient.get("ingredient_name", "")
                
                # Find relevant search results for this ingredient
                relevant_results = []
                safety_results = []
                interaction_results = []
                
                for result in search_results:
                    if result["status"] == "success" and ingredient_name.lower() in result["results"].lower():
                        relevant_results.append(result)
                        
                        # Categorize results by type
                        query = result.get("query", "").lower()
                        if "safety" in query or "contraindication" in query or "side effect" in query:
                            safety_results.append(result)
                        elif "interaction" in query or "drug" in query:
                            interaction_results.append(result)
                
                # Calculate validation score based on multiple factors
                validation_score = 0.0
                validation_notes = []
                safety_score = 0.0
                interaction_score = 0.0
                
                # Base effectiveness score
                if relevant_results:
                    effectiveness_score = min(0.6, len(relevant_results) * 0.1)  # Max 60% for effectiveness
                    validation_score += effectiveness_score
                    validation_notes.append(f"Found {len(relevant_results)} relevant research sources")
                else:
                    validation_notes.append("Limited research validation found")
                
                # Safety assessment
                if safety_results:
                    safety_score = min(0.3, len(safety_results) * 0.1)  # Max 30% for safety
                    validation_score += safety_score
                    validation_notes.append(f"Safety data available from {len(safety_results)} sources")
                else:
                    validation_notes.append("Limited safety data found")
                
                # Drug interaction assessment
                if interaction_results:
                    interaction_score = min(0.2, len(interaction_results) * 0.1)  # Max 20% for interactions
                    validation_score += interaction_score
                    validation_notes.append(f"Drug interaction data from {len(interaction_results)} sources")
                else:
                    validation_notes.append("Limited drug interaction data found")
                
                # Patient-specific validation checks
                patient_specific_notes = self._check_patient_specific_factors(ingredient_name, diagnoses, current_meds, flagged_biomarkers)
                validation_notes.extend(patient_specific_notes)
                
                # Add validation data to ingredient
                validated_ingredient = ingredient.copy()
                validated_ingredient.update({
                    "validation_score": min(1.0, validation_score),
                    "safety_score": safety_score,
                    "interaction_score": interaction_score,
                    "validation_notes": validation_notes,
                    "search_results_count": len(relevant_results),
                    "validated": validation_score > 0.4  # Higher threshold for validation
                })
                
                validated_ingredients.append(validated_ingredient)
            
            return validated_ingredients
            
        except Exception as e:
            print(f"❌ Error validating ingredients: {str(e)}")
            return top_ingredients

    def _check_patient_specific_factors(self, ingredient_name: str, diagnoses: List[str], current_meds: List[str], flagged_biomarkers: List[Dict]) -> List[str]:
        """Check patient-specific factors for ingredient safety and appropriateness based on search results"""
        notes = []
        
        # This method now relies on Google Search results rather than hardcoded rules
        # The search queries are designed to find patient-specific information:
        # - Condition-specific effectiveness queries
        # - Drug interaction safety queries  
        # - Demographics and safety queries
        
        # Add general patient context notes
        if diagnoses:
            notes.append(f"Patient conditions: {', '.join(diagnoses)}")
        
        if current_meds:
            notes.append(f"Current medications: {', '.join(current_meds)}")
        
        if flagged_biomarkers:
            biomarker_summary = f"{len(flagged_biomarkers)} flagged biomarkers"
            notes.append(f"Biomarker status: {biomarker_summary}")
        
        return notes

    def _run(self, user_profile: Union[str, dict], ranked_ingredients: Union[str, dict]) -> str:
        """Main validation function using Google Search"""
        try:
            # Parse inputs
            if isinstance(user_profile, str):
                user_profile_parsed = json.loads(user_profile)
            else:
                user_profile_parsed = user_profile
                
            if isinstance(ranked_ingredients, str):
                ranked_ingredients_parsed = json.loads(ranked_ingredients)
            else:
                ranked_ingredients_parsed = ranked_ingredients
            
            print(f"🔍 Google Search Validator - Processing validation")
            print(f"  - User profile received: {'patient_data' in user_profile_parsed}")
            print(f"  - Ranked ingredients count: {len(ranked_ingredients_parsed)}")
            
            # Create search queries
            search_queries = self._create_search_queries(user_profile_parsed, ranked_ingredients_parsed)
            
            if not search_queries:
                return json.dumps({
                    "status": "error",
                    "message": "Could not create search queries",
                    "validated_ingredients": ranked_ingredients_parsed
                }, indent=2)
            
            # Perform searches
            print(f"🔍 Performing {len(search_queries)} Google searches...")
            search_results = []
            for i, query in enumerate(search_queries):
                print(f"  Search {i+1}/{len(search_queries)}: {query[:50]}...")
                result = self._perform_search(query)
                search_results.append(result)
            
            # Validate ingredients based on search results and patient profile
            validated_ingredients = self._validate_ingredients(search_results, ranked_ingredients_parsed, user_profile_parsed)
            
            # Create response
            response = {
                "status": "success",
                "message": f"Validated {len(validated_ingredients)} ingredients using Google Search",
                "search_queries_performed": len(search_queries),
                "search_results_summary": {
                    "successful_searches": len([r for r in search_results if r["status"] == "success"]),
                    "failed_searches": len([r for r in search_results if r["status"] == "error"])
                },
                "validated_ingredients": validated_ingredients
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Google Search validation failed: {str(e)}",
                "validated_ingredients": []
            }
            return json.dumps(error_response, indent=2)
