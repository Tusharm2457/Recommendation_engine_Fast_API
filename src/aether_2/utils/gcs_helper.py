"""
GCS Helper Module for Excel File Generation and Upload.
Handles in-memory Excel generation and Google Cloud Storage operations.
"""

import io
from datetime import timedelta
from typing import Dict, Any
import pandas as pd
from google.cloud import storage


def create_nested_excel_data(data, parent_paths=[], skip_phase_prefix=True):
    """
    Create nested structure for Excel export with separate columns for each hierarchy level.
    Reused from data_processing.py to maintain consistency.
    """
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
                                while len(item_paths) < 4:
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
                while len(item_paths) < 4:
                    item_paths.append('')
                item_paths.append(v)
                items.append(tuple(item_paths))
    return items


def generate_excel_in_memory(
    protocol_data: Dict[str, Any],
    input_data: Dict[str, Any],
    user_id: str,
    user_email: str
) -> io.BytesIO:
    """
    Generate Excel file in memory (no disk I/O).
    
    Creates a 3-sheet Excel file:
    - Sheet 1: Patient_Data (hierarchical patient information)
    - Sheet 2: Biomarkers (biomarker test results)
    - Sheet 3: Recommendations (supplement recommendations)
    
    Args:
        protocol_data: The protocol dict from pipeline output containing supplement_recommendations
        input_data: The original patient data from API request
        user_id: User identifier
        user_email: User email address
    
    Returns:
        BytesIO object containing the Excel file
    """
    # Create BytesIO object to hold Excel file in memory
    excel_buffer = io.BytesIO()
    
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # Sheet 1: Patient Data (multi-column hierarchical format)
        # Handle both nested and flat data structures
        if 'patient_data' in input_data:
            patient_data = input_data['patient_data']
        else:
            # Construct from flat structure
            patient_data = {}
            if 'phase1_basic_intake' in input_data:
                patient_data['phase1_basic_intake'] = input_data['phase1_basic_intake']
            if 'phase2_detailed_intake' in input_data:
                patient_data['phase2_detailed_intake'] = input_data['phase2_detailed_intake']
        
        nested_patient_data = create_nested_excel_data(patient_data)
        patient_df = pd.DataFrame(
            nested_patient_data,
            columns=['Category', 'Subcategory', 'Field', 'Detail', 'Value']
        )
        patient_df.to_excel(writer, sheet_name='Patient_Data', index=False)
        
        # Sheet 2: Biomarkers (vertical format)
        biomarkers = input_data.get('latest_biomarker_results', {})
        biomarkers_df = pd.DataFrame(
            list(biomarkers.items()),
            columns=['Biomarker', 'Value']
        )
        biomarkers_df.to_excel(writer, sheet_name='Biomarkers', index=False)
        
        # Sheet 3: Recommendations (horizontal format)
        # Get recommendations from protocol_data instead of file system
        recommendations = protocol_data.get('supplement_recommendations', [])
        
        if recommendations:
            rec_data = []
            for rec in recommendations:
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
            empty_df = pd.DataFrame(
                columns=['User Email', 'Supplement', 'Dosage', 'Frequency', 'Why', 'Core Focus Area', 'Additional Comments']
            )
            empty_df.to_excel(writer, sheet_name='Recommendations', index=False)
    
    # Reset buffer position to beginning
    excel_buffer.seek(0)
    
    return excel_buffer


def upload_excel_to_gcs(
    excel_bytes: io.BytesIO,
    bucket_name: str,
    user_id: str,
    user_email: str
) -> Dict[str, Any]:
    """
    Upload Excel file to Google Cloud Storage and generate signed URL.

    Args:
        excel_bytes: BytesIO object containing Excel file
        bucket_name: GCS bucket name (e.g., "aether-protocols")
        user_id: User identifier
        user_email: User email address for organizing files and filename

    Returns:
        Dict with:
            - file_path: GCS path (e.g., "test_example_com/test_example_com.xlsx")
            - signed_url: Temporary download URL (24-hour expiry)
            - bucket: Bucket name
            - expires_in_hours: URL expiration time in hours
    """
    # Initialize GCS client (uses Application Default Credentials)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Sanitize email for filename (replace @ and . with _)
    safe_email = user_email.replace('@', '_').replace('.', '_') if user_email else "unknown_user"
    file_path = f"{safe_email}/{safe_email}.xlsx"
    
    # Create blob and upload
    blob = bucket.blob(file_path)
    
    # Upload from BytesIO object
    # Use if_generation_match=0 to prevent race conditions (only upload if file doesn't exist)
    blob.upload_from_string(
        excel_bytes.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        if_generation_match=0
    )
    
    # Generate signed URL (valid for 24 hours)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=24),
        method="GET"
    )
    
    return {
        "file_path": file_path,
        "signed_url": signed_url,
        "bucket": bucket_name,
        "expires_in_hours": 24
    }


def generate_and_upload_protocol_excel(
    protocol_data: Dict[str, Any],
    input_data: Dict[str, Any],
    user_id: str,
    user_email: str,
    bucket_name: str
) -> Dict[str, Any]:
    """
    Convenience function that generates Excel file and uploads to GCS in one call.
    
    Args:
        protocol_data: The protocol dict from pipeline output
        input_data: The original patient data from API request
        user_id: User identifier
        user_email: User email address
        bucket_name: GCS bucket name
    
    Returns:
        Dict with file_path, signed_url, bucket, and expires_in_hours
    """
    # Generate Excel in memory
    excel_buffer = generate_excel_in_memory(
        protocol_data=protocol_data,
        input_data=input_data,
        user_id=user_id,
        user_email=user_email
    )
    
    # Upload to GCS
    upload_result = upload_excel_to_gcs(
        excel_bytes=excel_buffer,
        bucket_name=bucket_name,
        user_id=user_id,
        user_email=user_email
    )

    return upload_result

