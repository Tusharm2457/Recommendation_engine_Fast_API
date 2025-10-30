from crewai.tools import BaseTool
from typing import Type, Union, List, Dict, Any
from pydantic import BaseModel, Field
import json
import os
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
import re

# Load environment variables
load_dotenv()

class WebIngredientDiscoveryInput(BaseModel):
    user_profile: Union[str, dict, None] = Field(
        default=None,
        description="JSON string OR dict containing the user profile from Agent 2. If not provided, will use kickoff inputs."
    )

class WebIngredientDiscoveryTool(BaseTool):
    name: str = "web_ingredient_discovery"
    description: str = (
        "Discovers new and trending supplement ingredients from credible scientific sources "
        "like PubMed, NIH, Examine.com, and other authoritative health databases. Searches "
        "for evidence-based ingredients that address the user's specific health conditions "
        "and flagged biomarkers."
    )
    args_schema: Type[BaseModel] = WebIngredientDiscoveryInput
    kickoff_inputs: dict = {}

    def _get_search_wrapper(self):
        """Get Google Search wrapper instance"""
        return GoogleSerperAPIWrapper()

    def _create_discovery_queries(self, user_profile: Dict[str, Any]) -> List[str]:
        """Create targeted queries for ingredient discovery from credible sources"""
        try:
            queries = []
            
            # Extract user context
            demographics = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("demographics", {})
            medical_history = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_history", {})
            flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
            
            # Extract pain and skin health information
            pain_skin_health = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("pain_and_skin_health", {})
            headaches = pain_skin_health.get("headaches", [])
            chronic_pain = pain_skin_health.get("chronic_pain", [])
            skin_health = pain_skin_health.get("skin_health", [])
            
            age = demographics.get("age", "")
            gender = demographics.get("biological_sex", "")
            diagnoses = medical_history.get("diagnoses", [])
            biomarker_names = [b.get("name", "") for b in flagged_biomarkers]
            
            # Query 1: Biomarker-specific discovery (including high/low status)
            for biomarker in flagged_biomarkers[:5]:  # Top 3 biomarkers
                biomarker_name = biomarker.get("name", "")
                biomarker_status = biomarker.get("status", "").lower()  # high/low
                
                if biomarker_name and biomarker_status:
                    queries.append(f"site:pubmed.ncbi.nlm.nih.gov nutritional supplements nutrients for {biomarker_status} {biomarker_name} research")
                    queries.append(f"site:examine.com vitamins minerals herbs for {biomarker_status} {biomarker_name} biomarker")
                    
            # Query 2: Condition-specific discovery (nutrients only, no branded products)
            for condition in diagnoses:  # Top 2 conditions
                queries.append(f"site:pubmed.ncbi.nlm.nih.gov {condition} nutritional supplements vitamins minerals research")
                queries.append(f"site:examine.com {condition} natural nutrients herbs vitamins research")
                queries.append(f"site:nccih.nih.gov {condition} dietary supplements nutrients studies")
            
            # Query 3: Pain and skin health specific discovery
            if headaches:
                for headache_type in headaches[:2]:  # Top 2 headache types
                    queries.append(f"site:pubmed.ncbi.nlm.nih.gov {headache_type} headaches nutritional supplements vitamins minerals research")
                    queries.append(f"site:examine.com {headache_type} headaches natural nutrients herbs research")
            
            if chronic_pain:
                for pain_type in chronic_pain[:2]:  # Top 2 pain types
                    queries.append(f"site:pubmed.ncbi.nlm.nih.gov {pain_type} chronic pain nutritional supplements vitamins minerals research")
                    queries.append(f"site:examine.com {pain_type} chronic pain natural nutrients herbs research")
            
            if skin_health:
                for skin_issue in skin_health[:2]:  # Top 2 skin issues
                    queries.append(f"site:pubmed.ncbi.nlm.nih.gov {skin_issue} skin health nutritional supplements vitamins minerals research")
                    queries.append(f"site:examine.com {skin_issue} skin health natural nutrients herbs research")
            
            print(f"🔍 Created {len(queries)} discovery queries targeting credible sources")
            return queries
            
        except Exception as e:
            print(f"❌ Error creating discovery queries: {str(e)}")
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

    def _extract_ingredients_from_results(self, search_results: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract ingredients from search results using LLM analysis"""
        try:
            # Combine all search results into one text
            combined_text = ""
            for result in search_results:
                if result["status"] == "success":
                    combined_text += f"\n\n--- Search Query: {result.get('query', '')} ---\n"
                    combined_text += result["results"]
            
            print(f"🔍 DEBUG: Combined text length: {len(combined_text)} characters")
            print(f"🔍 DEBUG: Combined text preview: {combined_text[:200]}...")
            
            # Extract patient context for LLM prompt
            flagged_biomarkers = user_profile.get("flagged_biomarkers", [])
            diagnoses = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_history", {}).get("diagnoses", [])
            
            # Extract pain and skin health information
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
            
            # Create pain and skin health context
            pain_skin_context = []
            if headaches:
                pain_skin_context.append(f"headaches: {', '.join(headaches)}")
            if chronic_pain:
                pain_skin_context.append(f"chronic pain: {', '.join(chronic_pain)}")
            if skin_health:
                pain_skin_context.append(f"skin health: {', '.join(skin_health)}")
            
            biomarker_text = ", ".join(biomarker_context) if biomarker_context else "general health"
            condition_text = ", ".join(diagnoses) if diagnoses else "general wellness"
            pain_skin_text = ", ".join(pain_skin_context) if pain_skin_context else "no specific pain/skin issues"
            
            # Create LLM prompt
            prompt = f"""
            Analyze the following scientific research text and extract supplement ingredients (nutrients, vitamins, minerals, herbs) that are mentioned.
            
            Patient Context:
            - Flagged Biomarkers: {biomarker_text}
            - Medical Conditions: {condition_text}
            - Pain & Skin Health: {pain_skin_text}
            
            Research Text:
            {combined_text}
            
            Extract ONLY actual supplement ingredients (nutrients, vitamins, minerals, herbs, amino acids, etc.).
            Do NOT include:
            - Brand names or product names
            - General terms like "supplements", "medications", "treatments"
            - Study-related words like "clinical", "trial", "research", "study"
            - Dosage information or forms like "mg", "capsule", "tablet"
            
            For each ingredient, provide:
            1. The exact ingredient name as mentioned
            2. A brief description of its benefits/context from the text
            3. The source where it was found (PubMed, Examine.com, NIH, etc.)
            
            Return ONLY a JSON array in this format:
            [
                {{
                    "name": "Ingredient Name",
                    "description": "Brief context from the text",
                    "source": "PubMed"
                }}
            ]
            
            Focus on ingredients that are relevant to the patient's biomarkers and conditions.
            Maximum 15 ingredients.
            """
            
            # Use CrewAI's LLM to extract ingredients
            from crewai import LLM
            llm = LLM(model="vertex_ai/gemini-2.5-flash")

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
            print(f"🔍 DEBUG: LLM output preview: {llm_output[:200]}...")

            # Parse LLM response
            try:
                # Find JSON array in the response
                start_idx = llm_output.find('[')
                end_idx = llm_output.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = llm_output[start_idx:end_idx]
                    ingredients = json.loads(json_str)
                    
                    # Validate and structure the results
                    discovered_ingredients = []
                    for ingredient in ingredients:
                        if isinstance(ingredient, dict) and "name" in ingredient:
                            name = ingredient["name"].strip()
                            description = ingredient.get("description", "").strip()
                            source = ingredient.get("source", "Web Research")
                            
                            # Basic validation
                            if len(name) > 2 and len(name) < 100:
                                discovered_ingredients.append({
                                    "ingredient_name": name,
                                    "description": description,
                                    "source": source
                                })
                    
                    print(f"✅ LLM extracted {len(discovered_ingredients)} ingredients from research text")
                    return discovered_ingredients
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing LLM JSON response: {e}")
                return []
            
            return []
            
        except Exception as e:
            print(f"❌ Error extracting ingredients: {str(e)}")
            return []



    def _run(self, user_profile: Union[str, dict, None] = None) -> str:
        """Main discovery function using Google Search on credible sources"""
        try:
            # Get user_profile from parameter or kickoff_inputs
            if user_profile is None or user_profile == "":
                user_profile = self.kickoff_inputs.get("user_profile")
                if user_profile:
                    print("ℹ️ Using user_profile from kickoff_inputs")

            if not user_profile:
                return json.dumps({"error": "user_profile not provided"}, indent=2)

            # Parse input
            if isinstance(user_profile, str):
                user_profile_parsed = json.loads(user_profile)
            else:
                user_profile_parsed = user_profile
            
            print(f"🔍 Web Ingredient Discovery - Processing user profile")
            print(f"  - Patient data present: {'patient_data' in user_profile_parsed}")
            print(f"  - Flagged biomarkers: {len(user_profile_parsed.get('flagged_biomarkers', []))}")
            
            # Create discovery queries targeting credible sources
            discovery_queries = self._create_discovery_queries(user_profile_parsed)
            
            if not discovery_queries:
                return json.dumps([], indent=2)
            
            # Perform searches
            print(f"🔍 Performing {len(discovery_queries)} searches on credible sources...")
            search_results = []
            for i, query in enumerate(discovery_queries):
                print(f"  Search {i+1}/{len(discovery_queries)}: {query[:60]}...")
                result = self._perform_search(query)
                search_results.append(result)
            
            # Extract ingredients from search results
            discovered_ingredients = self._extract_ingredients_from_results(search_results, user_profile_parsed)
            
            # Create simple ingredient list
            simple_ingredient_list = []
            for ingredient in discovered_ingredients:
                simple_ingredient_list.append({
                    "ingredient_name": ingredient["ingredient_name"],
                    "source": ingredient["source"]
                })
            
            # Create response
            response = {
                "status": "success",
                "message": f"Discovered {len(discovered_ingredients)} ingredients from credible scientific sources",
                "searches_performed": len(discovery_queries),
                "sources_searched": ["PubMed", "Examine.com", "NIH", "NCCIH"],
                "ingredient_list": simple_ingredient_list,  # Simple list
                "detailed_ingredients": discovered_ingredients  # Full details
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            print(f"❌ Web ingredient discovery failed: {str(e)}")
            error_response = {
                "status": "error",
                "message": f"Web ingredient discovery failed: {str(e)}",
                "discovered_ingredients": []
            }
            return json.dumps(error_response, indent=2)
