from crewai.tools import BaseTool
from typing import Type, Union, List, Dict, Any
from pydantic import BaseModel, Field
import json

class FinalSupplementCompilerInput(BaseModel):
    supplement_recommendations: Union[str, dict] = Field(
        ..., description="Supplement recommendations JSON from supplement_recommender agent"
    )
    focus_areas: Union[str, dict] = Field(
        ..., description="Focus areas JSON from focus_areas_generator agent"
    )

class FinalSupplementCompilerTool(BaseTool):
    name: str = "compile_final_supplement_recommendations"
    description: str = (
        "Final compiler that takes supplement recommendations and focus areas to create "
        "complete supplement recommendations with dosages, frequencies, and focus area associations."
    )
    args_schema: Type[BaseModel] = FinalSupplementCompilerInput

    # Focus area mappings
    FOCUS_AREA_MAPPINGS: Dict[str, str] = {
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


    def _parse_inputs(self, supplement_recommendations: Union[str, dict], focus_areas: Union[str, dict]) -> tuple:
        """Parse and validate all input data."""
        # Parse supplement recommendations
        if isinstance(supplement_recommendations, str):
            supp_data = json.loads(supplement_recommendations)
        else:
            supp_data = supplement_recommendations

        # Parse focus areas
        if isinstance(focus_areas, str):
            focus_data = json.loads(focus_areas)
        else:
            focus_data = focus_areas

        return supp_data, focus_data

    def _extract_focus_areas_from_text(self, focus_areas_text: str) -> List[Dict[str, Any]]:
        """Extract focus areas from the text format"""
        focus_areas = []
        lines = focus_areas_text.strip().split('\n')
        
        for line in lines:
            if ':' in line and '(' in line and ')' in line:
                # Parse format: "Focus Area Name (CODE): score"
                try:
                    # Split by colon to separate name+code from score
                    parts = line.split(':')
                    if len(parts) == 2:
                        name_code_part = parts[0].strip()
                        score_part = parts[1].strip()
                        
                        # Extract code from parentheses
                        if '(' in name_code_part and ')' in name_code_part:
                            start = name_code_part.rfind('(')
                            end = name_code_part.rfind(')')
                            if start != -1 and end != -1:
                                code = name_code_part[start+1:end].strip()
                                name = name_code_part[:start].strip()
                                
                                try:
                                    score = float(score_part)
                                    focus_areas.append({
                                        "code": code,
                                        "name": name,
                                        "score": score
                                    })
                                except ValueError:
                                    continue
                except Exception:
                    continue
        
        # Sort by score (highest first)
        focus_areas.sort(key=lambda x: x["score"], reverse=True)
        return focus_areas


    def _create_llm_compilation_prompt(self, supplement_recommendations: List[Dict], focus_areas: List[Dict]) -> str:
        """Create LLM prompt for generating complete supplement protocols"""
        
        # Format supplement recommendations
        supp_list = []
        for i, rec in enumerate(supplement_recommendations):
            supp_list.append(f"{i+1}. {rec.get('ingredient_name', '')} - {rec.get('why', '')}")
        
        # Format focus areas
        focus_list = []
        for area in focus_areas:
            focus_list.append(f"- {area.get('name', '')} ({area.get('code', '')}): {area.get('score', 0):.2f}")
        
        prompt = f"""
        You are a clinical pharmacist and supplement protocol specialist. Create complete supplement protocols with appropriate dosages, frequencies, and focus area associations.

        SUPPLEMENT RECOMMENDATIONS TO COMPILE:
        {chr(10).join(supp_list)}

        PATIENT'S FOCUS AREAS (Health Priorities):
        {chr(10).join(focus_list)}

        TASK:
        For each supplement recommendation, provide:
        1. Appropriate clinical dosage with units (mg, mcg, IU, etc.)
        2. Optimal frequency and timing
        3. Relevant focus area codes (1-2 most relevant)
        4. Keep the original "why" reasoning

        DOSAGE GUIDELINES:
        - Use evidence-based clinical dosages
        - Consider safety and tolerability
        - Include appropriate units (mg, mcg, IU, CFU, etc.)
        - Specify timing (with meals, empty stomach, bedtime, etc.)

        FOCUS AREA ASSOCIATIONS:
        - CM: Cardiometabolic & Metabolic Health
        - COG: Cognitive & Mental Health
        - DTX: Detoxification & Biotransformation
        - IMM: Immune Function & Inflammation
        - MITO: Mitochondrial & Energy Metabolism
        - SKN: Skin & Barrier Function
        - STR: Stress-Axis & Nervous System Resilience
        - HRM: Hormonal Health (Transport)
        - GA: Gut Health and assimilation

        Return ONLY a JSON response in this exact format:
        {{
            "supplement_recommendations": [
                {{
                    "ingredient_name": "Exact ingredient name",
                    "recommended_dosage": "Clinical dosage with units",
                    "frequency": "Optimal timing and frequency",
                    "focus_area": ["CODE1", "CODE2"],
                    "why": "Original patient-specific reasoning"
                }}
            ]
        }}

        Provide complete protocols for all {len(supplement_recommendations)} supplements.
        """
        
        return prompt

    def _run(self, supplement_recommendations: Union[str, dict], focus_areas: Union[str, dict]) -> str:
        """Main execution method using LLM for complete supplement protocol compilation"""
        try:
            # Parse inputs
            supp_data, focus_data = self._parse_inputs(supplement_recommendations, focus_areas)
            
            # Extract supplement recommendations
            final_recommendations = supp_data.get("final_recommendations", [])
            
            # Extract focus areas (handle both text and structured formats)
            focus_areas_list = []
            if isinstance(focus_data, str):
                focus_areas_list = self._extract_focus_areas_from_text(focus_data)
            elif isinstance(focus_data, list):
                focus_areas_list = focus_data
            elif isinstance(focus_data, dict):
                # Try to extract from common dict structures
                if "focus_areas" in focus_data:
                    focus_areas_list = focus_data["focus_areas"]
                else:
                    # Convert dict to list format
                    focus_areas_list = [{"code": k, "name": v, "score": 0.5} for k, v in focus_data.items()]
            
            print(f"🔍 Final Compiler - Processing {len(final_recommendations)} recommendations with {len(focus_areas_list)} focus areas")
            
            if not final_recommendations:
                return json.dumps({
                    "error": "No supplement recommendations found",
                    "supplement_recommendations": []
                }, indent=2)
            
            # Create LLM compilation prompt
            prompt = self._create_llm_compilation_prompt(final_recommendations, focus_areas_list)
            
            # Use CrewAI's LLM for compilation
            from crewai import LLM
            llm = LLM(model="azure/gpt-4o")
            
            print(f"🔍 Final Compiler - Generating complete supplement protocols with LLM")
            
            llm_output = llm.call(prompt)
            print(f"🔍 DEBUG: LLM response length: {len(llm_output)}")
            
            # Parse LLM response
            try:
                # Find JSON in the response
                start_idx = llm_output.find('{')
                end_idx = llm_output.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = llm_output[start_idx:end_idx]
                    compiled_recommendations = json.loads(json_str)
                    
                    print(f"✅ Final compilation completed with {len(compiled_recommendations.get('supplement_recommendations', []))} complete protocols")
                    return json.dumps(compiled_recommendations, indent=2)
                else:
                    print(f"❌ No JSON structure found in LLM response")
                    print(f"🔍 DEBUG: Full LLM response: {llm_output}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing LLM JSON response: {e}")
                print(f"🔍 DEBUG: JSON string that failed: {json_str if 'json_str' in locals() else 'N/A'}")
                return json.dumps({
                    "error": f"Failed to parse LLM response: {str(e)}",
                    "supplement_recommendations": []
                }, indent=2)
            
            return json.dumps({
                "error": "No valid JSON found in LLM response",
                "supplement_recommendations": []
            }, indent=2)
            
        except Exception as e:
            print(f"❌ Final compilation failed: {str(e)}")
            return json.dumps({
                "error": f"Final compilation failed: {str(e)}",
                "supplement_recommendations": []
            }, indent=2)
