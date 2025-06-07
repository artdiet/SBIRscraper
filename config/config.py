#!/usr/bin/env python3
"""
Configuration management for SBIR Scraper
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
API_BASE_URL = "https://api.www.sbir.gov/public/api/awards"
API_TIMEOUT = 30  # seconds
API_DELAY = 1.0   # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5   # seconds

# Download Configuration
BATCH_SIZE = 1000  # Maximum records per API request
ESTIMATED_TOTAL_RECORDS = 213000

# Database Configuration
DATABASE_PATH = DATA_DIR / "sbir_awards.db"
BACKUP_DATABASE_PATH = DATA_DIR / "sbir_awards_backup.db"

# Export Configuration
CSV_EXPORT_PATH = DATA_DIR / "sbir_awards.csv"
JSON_BACKUP_PATH = DATA_DIR / "sbir_awards_raw.json"

# Logging Configuration
LOG_FILE = LOGS_DIR / "sbir_scraper.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Progress Tracking
PROGRESS_UPDATE_INTERVAL = 10  # Update progress every N batches
CHECKPOINT_INTERVAL = 50       # Save checkpoint every N batches

# Data Quality
REQUIRED_FIELDS = [
    "firm", "award_title", "agency", "phase", "program",
    "award_amount", "proposal_award_date", "contract"
]

# Update Configuration
UPDATE_CHECK_DAYS = 7  # Check for updates every N days
UPDATE_LOOKBACK_DAYS = 30  # Look back N days for new records

# Rate Limiting
REQUESTS_PER_MINUTE = 60
DAILY_REQUEST_LIMIT = 10000

def get_user_agent():
    """Get User-Agent string for API requests"""
    return "SBIR-Scraper/1.0 (https://github.com/artdiet/SBIRscraper; contact: art.dietrich@dtriq.com)"

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    if BATCH_SIZE > 1000:
        errors.append("BATCH_SIZE cannot exceed 1000 (API limitation)")
    
    if API_DELAY < 0.5:
        errors.append("API_DELAY should be at least 0.5 seconds for API politeness")
    
    if not API_BASE_URL.startswith("https://"):
        errors.append("API_BASE_URL must use HTTPS")
    
    return errors

if __name__ == "__main__":
    # Validate configuration on import
    config_errors = validate_config()
    if config_errors:
        print("Configuration errors found:")
        for error in config_errors:
            print(f"  - {error}")
    else:
        print("Configuration validation passed")
        print(f"Database path: {DATABASE_PATH}")
        print(f"Data directory: {DATA_DIR}")
        print(f"Logs directory: {LOGS_DIR}")