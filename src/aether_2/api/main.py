"""
FastAPI wrapper for Aether AI Engine.
Provides REST API endpoints for generating personalized supplement protocols.
"""

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.aether_2.pipeline import run_aether_pipeline

# Initialize FastAPI app
app = FastAPI(
    title="Aether AI Engine API",
    description="AI-powered personalized supplement protocol generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (configure as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== REQUEST/RESPONSE MODELS ==========

class Demographics(BaseModel):
    """Patient demographics"""
    age: Optional[int] = None
    biological_sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None


class MedicalHistory(BaseModel):
    """Patient medical history"""
    diagnoses: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []


class Phase1BasicIntake(BaseModel):
    """Phase 1 basic intake data"""
    demographics: Optional[Demographics] = None
    medical_history: Optional[MedicalHistory] = None
    # Add other fields as needed - using flexible dict for now


class Phase2BloodReport(BaseModel):
    """Phase 2 blood report data"""
    # Using flexible dict structure to match your existing data
    pass


class Metadata(BaseModel):
    """Request metadata"""
    phase_status: Optional[Dict[str, Any]] = Field(default_factory=dict)
    email: Optional[str] = None


class PatientDataRequest(BaseModel):
    """
    Request model for patient data.
    Flexible structure to handle both formats:
    1. Direct format: {phase1_basic_intake, phase2_blood_report, metadata}
    2. Nested format: {metadata, patient_data: {phase1_basic_intake, phase2_detailed_intake}, latest_biomarker_results}
    """
    # Support both formats - all fields optional, will be validated in endpoint
    phase1_basic_intake: Optional[Dict[str, Any]] = Field(
        None,
        description="Phase 1 basic intake data including demographics, medical history, etc."
    )
    phase2_blood_report: Optional[Dict[str, Any]] = Field(
        None,
        description="Phase 2 blood report data with biomarker values"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadata including user_id, email, etc."
    )
    # Support nested format
    patient_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Nested patient data (alternative format)"
    )
    latest_biomarker_results: Optional[Dict[str, Any]] = Field(
        None,
        description="Latest biomarker results (alternative format)"
    )

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class SupplementRecommendation(BaseModel):
    """Individual supplement recommendation"""
    supplement_name: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = []
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None
    focus_areas: Optional[List[str]] = []


class ProtocolResponse(BaseModel):
    """Response model for successful protocol generation"""
    status: str = Field(..., description="Status of the request (success/error)")
    user_id: str = Field(..., description="User ID from the request")
    protocol: Dict[str, Any] = Field(..., description="Generated supplement protocol")
    preprocessing_outputs: Optional[Dict[str, Any]] = Field(
        None,
        description="Outputs from preprocessing steps (biomarkers, user profile, focus areas)"
    )
    execution_time_seconds: Optional[float] = Field(
        None,
        description="Total execution time in seconds"
    )
    message: Optional[str] = Field(
        None,
        description="Additional information or success message"
    )


class ErrorResponse(BaseModel):
    """Response model for errors"""
    status: str = "error"
    user_id: Optional[str] = None
    error: str
    execution_time_seconds: Optional[float] = None


# ========== API ENDPOINTS ==========

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Aether AI Engine API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate_protocol": "/generate-protocol",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aether-ai-engine",
        "version": "1.0.0"
    }


@app.post(
    "/generate-protocol",
    response_model=ProtocolResponse,
    responses={
        200: {"description": "Protocol generated successfully"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"}
    },
    tags=["Protocol Generation"]
)
async def generate_protocol(
    request: PatientDataRequest,
    include_details: bool = Query(
        False,
        description="Include preprocessing outputs and detailed information in the response"
    )
):
    """
    Generate personalized supplement protocol.

    This endpoint:
    1. Runs preprocessing (biomarker evaluation, user profile compilation, focus area analysis)
    2. Executes CrewAI pipeline (web discovery, RAG ranking, recommendations, final compilation)
    3. Returns cleaned JSON protocol

    **Input:** Patient data (supports multiple formats)

    **Output:** JSON protocol with supplement recommendations

    **Query Parameters:**
    - `include_details` (optional): Set to `true` to include preprocessing outputs in the response
    """
    try:
        # Convert request to dict
        raw_data = request.model_dump()

        # Normalize data structure to match what pipeline expects
        # Handle nested format: {metadata, patient_data: {phase1_basic_intake, phase2_detailed_intake}, latest_biomarker_results}
        if raw_data.get("patient_data"):
            patient_data = {
                "metadata": raw_data.get("metadata", {}),
                "phase1_basic_intake": raw_data["patient_data"].get("phase1_basic_intake", {}),
                "phase2_detailed_intake": raw_data["patient_data"].get("phase2_detailed_intake", {}),
                "latest_biomarker_results": raw_data.get("latest_biomarker_results", {})
            }
        # Handle direct format: {phase1_basic_intake, phase2_blood_report, metadata}
        elif raw_data.get("phase1_basic_intake"):
            patient_data = {
                "metadata": raw_data.get("metadata", {}),
                "phase1_basic_intake": raw_data.get("phase1_basic_intake", {}),
                "phase2_detailed_intake": raw_data.get("phase2_detailed_intake", {}),
                "latest_biomarker_results": raw_data.get("phase2_blood_report", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format. Must include either 'patient_data' or 'phase1_basic_intake'"
            )

        # Ensure user_id exists
        if not patient_data.get("metadata"):
            patient_data["metadata"] = {}
        if not patient_data["metadata"].get("phase_status"):
            patient_data["metadata"]["phase_status"] = {}
        if not patient_data["metadata"]["phase_status"].get("user_id"):
            # Generate a default user_id if not provided
            from datetime import datetime
            patient_data["metadata"]["phase_status"]["user_id"] = f"api_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n{'='*60}")
        print(f"📥 Received request for user: {patient_data['metadata']['phase_status']['user_id']}")
        print(f"{'='*60}")
        
        # Run pipeline
        result = run_aether_pipeline(patient_data)
        
        # Check if pipeline succeeded
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Pipeline execution failed")
            )

        # Build response - conditionally include preprocessing outputs
        response_data = {
            "status": "success",
            "user_id": result["user_id"],
            "protocol": result["protocol"],
            "execution_time_seconds": result.get("execution_time_seconds"),
            "message": f"Protocol generated successfully for user {result['user_id']}"
        }

        # Only include preprocessing outputs if requested
        if include_details:
            response_data["preprocessing_outputs"] = result.get("preprocessing_outputs")

        return ProtocolResponse(**response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"❌ Error generating protocol: {str(e)}")
        
        # Return error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate protocol: {str(e)}"
        )


# ========== STARTUP/SHUTDOWN EVENTS ==========

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("\n" + "="*60)
    print("🚀 Aether AI Engine API Starting...")
    print("="*60)
    print("📋 Service: Aether AI Engine")
    print("🔢 Version: 1.0.0")
    print("📚 Docs: http://localhost:8000/docs")
    print("🏥 Health: http://localhost:8000/health")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("\n" + "="*60)
    print("🛑 Aether AI Engine API Shutting Down...")
    print("="*60 + "\n")


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )

