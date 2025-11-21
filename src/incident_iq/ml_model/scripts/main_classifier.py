"""
Main entry point for incident severity classification system.
Orchestrates all components and processes incidents.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add src directory to path for imports
src_path = Path(__file__).resolve().parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now import from this directory
from incident_iq.ml_model.scripts.incident_processor import IncidentProcessor


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_dir / "classifier.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')


def validate_configuration(model_dir: str, db_path: str) -> None:
    """
    Validate configuration paths exist.
    
    Args:
        model_dir: Path to model directory
        db_path: Path to database file
        
    Raises:
        FileNotFoundError: If required files don't exist
    """
    logger = logging.getLogger(__name__)
    
    # Check database
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    logger.info(f"✓ Database found: {db_path}")
    
    # Check model directory
    if not Path(model_dir).exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")
    logger.info(f"✓ Model directory found: {model_dir}")
    
    # Check BERT model files
    required_bert_files = ['config.json', 'vocab.txt']
    for file in required_bert_files:
        file_path = Path(model_dir) / file
        if not file_path.exists():
            raise FileNotFoundError(f"Required BERT file not found: {file_path}")
    logger.info(f"✓ BERT model files validated")
    
    # Check for model weights (either format)
    has_weights = (
        (Path(model_dir) / 'pytorch_model.bin').exists() or
        (Path(model_dir) / 'model.safetensors').exists()
    )
    if not has_weights:
        raise FileNotFoundError(f"BERT model weights not found in {model_dir}")
    logger.info(f"✓ BERT model weights found")


def print_banner():
    """Print application banner."""
    banner = """
    ================================================================
    
         Incident Severity Classification System              
    
         Version: 2.0                                          
         Using: BERT Embeddings + ML Classification           
    
    ================================================================
    """
    print(banner)


def main():
    """Main execution function."""
    
    # Print banner
    print_banner()
    
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    # Configuration
    DB_NAME = os.getenv("DB_NAME", "incident_iq.db")
    DB_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "data" / DB_NAME
    MODEL_DIR = Path(__file__).resolve().parent.parent / "bert" 
    
    # Processing options
    BATCH_SIZE = 100  # Commit every 100 incidents
    LIMIT = None  # Process all (set to number to limit)
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_configuration(MODEL_DIR, DB_PATH)
        logger.info("Configuration validated successfully")
        print()
        
        # Initialize processor
        logger.info("Initializing incident processor...")
        processor = IncidentProcessor(db_path=DB_PATH, model_dir=MODEL_DIR)
        print()
        
        # Process incidents
        logger.info("Starting incident processing...")
        processor.process_incidents(limit=LIMIT, batch_size=BATCH_SIZE)
        print()
        
        # Log completion
        logger.info("Incident classification completed successfully")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("Please check your configuration paths.")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n❌ Unexpected error occurred: {str(e)}")
        print("Check logs/classifier.log for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())