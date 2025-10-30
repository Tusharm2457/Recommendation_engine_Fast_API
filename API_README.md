# Aether AI Engine API

FastAPI wrapper for the Aether AI Engine - AI-powered personalized supplement protocol generation.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install API dependencies (includes all base dependencies)
pip install -r requirements-api.txt
```

### 2. Set Environment Variables

```bash
# Serper API Key (if not already set)
export SERPER_API_KEY="your-serper-api-key"

# Authenticate with Google Cloud (for Vertex AI)
gcloud auth application-default login
```

### 3. Start the API Server

**Option A: Using the startup script**
```bash
chmod +x run_api.sh
./run_api.sh
```

**Option B: Using uvicorn directly**
```bash
cd src/aether_2/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Option C: Using Python**
```bash
python src/aether_2/api/main.py
```

The API will be available at:
- **API Base:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 📡 API Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "aether-ai-engine",
  "version": "1.0.0"
}
```

### 2. Generate Protocol
```bash
POST /generate-protocol
```

**Request Body:**
```json
{
  "phase1_basic_intake": {
    "demographics": {
      "age": 35,
      "biological_sex": "male",
      "height_cm": 175,
      "weight_kg": 75
    },
    "medical_history": {
      "diagnoses": ["vitamin_d_deficiency"],
      "medications": [],
      "allergies": []
    }
  },
  "phase2_blood_report": {
    "vitamin_d": {"value": 15, "unit": "ng/mL"}
  },
  "metadata": {
    "phase_status": {
      "user_id": "test_user_123"
    },
    "email": "test@example.com"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "user_id": "test_user_123",
  "protocol": {
    "supplement_recommendations": [
      {
        "supplement_name": "Vitamin D Protocol",
        "ingredients": [...],
        "dosage": "5000 IU",
        "frequency": "Daily",
        "timing": "With breakfast"
      }
    ]
  },
  "preprocessing_outputs": {
    "biomarker_results": {...},
    "user_profile": {...},
    "focus_areas": {...}
  },
  "execution_time_seconds": 45.2,
  "message": "Protocol generated successfully for user test_user_123"
}
```

---

## 🧪 Testing the API

### Using the Test Script

```bash
# Make sure the API is running first
./run_api.sh

# In another terminal, run the test script
python test_api.py
```

The test script will:
1. Check API health
2. Load data from `inputs/combined_data.json`
3. Send a request to generate a protocol
4. Save the response to `test_api_response.json`

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Generate protocol
curl -X POST http://localhost:8000/generate-protocol \
  -H "Content-Type: application/json" \
  -d @inputs/combined_data.json
```

### Using Python requests

```python
import requests
import json

# Load patient data
with open('inputs/combined_data.json', 'r') as f:
    data = json.load(f)
    patient_data = data[0]['user_full_data']

# Send request
response = requests.post(
    'http://localhost:8000/generate-protocol',
    json=patient_data
)

# Get result
result = response.json()
print(f"Status: {result['status']}")
print(f"User ID: {result['user_id']}")
print(f"Protocol: {result['protocol']}")
```

### Using the Interactive Docs

1. Open http://localhost:8000/docs in your browser
2. Click on the `/generate-protocol` endpoint
3. Click "Try it out"
4. Paste your patient data JSON
5. Click "Execute"
6. View the response

---

## 📁 Project Structure

```
.
├── src/aether_2/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application
│   ├── pipeline.py           # Core pipeline logic
│   ├── main.py              # CLI version (unchanged)
│   ├── crew.py              # CrewAI configuration
│   ├── tools/               # AI agent tools
│   └── utils/               # Utility functions
├── requirements-api.txt      # API dependencies
├── run_api.sh               # API startup script
├── test_api.py              # API test script
└── API_README.md            # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SERPER_API_KEY` | Google Serper API key for web search | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key (auto-set by gcloud) | Yes (for Vertex AI) |

### Port Configuration

Default port: `8000`

To change the port:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## 🐳 Docker Deployment (Coming Soon)

See the deployment guide for containerization and GCP deployment instructions.

---

## 🔒 Authentication

Currently, the API has **no authentication** (development mode).

For production deployment, consider:
- API Key authentication
- GCP IAM authentication
- OAuth 2.0

---

## ⚡ Performance

- **Average execution time:** 30-60 seconds
- **Timeout:** 10 minutes (configurable)
- **Concurrent requests:** Supported (but may be limited by LLM rate limits)

---

## 🐛 Troubleshooting

### API won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r requirements-api.txt
```

**Error:** `Address already in use`
```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --port 8080
```

### Authentication errors

**Error:** `Could not automatically determine credentials`
```bash
# Authenticate with Google Cloud
gcloud auth application-default login
```

**Error:** `SERPER_API_KEY not found`
```bash
# Set the environment variable
export SERPER_API_KEY="your-key-here"
```

### Pipeline errors

Check the logs in the terminal where the API is running. The pipeline prints detailed debug information.

---

## 📊 Monitoring

The API logs all requests and pipeline execution to stdout. In production, configure proper logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 🚀 Next Steps

1. ✅ Test the API locally
2. 🐳 Containerize with Docker
3. ☁️ Deploy to Google Cloud Run
4. 🔒 Add authentication
5. 📊 Add monitoring and logging
6. 📈 Add rate limiting
7. 🎯 Add caching for common requests

---

## 📝 Notes

- The API returns **JSON only** (no Excel file)
- Files are **not saved** to disk (stateless API)
- The original `main.py` CLI version is **unchanged** and still works
- All existing agent code is **unchanged**

---

## 🆘 Support

For issues or questions, check:
- API logs (terminal output)
- Interactive docs: http://localhost:8000/docs
- Test script output: `python test_api.py`

