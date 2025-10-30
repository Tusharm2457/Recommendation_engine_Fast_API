"""
Preprocessing pipeline for rule-based tasks.
Migrated from CrewAI agents to regular Python functions for performance optimization.
"""

import json
from typing import Dict, Any
from src.aether_2.tools.biomarker_evaluation import BiomarkerEvaluationTool
from src.aether_2.tools.user_profile_compiler import UserProfileCompilerTool
from src.aether_2.tools.focus_areas_generator import EvaluateFocusAreasTool
from src.aether_2.models import UserProfile, FocusAreaScores


def evaluate_biomarkers(patient_and_blood_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate biomarkers using rule-based threshold checking.
    
    Args:
        patient_and_blood_data: Dict with keys 'patient_form' and 'blood_report'
    
    Returns:
        Dict with:
            - flagged_biomarkers: List of flagged biomarkers
            - summary: Summary statistics
            - markdown_output: Formatted markdown text for file output
    """
    try:
        tool = BiomarkerEvaluationTool()
        result_json = tool._run(patient_and_blood_data=patient_and_blood_data)
        result = json.loads(result_json)
        
        # Create markdown output
        markdown_lines = ["# Biomarker Evaluation Results\n"]
        
        if "flagged_biomarkers" in result and result["flagged_biomarkers"]:
            markdown_lines.append("## Flagged Biomarkers\n")
            for biomarker in result["flagged_biomarkers"]:
                markdown_lines.append(
                    f"- **{biomarker['name']}**: {biomarker['value']} {biomarker['unit']} "
                    f"({biomarker['category']})"
                )
            markdown_lines.append("")
        
        if "summary" in result:
            summary = result["summary"]
            markdown_lines.append("## Summary\n")
            markdown_lines.append(f"- Total biomarkers evaluated: {summary.get('total_biomarkers_evaluated', 0)}")
            markdown_lines.append(f"- Total flagged: {summary.get('total_flagged', 0)}")
            
            if "category_summary" in summary:
                cat_sum = summary["category_summary"]
                markdown_lines.append(f"- Healthy markers: {cat_sum.get('healthy_markers', 0)}")
                markdown_lines.append(f"- Low markers: {cat_sum.get('low_markers', 0)}")
                markdown_lines.append(f"- High markers: {cat_sum.get('high_markers', 0)}")
        
        return {
            "flagged_biomarkers": result.get("flagged_biomarkers", []),
            "summary": result.get("summary", {}),
            "markdown_output": "\n".join(markdown_lines)
        }
        
    except Exception as e:
        print(f"❌ Biomarker evaluation failed: {str(e)}")
        return {
            "flagged_biomarkers": [],
            "summary": {},
            "markdown_output": f"# Error\n\nBiomarker evaluation failed: {str(e)}"
        }


def compile_user_profile(
    patient_and_blood_data: Dict[str, Any],
    biomarker_results: Dict[str, Any]
) -> UserProfile:
    """
    Compile user profile by combining patient data with biomarker results.
    
    Args:
        patient_and_blood_data: Dict with keys 'patient_form' and 'blood_report'
        biomarker_results: Output from evaluate_biomarkers()
    
    Returns:
        UserProfile: Pydantic-validated user profile
    """
    try:
        tool = UserProfileCompilerTool()
        result_json = tool._run(
            patient_and_blood_data=patient_and_blood_data,
            flagged_biomarkers=biomarker_results
        )
        result = json.loads(result_json)
        
        # Validate with Pydantic
        user_profile = UserProfile(**result)
        return user_profile
        
    except Exception as e:
        print(f"❌ User profile compilation failed: {str(e)}")
        raise


def evaluate_focus_areas(patient_and_blood_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate focus areas using rule-based scoring.
    
    Args:
        patient_and_blood_data: Dict with keys 'patient_form' and 'blood_report'
    
    Returns:
        Dict with:
            - scores: FocusAreaScores (Pydantic model)
            - markdown_output: Formatted markdown text for file output
    """
    try:
        tool = EvaluateFocusAreasTool()
        markdown_output = tool._run(patient_and_blood_data=patient_and_blood_data)
        
        # Parse the markdown output to extract scores
        scores_dict = {}
        focus_area_codes = ["CM", "COG", "DTX", "IMM", "MITO", "SKN", "STR", "HRM", "GA"]
        
        for line in markdown_output.split("\n"):
            for code in focus_area_codes:
                if f"({code}):" in line:
                    # Extract score from line like "Cardiometabolic & Metabolic Health (CM): 0.50"
                    try:
                        score_str = line.split(":")[-1].strip()
                        scores_dict[code] = float(score_str)
                    except (ValueError, IndexError):
                        scores_dict[code] = 0.0
                    break
        
        # Ensure all focus areas have a score (default to 0.0 if missing)
        for code in focus_area_codes:
            if code not in scores_dict:
                scores_dict[code] = 0.0
        
        # Validate with Pydantic
        focus_area_scores = FocusAreaScores(**scores_dict)
        
        return {
            "scores": focus_area_scores,
            "markdown_output": markdown_output
        }
        
    except Exception as e:
        print(f"❌ Focus areas evaluation failed: {str(e)}")
        raise

