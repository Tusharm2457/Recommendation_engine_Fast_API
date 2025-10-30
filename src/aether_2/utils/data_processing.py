import json
import os
import re
import pandas as pd

def clean_agent_output(content: str, task_name: str) -> str:
    """Extract clean JSON from agent output that may contain reasoning text"""
    try:
        # Define expected JSON keys for different tasks
        task_keys = {
            "generate_supplement_recommendations": ["final_recommendations"],
            "compile_final_supplement_recommendations": ["supplement_recommendations"]
        }
        
        expected_keys = task_keys.get(task_name, [])
        
        # If no expected keys, return original content
        if not expected_keys:
            return content
        
        # Look for JSON blocks containing expected keys
        for key in expected_keys:
            # Pattern to match JSON objects with the specific key
            pattern = f'\\{{[^{{}}]*"{key}"[^{{}}]*\\[.*?\\]\\s*\\}}'
            matches = re.findall(pattern, content, re.DOTALL)
            
            if matches:
                # Use the last (most complete) JSON block
                clean_json = matches[-1]
                # Validate it's proper JSON
                json.loads(clean_json)
                print(f"✅ Extracted clean JSON from {task_name} output")
                return clean_json
        
        # Fallback: try to parse the entire content as JSON
        json.loads(content)
        print(f"✅ Content is already clean JSON for {task_name}")
        return content
        
    except json.JSONDecodeError:
        print(f"⚠️ Could not extract valid JSON from {task_name}, returning original content")
        return content
    except Exception as e:
        print(f"⚠️ Error cleaning {task_name} output: {e}")
        return content

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
            
            # Apply the same cleaning logic as in task output saving
            content = clean_agent_output(content, "compile_final_supplement_recommendations")
            
            return json.loads(content)
    return None


def create_excel_report(original_data, output_dir, user_id, user_email):
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
                    'User Email': user_email,
                    'Supplement': rec.get('ingredient_name', ''),
                    'Dosage': rec.get('recommended_dosage', ''),
                    'Frequency': rec.get('frequency', ''),
                    'Why': rec.get('why', ''),
                    'Core Focus Area': ', '.join(rec.get('focus_area', [])) if isinstance(rec.get('focus_area'), list) else rec.get('focus_area', ''),
                    'Additional Comments': ''
                })
            recommendations_df = pd.DataFrame(rec_data)
            recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
        else:
            # Create empty sheet if no recommendations found
            empty_df = pd.DataFrame(columns=['User Email', 'Supplement', 'Dosage', 'Frequency', 'Why', 'Core Focus Area', 'Additional Comments'])
            empty_df.to_excel(writer, sheet_name='Recommendations', index=False)
    
    print(f"✅ Excel report created: {excel_file}")

