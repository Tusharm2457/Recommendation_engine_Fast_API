import os
import sys
from dotenv import load_dotenv
from google.cloud import secretmanager
from .logging_setup import logger

def initialize_auth():
    """Initialize all authentication and environment setup"""
    
    # Set Vertex AI environment variables for project configuration
    os.environ["VERTEX_PROJECT"] = "singular-object-456719-i6"
    os.environ["VERTEX_LOCATION"] = "us-central1"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "singular-object-456719-i6"
    
    # Disable LiteLLM verbose logging
    os.environ["LITELLM_LOG"] = "WARNING"
    os.environ["LITELLM_LOG_LEVEL"] = "WARNING"
    
    # Google Colab authentication
    if "google.colab" in sys.modules:
        try:
            from google.colab import auth
            auth.authenticate_user(project_id='singular-object-456719-i6')
            print("Authenticated")
            logger.info("🔐 Google Colab authentication completed")
        except ImportError:
            logger.info("🔐 Not in Google Colab environment - skipping Colab auth")
    
    # Google Cloud Secret Manager setup
    PROJECT_ID = "singular-object-456719-i6"
    SECRET_1 = "SERPER_API_KEY" 
    SECRET_2 = "Vertex_API_Key" 
    
    try:
        client = secretmanager.SecretManagerServiceClient()
    except Exception as e:
        logger.error(f"Failed to initialize Secret Manager client: {e}", exc_info=True)
        raise
    
    # Access SERPER_API_KEY secret
    try:
        secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_1}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_value = response.payload.data.decode("UTF-8")
        os.environ["SERPER_API_KEY"] = secret_value
    except Exception as e:
        logger.error(f" Failed to access {SECRET_1}: {e}", exc_info=True)
    
    # Access GEMINI_API_KEY secret
    try:
        secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_2}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_value = response.payload.data.decode("UTF-8")
        os.environ["GEMINI_API_KEY"] = secret_value
        logger.info("GEMINI_API_KEY secret loaded successfully")
    except Exception as e:
        logger.error(f" Failed to access {SECRET_2}: {e}", exc_info=True)
    
    # Load environment variables from .env file
    load_dotenv()

