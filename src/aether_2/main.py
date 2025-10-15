import json
import os
import sys
from dotenv import load_dotenv
import pandas as pd
from google.cloud import secretmanager
# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
PROJECT_ID = "singular-object-456719-i6"
SECRET_1 = "SERPER_API_KEY" 
SECRET_2 = "Vertex_API_Key" 
 
client = secretmanager.SecretManagerServiceClient()

from src.aether_2.crew import Aether2

# Access the secret
secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_1}/versions/latest"
response = client.access_secret_version(request={"name": secret_path})
secret_value = response.payload.data.decode("UTF-8")

# Set the secret value as an environment variable
os.environ["SERPER_API_KEY"] = secret_value

# Access the secret
secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_2}/versions/latest"
response = client.access_secret_version(request={"name": secret_path})
secret_value = response.payload.data.decode("UTF-8")

# Set the secret value as an environment variable
os.environ["GEMINI_API_KEY"] = secret_value

load_dotenv()

def load_and_combine_inputs(input_path):
    """Load combined patient data and extract patient details and blood report."""
    # Load the input file
    if input_path.endswith(".json"):
        with open(input_path, "r") as f:
            data = json.load(f)
    else:
        raise ValueError("Input file must be .json")
    
    # Extract data from new combined format
    user_data = data[0]["user_full_data"]
    patient_data = user_data["patient_data"]
    blood_data = user_data["latest_biomarker_results"]
    
    # Wrap patient_data back into the expected structure
    patient_data_wrapped = {
        "patient_data": patient_data
    }
    
    # Combine into expected format
    combined_data = {
        "patient_form": patient_data_wrapped,
        "blood_report": blood_data
    }
    
    return combined_data


def create_nested_excel_data(data, parent_paths=[], skip_phase_prefix=True):
    """Create nested structure for Excel export with separate columns for each hierarchy level"""
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            # Create readable key
            readable_key = k.replace('_', ' ').title()
            
            # Skip phase prefixes (phase1_basic_intake, phase2_detailed_intake)
            if skip_phase_prefix and readable_key in ['Phase1 Basic Intake', 'Phase2 Detailed Intake']:
                current_paths = parent_paths.copy()
            else:
                current_paths = parent_paths + [readable_key]
            
            if isinstance(v, dict):
                items.extend(create_nested_excel_data(v, current_paths, skip_phase_prefix))
            elif isinstance(v, list):
                # Handle lists of dictionaries (like medications)
                if v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            for sub_k, sub_v in item.items():
                                sub_readable_key = sub_k.replace('_', ' ').title()
                                item_paths = current_paths + [f"Item {i+1}", sub_readable_key]
                                # Pad with empty strings to ensure consistent column count
                                while len(item_paths) < 4:  # Adjust max depth as needed
                                    item_paths.append('')
                                item_paths.append(sub_v)  # Add the value as the last column
                                items.append(tuple(item_paths))
                        else:
                            item_paths = current_paths + [f"Item {i+1}"]
                            while len(item_paths) < 4:
                                item_paths.append('')
                            item_paths.append(item)
                            items.append(tuple(item_paths))
                else:
                    # Convert simple lists to string representation
                    list_value = ', '.join(map(str, v)) if v else ''
                    item_paths = current_paths.copy()
                    while len(item_paths) < 4:
                        item_paths.append('')
                    item_paths.append(list_value)
                    items.append(tuple(item_paths))
            else:
                item_paths = current_paths.copy()
                while len(item_paths) < 4:  # Ensure consistent column count
                    item_paths.append('')
                item_paths.append(v)
                items.append(tuple(item_paths))
    return items


def load_final_recommendations(output_dir):
    """Load the final supplement recommendations JSON"""
    recommendations_file = os.path.join(output_dir, "final_supplement_recommendations.json")
    if os.path.exists(recommendations_file):
        with open(recommendations_file, 'r') as f:
            content = f.read()
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
    return None


def create_excel_report(original_data, output_dir, user_id):
    """Create Excel file with 3 sheets: patient_data, biomarkers, recommendations"""
    excel_file = os.path.join(output_dir, f"{user_id}.xlsx")
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Sheet 1: Patient Data (multi-column hierarchical format)
        patient_data = original_data.get('patient_data', {})
        nested_patient_data = create_nested_excel_data(patient_data)
        patient_df = pd.DataFrame(nested_patient_data, columns=['Category', 'Subcategory', 'Field', 'Detail', 'Value'])
        patient_df.to_excel(writer, sheet_name='Patient_Data', index=False)
        
        # Sheet 2: Biomarkers (vertical format)
        biomarkers = original_data.get('latest_biomarker_results', {})
        biomarkers_df = pd.DataFrame(list(biomarkers.items()), columns=['Biomarker', 'Value'])
        biomarkers_df.to_excel(writer, sheet_name='Biomarkers', index=False)
        
        # Sheet 3: Recommendations (horizontal format)
        recommendations = load_final_recommendations(output_dir)
        if recommendations and 'supplement_recommendations' in recommendations:
            rec_data = []
            for rec in recommendations['supplement_recommendations']:
                rec_data.append({
                    'ingredient_name': rec.get('ingredient_name', ''),
                    'recommended_dosage': rec.get('recommended_dosage', ''),
                    'frequency': rec.get('frequency', ''),
                    'focus_area': ', '.join(rec.get('focus_area', [])) if isinstance(rec.get('focus_area'), list) else rec.get('focus_area', ''),
                    'why': rec.get('why', '')
                })
            recommendations_df = pd.DataFrame(rec_data)
            recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
        else:
            # Create empty sheet if no recommendations found
            empty_df = pd.DataFrame(columns=['ingredient_name', 'recommended_dosage', 'frequency', 'focus_area', 'why'])
            empty_df.to_excel(writer, sheet_name='Recommendations', index=False)
    
    print(f"✅ Excel report created: {excel_file}")


def run(input_path="inputs/combined_data.json"):
    """Run the crew on combined patient data (patient details + blood report)."""
    # Load the original input data for Excel export
    with open(input_path, "r") as f:
        original_input_data = json.load(f)
    
    patient_data = load_and_combine_inputs(input_path)

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

    # 2. Save per-agent outputs (7 agents enabled: biomarker evaluation, user profile, focus areas, web discovery, RAG ranking, medical recommendations, final protocol compilation)
    name_map = {
        "evaluate_inputs": "biomarker_status.md",  # Agent 1: Biomarker evaluation
        "compile_user_profile": "user_profile.json",  # Agent 2: User profile compiler
        "evaluate_focus_areas": "focus_areas.md",  # Agent 3: Focus areas
        "discover_ingredients_web": "discovered_ingredients_web.json",  # Agent 4: Web ingredient discovery
        "rank_ingredients_rag": "ranked_ingredients_rag.json",  # Agent 5: RAG ingredient ranker
        "generate_supplement_recommendations": "supplement_recommendations.json",  # Agent 6: Medical supplement recommendations
        "compile_final_supplement_recommendations": "final_supplement_recommendations.json",  # Agent 7: Final complete protocol
        # "validate_ingredients_google": "validated_ingredients_google.json",  # Agent 6: Google Search validator (disabled)
        # "rank_ingredients": "ranked_ingredients.json",
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
    
    # 4. Create Excel report
    try:
        user_id = original_input_data[0]["user_full_data"]["metadata"]["phase_status"].get("user_id", "unknown_user")
        create_excel_report(original_input_data[0]["user_full_data"], out_dir, user_id)
    except Exception as e:
        print(f"⚠️ Warning: Could not create Excel report: {e}")


if __name__ == "__main__":
    run(input_path="inputs/combined_data.json")
