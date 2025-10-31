#!/usr/bin/env python3
"""
Test script for Aether AI Engine API.
Sends a request to the API using the combined_data.json file.
"""

import requests
import json
import sys
from pathlib import Path

# API endpoint - Change this to test different environments
# Local: http://localhost:8000/generate-protocol
# Cloud Run: https://aether-api-224321939514.us-central1.run.app/generate-protocol
API_URL = "http://localhost:8000/generate-protocol"

def load_test_data(file_path="inputs/combined_data.json"):
    """Load test data from combined_data.json"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract the first user's data (combined_data.json is a list)
        if isinstance(data, list) and len(data) > 0:
            # Get user_full_data from the first entry
            user_data = data[0].get("user_full_data", {})

            # The API expects this structure:
            # {
            #   "metadata": {...},
            #   "patient_data": {
            #     "phase1_basic_intake": {...},
            #     "phase2_detailed_intake": {...}
            #   },
            #   "latest_biomarker_results": {...}
            # }

            # This matches the structure in combined_data.json
            return user_data
        else:
            return data

    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("🏥 Testing Health Check Endpoint")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Is the server running?")
        print("   Run: ./run_api.sh or python src/aether_2/api/main.py")
        return False


def test_generate_protocol(data, include_details=False):
    """Test the generate protocol endpoint"""
    mode = "with details" if include_details else "clean (default)"
    print("\n" + "="*60)
    print(f"🧪 Testing Generate Protocol Endpoint ({mode})")
    print("="*60)

    # Add query parameter if needed
    url = API_URL
    if include_details:
        url = f"{API_URL}?include_details=true"

    print(f"\n📤 Sending request to: {url}")
    print(f"📊 Patient data keys: {list(data.keys())}")
    
    try:
        # Send POST request (use the url variable with query params)
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minutes timeout (pipeline can take time)
        )
        
        print(f"\n📥 Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Protocol Generated Successfully!")
            print(f"👤 User ID: {result.get('user_id')}")
            print(f"⏱️  Execution Time: {result.get('execution_time_seconds', 0):.2f} seconds")

            # Check if preprocessing outputs are included
            has_details = 'preprocessing_outputs' in result
            print(f"📊 Preprocessing outputs included: {'✅ Yes' if has_details else '❌ No (use ?include_details=true to include)'}")

            # Save the response
            output_file = "test_api_response.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full response saved to: {output_file}")

            # Display protocol summary
            protocol = result.get('protocol', {})
            recommendations = protocol.get('supplement_recommendations', [])
            print(f"\n📋 Protocol Summary:")
            print(f"   Total Recommendations: {len(recommendations)}")

            if recommendations:
                print(f"\n   Top 3 Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec.get('ingredient_name', 'N/A')}")

            return True
        
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out (pipeline took too long)")
        return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Is the server running?")
        return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Aether AI Engine API")
    parser.add_argument(
        "--include-details",
        action="store_true",
        help="Include preprocessing outputs in the response"
    )
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🧪 Aether AI Engine API Test Suite")
    print("="*60)

    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Health check failed. Exiting.")
        sys.exit(1)

    # Test 2: Load test data
    print("\n" + "="*60)
    print("📂 Loading Test Data")
    print("="*60)

    test_data = load_test_data()
    print(f"✅ Loaded test data with keys: {list(test_data.keys())}")

    # Test 3: Generate protocol
    success = test_generate_protocol(test_data, include_details=args.include_details)

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)

    if success:
        print("✅ All tests passed!")
        print("\n📝 Next steps:")
        print("   1. Check test_api_response.json for the full response")
        print("   2. Review the generated protocol")
        print("   3. Test with different patient data")
        print("\n💡 Tip: Run with --include-details to get preprocessing outputs")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

