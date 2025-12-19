#!/usr/bin/env python3
"""
Test GCS upload functionality for LOCAL testing.
Uploads file but skips signed URL generation (requires service account).
"""

import json
import io
from google.cloud import storage
from src.aether_2.utils.gcs_helper import generate_excel_in_memory

def test_gcs_upload_local():
    """Test GCS upload without signed URL (for local testing)"""
    
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
            }
        ]
    }
    
    # Extract user info
    user_email = sample_data.get('metadata', {}).get('email', 'test@example.com')
    user_id = 'test-user-id'
    bucket_name = 'recc_engine_data'
    
    print("="*70)
    print("🧪 Testing GCS Upload (Local Mode - No Signed URL)")
    print("="*70)
    print(f"   User Email: {user_email}")
    print(f"   User ID: {user_id}")
    print(f"   GCS Bucket: {bucket_name}")
    print(f"   Recommendations: {len(protocol_data['supplement_recommendations'])}")
    print()
    
    try:
        # Step 1: Generate Excel in memory
        print("📊 Step 1: Generating Excel in memory...")
        excel_buffer = generate_excel_in_memory(
            protocol_data=protocol_data,
            input_data=sample_data,
            user_id=user_id,
            user_email=user_email
        )
        excel_size = len(excel_buffer.getvalue())
        print(f"   ✅ Excel generated: {excel_size:,} bytes ({excel_size/1024:.2f} KB)")
        print()
        
        # Step 2: Upload to GCS (without signed URL)
        print("📤 Step 2: Uploading to GCS...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Sanitize email for filename
        safe_email = user_email.replace('@', '_').replace('.', '_')
        file_path = f"{safe_email}/{safe_email}.xlsx"
        
        blob = bucket.blob(file_path)
        blob.upload_from_string(
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        print(f"   ✅ File uploaded to: gs://{bucket_name}/{file_path}")
        print()
        
        # Step 3: Verify file exists
        print("🔍 Step 3: Verifying file exists in GCS...")
        if blob.exists():
            print(f"   ✅ File exists in GCS")
            print(f"   📏 Size: {blob.size:,} bytes")
            print(f"   📅 Updated: {blob.updated}")
            print()
        else:
            print(f"   ❌ File not found in GCS")
            return False
        
        # Step 4: Make file publicly accessible (for testing)
        print("🌐 Step 4: Making file publicly accessible (for testing)...")
        blob.make_public()
        public_url = blob.public_url
        print(f"   ✅ Public URL: {public_url}")
        print()
        
        print("💡 TIP: You can download the file using:")
        print(f"   wget \"{public_url}\" -O downloaded_protocol.xlsx")
        print()
        print("   Or open in browser:")
        print(f"   open \"{public_url}\"")
        print()
        print("⚠️  NOTE: File is now PUBLIC. In production, use signed URLs instead.")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("💡 TROUBLESHOOTING:")
        print("   1. Check if GCS bucket 'recc_engine_data' exists:")
        print("      gsutil ls gs://recc_engine_data")
        print()
        print("   2. Verify GCP credentials are configured:")
        print("      gcloud auth application-default login")
        print()
        print("   3. Check you have write permissions to the bucket:")
        print("      gsutil iam get gs://recc_engine_data")
        print()
        return False


if __name__ == "__main__":
    success = test_gcs_upload_local()
    
    print("="*70)
    if success:
        print("✅ TEST PASSED - GCS upload works correctly!")
        print("   (Signed URLs will work in Cloud Run with service account)")
    else:
        print("❌ TEST FAILED - Check errors above")
    print("="*70)

