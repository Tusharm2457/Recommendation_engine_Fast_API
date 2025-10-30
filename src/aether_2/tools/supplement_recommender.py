from crewai.tools import BaseTool
from typing import Type, Union, List, Dict, Any
from pydantic import BaseModel, Field
import json

class SupplementRecommendationInput(BaseModel):
    user_profile: Union[str, dict, None] = Field(
        default=None,
        description="User profile JSON from user_profile_compiler agent. If not provided, will use kickoff inputs."
    )
    rag_ingredients: Union[str, dict, None] = Field(
        default=None,
        description="RAG-ranked ingredients JSON from ingredient_ranker_rag agent"
    )
    web_ingredients: Union[str, dict, None] = Field(
        default=None,
        description="Web-discovered ingredients JSON from web_ingredient_discovery agent"
    )

class SupplementRecommendationTool(BaseTool):
    name: str = "generate_supplement_recommendations"
    description: str = (
        "Final collaborative agent that analyzes user profile, RAG-ranked ingredients, and web-discovered ingredients "
        "to create the ultimate personalized supplement recommendations using medical reasoning."
    )
    args_schema: Type[BaseModel] = SupplementRecommendationInput
    kickoff_inputs: dict = {}

    def _parse_inputs(self, user_profile: Union[str, dict], rag_ingredients: Union[str, dict], web_ingredients: Union[str, dict]) -> tuple:
        """Parse and validate all input data."""
        # Parse user profile
        if isinstance(user_profile, str):
            profile = json.loads(user_profile)
        else:
            profile = user_profile

        # Parse RAG ingredients
        if isinstance(rag_ingredients, str):
            rag_data = json.loads(rag_ingredients)
        else:
            rag_data = rag_ingredients

        # Parse web ingredients
        if isinstance(web_ingredients, str):
            web_data = json.loads(web_ingredients)
        else:
            web_data = web_ingredients

        return profile, rag_data, web_data

    def _create_medical_analysis_prompt(self, user_profile: Dict[str, Any], rag_ingredients: List[Dict], web_ingredients: List[Dict]) -> str:
        """Create comprehensive medical analysis prompt for LLM"""
        
        # Extract key patient information
        demographics = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("demographics", {})
        medical_history = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_history", {})
        flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
        
        # Extract pain and skin health
        pain_skin_health = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("pain_and_skin_health", {})
        headaches = pain_skin_health.get("headaches", [])
        chronic_pain = pain_skin_health.get("chronic_pain", [])
        skin_health = pain_skin_health.get("skin_health", [])
        
        # Create biomarker context with status
        biomarker_context = []
        for biomarker in flagged_biomarkers:
            name = biomarker.get("name", "")
            status = biomarker.get("status", "")
            if name and status:
                biomarker_context.append(f"{status} {name}")
        
        biomarker_text = ", ".join(biomarker_context) if biomarker_context else "no flagged biomarkers"
        
        # Format RAG ingredients
        rag_ingredient_list = []
        for i, ingredient in enumerate(rag_ingredients[:10]):  # Top 10 RAG ingredients
            rag_ingredient_list.append(f"{i+1}. {ingredient.get('ingredient_name', '')} (Score: {ingredient.get('final_score', 0):.3f})")
        
        # Format web ingredients
        web_ingredient_list = []
        for i, ingredient in enumerate(web_ingredients[:10]):  # Top 10 web ingredients
            web_ingredient_list.append(f"{i+1}. {ingredient.get('ingredient_name', '')} (Source: {ingredient.get('source', 'Unknown')})")
        
        prompt = f"""
        You are a board-certified physician and clinical nutritionist with 20+ years of experience in personalized medicine and supplement protocols. 

        PATIENT CASE PRESENTATION:
        - Demographics: {demographics.get('age', 'Unknown')} year old {demographics.get('biological_sex', 'Unknown')}
        - Medical Conditions: {', '.join(medical_history.get('diagnoses', []))}
        - Flagged Biomarkers: {biomarker_text}
        - Headaches: {', '.join(headaches) if headaches else 'None reported'}
        - Chronic Pain: {', '.join(chronic_pain) if chronic_pain else 'None reported'}
        - Skin Health Issues: {', '.join(skin_health) if skin_health else 'None reported'}

        EVIDENCE-BASED INGREDIENT RECOMMENDATIONS FROM TWO SOURCES:

        SOURCE 1 - RAG-BASED RECOMMENDATIONS (from clinical database with hybrid scoring):
        {chr(10).join(rag_ingredient_list) if rag_ingredient_list else 'No RAG recommendations available'}

        SOURCE 2 - WEB-DISCOVERED RECOMMENDATIONS (from current scientific literature):
        {chr(10).join(web_ingredient_list) if web_ingredient_list else 'No web recommendations available'}

        CLINICAL TASK:
        As a physician, analyze this patient's complete health profile and both recommendation sources to create a final, evidence-based supplement protocol. 

        MEDICAL REASONING PROCESS:
        1. Review the patient's specific biomarkers and their clinical significance (high/low values)
        2. Consider their medical conditions and symptom burden
        3. Evaluate pain and skin health issues that need addressing
        4. Assess the quality and relevance of both recommendation sources
        5. Consider potential interactions and contraindications
        6. Prioritize ingredients with the strongest evidence for this specific patient profile
        7. Ensure the protocol addresses the most critical health needs first

        CLINICAL DECISION MAKING:
        - Prioritize ingredients that directly address flagged biomarkers
        - Consider ingredients that support the patient's specific medical conditions
        - Include ingredients that address pain and skin health issues
        - Balance evidence quality from both RAG database and current literature
        - Ensure safety and avoid potential interactions
        - Limit to the most clinically relevant recommendations

        Return ONLY a JSON response in this exact format:
        {{
            "final_recommendations": [
                {{
                    "ingredient_name": "Exact ingredient name",
                    "rank": 1,
                    "why": "Concise 1-2 line explanation of why this ingredient is necessary for this specific patient"
                }},
                {{
                    "ingredient_name": "Exact ingredient name",
                    "rank": 2,
                    "why": "Concise 1-2 line explanation of why this ingredient is necessary for this specific patient"
                }}
            ]
        }}

        For each ingredient, provide a concise "why" explanation (1-2 lines maximum) that:
        - References the patient's specific flagged biomarkers and their status (high/low)
        - Connects to their medical conditions and symptoms
        - Addresses their pain and skin health issues
        - Explains the clinical benefit for this particular patient
        - Shows evidence from either RAG database or web literature sources

        Provide 8-10 final recommendations ranked by clinical priority for this specific patient.
        Focus on ingredients that will have the greatest positive impact on their health outcomes.
        """
        
        return prompt

    def _run(self, user_profile: Union[str, dict, None] = None, rag_ingredients: Union[str, dict, None] = None, web_ingredients: Union[str, dict, None] = None) -> str:
        """Main execution method using medical LLM analysis."""
        try:
            # Get user_profile from parameter or kickoff_inputs
            if user_profile is None or user_profile == "":
                user_profile = self.kickoff_inputs.get("user_profile")
                if user_profile:
                    print("ℹ️ Using user_profile from kickoff_inputs")

            if not user_profile:
                return json.dumps({"error": "user_profile not provided"}, indent=2)

            # Parse inputs
            profile, rag_data, web_data = self._parse_inputs(user_profile, rag_ingredients, web_ingredients)

            # Extract ingredient lists
            rag_ingredient_list = rag_data if isinstance(rag_data, list) else rag_data.get("ranked_ingredients", [])
            web_ingredient_list = web_data.get("detailed_ingredients", []) if isinstance(web_data, dict) else web_data
            
            print(f"🔍 DEBUG: RAG data type: {type(rag_data)}, RAG ingredients count: {len(rag_ingredient_list)}")
            print(f"🔍 DEBUG: Web data type: {type(web_data)}, Web ingredients count: {len(web_ingredient_list)}")
            
            if len(rag_ingredient_list) == 0 and len(web_ingredient_list) == 0:
                print(f"❌ No ingredients found in either RAG or web data")
                return json.dumps({
                    "error": "No ingredients found in input data",
                    "final_recommendations": []
                }, indent=2)
            
            # Create medical analysis prompt
            prompt = self._create_medical_analysis_prompt(profile, rag_ingredient_list, web_ingredient_list)
            
            # Use CrewAI's LLM for medical analysis
            from crewai import LLM
            llm = LLM(model="vertex_ai/gemini-2.5-flash")

            print(f"🔍 Final Medical Analysis - Analyzing {len(rag_ingredient_list)} RAG ingredients and {len(web_ingredient_list)} web ingredients")

            llm_response = llm.call(prompt)

            # Extract text from LLM response (handle both list and string formats)
            if isinstance(llm_response, list) and len(llm_response) > 0:
                # CrewAI LLM returns list of message objects
                llm_output = llm_response[0].content if hasattr(llm_response[0], 'content') else str(llm_response[0])
            elif isinstance(llm_response, str):
                llm_output = llm_response
            else:
                llm_output = str(llm_response)

            print(f"🔍 DEBUG: LLM response type: {type(llm_response)}")
            print(f"🔍 DEBUG: LLM output length: {len(llm_output)}")
            print(f"🔍 DEBUG: LLM output preview: {llm_output[:500]}...")

            # Parse LLM response
            try:
                # Find JSON in the response
                start_idx = llm_output.find('{')
                end_idx = llm_output.rfind('}') + 1
                
                print(f"🔍 DEBUG: JSON start index: {start_idx}, end index: {end_idx}")
                
                if start_idx != -1 and end_idx != -1:
                    json_str = llm_output[start_idx:end_idx]
                    print(f"🔍 DEBUG: Extracted JSON string: {json_str[:200]}...")
                    
                    final_recommendations = json.loads(json_str)
                    
                    print(f"✅ Final medical analysis completed with {len(final_recommendations.get('final_recommendations', []))} recommendations")
                    return json.dumps(final_recommendations, indent=2)
                else:
                    print(f"❌ No JSON structure found in LLM response")
                    print(f"🔍 DEBUG: Full LLM response: {llm_output}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing LLM JSON response: {e}")
                print(f"🔍 DEBUG: JSON string that failed: {json_str if 'json_str' in locals() else 'N/A'}")
                return json.dumps({
                    "error": f"Failed to parse LLM response: {str(e)}",
                    "final_recommendations": []
                }, indent=2)
            
            return json.dumps({
                "error": "No valid JSON found in LLM response",
                "final_recommendations": []
            }, indent=2)
            
        except Exception as e:
            print(f"❌ Final medical analysis failed: {str(e)}")
            return json.dumps({
                "error": f"Final medical analysis failed: {str(e)}",
                "final_recommendations": []
            }, indent=2)
