"""
Core pipeline logic for Aether AI Engine.
Extracted from main.py to be reusable by both CLI and API.
"""

import json
from datetime import datetime
from typing import Dict, Any

from src.aether_2.crew import Aether2
from src.aether_2.utils.auth_setup import initialize_auth
from src.aether_2.utils.data_processing import clean_agent_output
from src.aether_2.utils.preprocessing import (
    evaluate_biomarkers,
    compile_user_profile,
    evaluate_focus_areas
)


def _transform_api_data_to_preprocessing_format(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform API data format to the format expected by preprocessing functions.

    API format:
    {
      "metadata": {...},
      "phase1_basic_intake": {...},
      "phase2_detailed_intake": {...},
      "latest_biomarker_results": {...}
    }

    Preprocessing format (matches what load_and_combine_inputs() returns):
    {
      "patient_form": {
        "patient_data": {
          "phase1_basic_intake": {...},
          "phase2_detailed_intake": {...}
        }
      },
      "blood_report": {...}
    }

    Args:
        patient_data: Data in API format

    Returns:
        Data in preprocessing format
    """
    return {
        "patient_form": {
            "patient_data": {
                "phase1_basic_intake": patient_data.get("phase1_basic_intake", {}),
                "phase2_detailed_intake": patient_data.get("phase2_detailed_intake", {})
            }
        },
        "blood_report": patient_data.get("latest_biomarker_results", {})
    }


def run_aether_pipeline(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete Aether AI pipeline.
    
    Args:
        patient_data: Dictionary containing patient data with structure:
            {
                "phase1_basic_intake": {...},
                "phase2_blood_report": {...},
                "metadata": {...}
            }
    
    Returns:
        Dictionary with:
            {
                "status": "success" | "error",
                "user_id": str,
                "protocol": dict,  # Cleaned final protocol JSON
                "preprocessing_outputs": {
                    "biomarker_results": dict,
                    "user_profile": dict,
                    "focus_areas": dict
                },
                "error": str (only if status == "error")
            }
    
    Raises:
        Exception: If pipeline execution fails
    """
    start_time = datetime.now()
    
    # Initialize authentication
    initialize_auth()
    
    # Extract user_id
    user_id = patient_data.get("metadata", {}).get("phase_status", {}).get("user_id", "unknown_user")
    
    try:
        # ========== PREPROCESSING PIPELINE (Agents 1-3) ==========
        print(f"\n🔧 Running preprocessing pipeline for user: {user_id}")

        # Transform API data format to preprocessing format
        preprocessing_data = _transform_api_data_to_preprocessing_format(patient_data)
        print("✅ Data transformation complete")

        # Step 1: Evaluate biomarkers (Agent 1)
        biomarker_results = evaluate_biomarkers(preprocessing_data)
        print("✅ Biomarker evaluation complete")

        # Step 2: Compile user profile (Agent 2)
        user_profile = compile_user_profile(preprocessing_data, biomarker_results)
        print("✅ User profile compilation complete")

        # Step 3: Evaluate focus areas (Agent 3)
        focus_areas_results = evaluate_focus_areas(preprocessing_data)
        print("✅ Focus areas evaluation complete")
        
        # ========== CREWAI EXECUTION (Agents 4-7) ==========
        print("\n🤖 Starting CrewAI execution...")
        
        # Set kickoff inputs for tools to access (class variable)
        Aether2.kickoff_inputs = {
            "user_profile": user_profile.model_dump_json(),
            "focus_areas": focus_areas_results["markdown_output"]
        }
        
        # Run crew with inputs
        result = Aether2().crew().kickoff(
            inputs={
                "user_profile": user_profile.model_dump_json(),
                "focus_areas": focus_areas_results["markdown_output"]
            }
        )
        print("✅ CrewAI execution completed successfully")
        
        # ========== POST-PROCESSING ==========
        print("\n🔄 Post-processing outputs...")
        
        # Extract and clean the final protocol
        final_protocol = None
        if hasattr(result, "tasks_output"):
            for task_output in result.tasks_output:
                # Look for the final compilation task
                if task_output.name == "compile_final_supplement_recommendations":
                    # Get the raw content
                    content = ""
                    if getattr(task_output, "tool_output", None):
                        content = str(task_output.tool_output)
                    elif getattr(task_output, "output", None):
                        content = str(task_output.output)
                    elif getattr(task_output, "raw", None):
                        content = str(task_output.raw)
                    
                    # Clean the output
                    cleaned_content = clean_agent_output(content, task_output.name)
                    
                    # Parse to JSON
                    try:
                        final_protocol = json.loads(cleaned_content)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Warning: Could not parse final protocol as JSON: {e}")
                        final_protocol = {"raw_output": cleaned_content}
                    
                    break
        
        if final_protocol is None:
            raise Exception("Could not extract final protocol from CrewAI output")
        
        # Calculate execution time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Pipeline completed successfully in {duration:.2f} seconds")
        
        # Return results
        return {
            "status": "success",
            "user_id": user_id,
            "protocol": final_protocol,
            "preprocessing_outputs": {
                "biomarker_results": {
                    "flagged_biomarkers": biomarker_results.get("flagged_biomarkers", []),
                    "summary": biomarker_results.get("summary", ""),
                    "markdown_output": biomarker_results.get("markdown_output", "")
                },
                "user_profile": json.loads(user_profile.model_dump_json()),
                "focus_areas": {
                    "scores": focus_areas_results.get("scores", {}),
                    "markdown_output": focus_areas_results.get("markdown_output", "")
                }
            },
            "execution_time_seconds": duration
        }
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"❌ Pipeline failed after {duration:.2f} seconds: {str(e)}")
        
        return {
            "status": "error",
            "user_id": user_id,
            "error": str(e),
            "execution_time_seconds": duration
        }

