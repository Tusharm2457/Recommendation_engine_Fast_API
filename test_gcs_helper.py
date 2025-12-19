#!/usr/bin/env python3
"""
Quick test script for GCS helper functions.
Tests Excel generation in memory (without GCS upload).
"""

import json
from src.aether_2.utils.gcs_helper import generate_excel_in_memory

def test_excel_generation():
    """Test Excel generation with sample data"""
    
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
    
    # Extract user email
    user_email = sample_data.get('metadata', {}).get('email', 'test@example.com')
    user_id = 'test-user-id'
    
    # Calculate expected filename
    safe_email = user_email.replace('@', '_').replace('.', '_')
    expected_filename = f"{safe_email}/{safe_email}.xlsx"

    print("🧪 Testing Excel generation in memory...")
    print(f"   User: {user_email}")
    print(f"   User ID: {user_id}")
    print(f"   Expected GCS path: {expected_filename}")
    print(f"   Recommendations: {len(protocol_data['supplement_recommendations'])}")
    
    try:
        # Generate Excel in memory
        excel_buffer = generate_excel_in_memory(
            protocol_data=protocol_data,
            input_data=sample_data,
            user_id=user_id,
            user_email=user_email
        )
        
        # Check buffer size
        excel_size = len(excel_buffer.getvalue())
        print(f"\n✅ Excel generated successfully!")
        print(f"   Size: {excel_size:,} bytes ({excel_size/1024:.2f} KB)")
        
        # Optionally save to disk for manual inspection
        save_to_disk = input("\n💾 Save Excel to disk for inspection? (y/n): ").lower().strip()
        if save_to_disk == 'y':
            output_file = 'test_protocol.xlsx'
            with open(output_file, 'wb') as f:
                f.write(excel_buffer.getvalue())
            print(f"   Saved to: {output_file}")
            print(f"   You can open this file in Excel to verify the format")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("GCS Helper - Excel Generation Test")
    print("="*60)
    
    success = test_excel_generation()
    
    print("\n" + "="*60)
    if success:
        print("✅ Test PASSED - Excel generation works correctly!")
    else:
        print("❌ Test FAILED - Check errors above")
    print("="*60)

