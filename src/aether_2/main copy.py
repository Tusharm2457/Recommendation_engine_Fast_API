import json
import os
import sys
from dotenv import load_dotenv
from aether_2.crew import Aether2

load_dotenv()

def load_and_combine_inputs(patient_path, blood_report_path):
    """Load patient details and blood report, then combine them into the expected format."""
    # Load patient details
    if patient_path.endswith(".json"):
        with open(patient_path, "r") as f:
            patient_data = json.load(f)
    else:
        raise ValueError("Patient file must be .json")
    
    # Load blood report
    if blood_report_path.endswith(".json"):
        with open(blood_report_path, "r") as f:
            blood_report_data = json.load(f)
    else:
        raise ValueError("Blood report file must be .json")
    
    # Combine into expected format
    combined_data = {
        "patient_form": patient_data,
        "blood_report": blood_report_data
    }
    
    return combined_data  # return dict instead of list



def run(patient_path="inputs/patient_details.json", blood_report_path="inputs/blood_report.json"):
    """Run the crew on each combined patient data (patient details + blood report)."""
    patient_data = load_and_combine_inputs(patient_path, blood_report_path)

    print(f"\n=== Running pipeline for patient ===")

    try:
        # 🔹 FIX: Serialize dict → JSON string and use correct arg name
        result = Aether2().crew().kickoff(
            inputs={
                "patient_and_blood_data": json.dumps(patient_data)  
            }
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Save results
    out_dir = os.path.join("outputs", f"patient_1")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Save full crew run
    with open(os.path.join(out_dir, "crew_final.json"), "w") as f:
        json.dump(result.dict(), f, indent=2)   # <-- serialize properly

    # 2. Save per-agent outputs (only agents 1 and 2 enabled)
    name_map = {
        "evaluate_inputs": "biomarker_status.md",  # Agent 1: Biomarker evaluation
        "compile_user_profile": "user_profile.json",  # Agent 2: User profile compiler
        "evaluate_focus_areas": "focus_areas.md",  # Agent 3: Focus areas
        "discover_ingredients_web": "discovered_ingredients_web.json",  # Agent 4: Web ingredient discovery
        # Temporarily disabled for testing
        # "rank_ingredients_rag": "ranked_ingredients_rag.json",  # Agent 4: RAG ingredient ranker
        # "validate_ingredients_google": "validated_ingredients_google.json",  # Agent 5: Google Search validator
        # "rank_ingredients": "ranked_ingredients.json",
        # "generate_supplement_recommendations": "supplement_recommendations.json"
    }

    if hasattr(result, "tasks_output"):
        for task_output in result.tasks_output:
            filename = name_map.get(task_output.name, f"{task_output.name}.md")
            filepath = os.path.join(out_dir, filename)

            # DEBUG
            print(f"\n=== Saving task {task_output.name} ===")
            print(f"  Agent: {task_output.agent}")
            print(f"  Raw: {getattr(task_output, 'raw', None)[:100]}...")  # first 100 chars

            with open(filepath, "w") as f:
                if getattr(task_output, "tool_output", None):
                    f.write(str(task_output.tool_output))
                elif getattr(task_output, "output", None):
                    f.write(str(task_output.output))
                elif getattr(task_output, "raw", None):   # 🔹 add this fallback
                    f.write(str(task_output.raw))
                else:
                    f.write("No output captured")

            print(f"✅ Saved task output: {filepath}")
    
    # 3. User profile is now created by Agent 2 (compile_user_profile task)
    print("\n✅ User profile created by Agent 2 (compile_user_profile task)")


if __name__ == "__main__":
    run(
        patient_path="inputs/patient_details.json", 
        blood_report_path="inputs/blood_report.json"
    )
