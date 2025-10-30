import os
import csv
import logging
from datetime import datetime

# Setup logging for file-based debugging (minimal console output)
def setup_logging():
    """Setup logging to files only, minimal console output"""
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging to files only (no console handler)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler for detailed logs only
            logging.FileHandler(os.path.join(log_dir, 'crewai_debug.log'))
        ]
    )
    
    # Set specific loggers to DEBUG level for file logging
    loggers_to_debug = [
        'crewai',
        'crewai.agent',
        'crewai.task',
        'crewai.crew',
        'openai',
        'anthropic',
        'google.cloud',
        'httpx',
        'urllib3'
    ]
    
    for logger_name in loggers_to_debug:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)
    
    # Create a custom logger for our application (file only)
    app_logger = logging.getLogger('aether_2')
    app_logger.setLevel(logging.INFO)
    
    return app_logger

# Setup CSV logging for execution tracking
def setup_csv_logging():
    """Setup CSV logging for execution tracking"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create CSV filename with current date
    today = datetime.now().strftime("%Y-%m-%d")
    csv_file = os.path.join(log_dir, f"execution_log_{today}.csv")
    
    # Create CSV file with headers if it doesn't exist
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'start_time', 'end_time', 'duration_seconds', 'status'])
    
    return csv_file

# Initialize logging
logger = setup_logging()

# Disable LiteLLM console logging (keep file logging only)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:DEBUG").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:utils").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:vertex_llm_base").setLevel(logging.WARNING)
logging.getLogger("LiteLLM:litellm_logging").setLevel(logging.WARNING)

# Setup CSV logging
csv_log_file = setup_csv_logging()
logger.info(f"📊 CSV execution log: {csv_log_file}")

