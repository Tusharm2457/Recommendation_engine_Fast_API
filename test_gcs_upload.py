#!/usr/bin/env python3
"""
Test GCS upload functionality.
Tests the complete flow: Excel generation + GCS upload + signed URL.
"""

import json
from src.aether_2.utils.gcs_helper import generate_and_upload_protocol_excel

def test_gcs_upload():
    """Test complete Excel generation and GCS upload"""
    
    # Load sample data
    with open('inputs/combined_data.json', 'r') as f:
        combined_data = json.load(f)
    
    # Extract the first user's data
    sample_data = combined_data[0]['user_full_data']
    
    # Sample protocol data (simulating pipeline output)
    protocol_data = {
        "supplement_recommendations": [
            {
                "ingredient_name": "Vitamin D3",
                "recommended_dosage": "5000 IU",
                "frequency": "Once daily",
                "why": "Low vitamin D levels detected in blood work",
                "focus_area": ["IMM", "SKN"]
            },
            {
                "ingredient_name": "Omega-3 Fish Oil",
                "recommended_dosage": "2000 mg EPA/DHA",
                "frequency": "Twice daily with meals",
                "why": "Support cardiovascular health and reduce inflammation",
                "focus_area": ["CM", "HRM"]
            },
            {
                "ingredient_name": "Magnesium Glycinate",
                "recommended_dosage": "400 mg",
                "frequency": "Once daily before bed",
                "why": "Support sleep quality and muscle relaxation",
                "focus_area": ["SLP", "MSK"]
            }
        ]
    }
    
    # Extract user info
    user_email = sample_data.get('metadata', {}).get('email', 'test@example.com')
    user_id = 'test-user-id'
    bucket_name = 'recc_engine_data'  # Your GCS bucket
    
    print("="*70)
    print("🧪 Testing GCS Upload Functionality")
    print("="*70)
    print(f"   User Email: {user_email}")
    print(f"   User ID: {user_id}")
    print(f"   GCS Bucket: {bucket_name}")
    print(f"   Recommendations: {len(protocol_data['supplement_recommendations'])}")
    print()
    
    try:
        print("📊 Step 1: Generating Excel in memory...")
        print("📤 Step 2: Uploading to GCS...")
        print("🔗 Step 3: Generating signed URL...")
        print()
        
        # Generate and upload
        result = generate_and_upload_protocol_excel(
            protocol_data=protocol_data,
            input_data=sample_data,
            user_id=user_id,
            user_email=user_email,
            bucket_name=bucket_name
        )
        
        print("✅ SUCCESS! Excel file uploaded to GCS")
        print()
        print("📋 RESULT:")
        print(f"   File Path: {result['file_path']}")
        print(f"   Bucket: {result['bucket']}")
        print(f"   Expires In: {result['expires_in_hours']} hours")
        print()
        print("🔗 SIGNED URL:")
        print(f"   {result['signed_url'][:100]}...")
        print()
        print("💡 TIP: You can download the file using:")
        print(f"   wget \"{result['signed_url']}\" -O downloaded_protocol.xlsx")
        print()
        print("   Or open in browser:")
        print(f"   open \"{result['signed_url']}\"")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("💡 TROUBLESHOOTING:")
        print("   1. Check if GCS bucket 'recc_engine_data' exists")
        print("   2. Verify GCP credentials are configured:")
        print("      gcloud auth application-default login")
        print("   3. Check service account has Storage Object Admin permissions")
        print()
        return False


if __name__ == "__main__":
    success = test_gcs_upload()
    
    print("="*70)
    if success:
        print("✅ TEST PASSED - GCS upload works correctly!")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("="*70)

