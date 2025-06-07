#!/usr/bin/env python3
"""
SBIR Initial Data Download
Downloads all available SBIR/STTR awards from the API and stores them in SQLite database.
"""

import requests
import time
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import signal

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config.config import *
from src.database import SBIRDatabase

class DownloadInterrupted(Exception):
    """Exception raised when download is interrupted by user"""
    pass

class SBIRInitialDownloader:
    """Downloads all SBIR awards from the API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': get_user_agent()
        })
        
        self.total_downloaded = 0
        self.start_time = None
        self.interrupted = False
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handler for graceful interruption
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.interrupted = True
    
    def fetch_batch(self, start_offset: int, batch_size: int = BATCH_SIZE) -> Optional[List[Dict[str, Any]]]:
        """Fetch a batch of awards from the API"""
        params = {
            'start': start_offset,
            'rows': batch_size
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.debug(f"Fetching batch: offset={start_offset}, size={batch_size}, attempt={attempt + 1}")
                
                response = self.session.get(
                    API_BASE_URL,
                    params=params,
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Handle API response format
                if isinstance(data, list):
                    awards = data
                elif isinstance(data, dict):
                    awards = data.get('docs', [])
                else:
                    self.logger.error(f"Unexpected API response format: {type(data)}")
                    return None
                
                self.logger.debug(f"Successfully fetched {len(awards)} awards")
                return awards
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.logger.error(f"Failed to fetch batch after {MAX_RETRIES} attempts")
                    return None
            
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {e}")
                return None
    
    def validate_batch(self, awards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean a batch of awards"""
        valid_awards = []
        
        for award in awards:
            # Check required fields
            missing_fields = [field for field in REQUIRED_FIELDS if field not in award]
            if missing_fields:
                self.logger.warning(f"Award missing required fields {missing_fields}: {award.get('contract', 'unknown')}")
                continue
            
            # Basic data validation
            if not award.get('firm') or not award.get('award_title'):
                self.logger.warning(f"Award has empty firm or title: {award.get('contract', 'unknown')}")
                continue
            
            valid_awards.append(award)
        
        return valid_awards
    
    def download_all_awards(self, resume: bool = True) -> bool:
        """Download all awards from the API"""
        self.start_time = datetime.now()
        self.logger.info("Starting initial SBIR awards download...")
        
        try:
            with SBIRDatabase() as db:
                db.create_tables()
                
                # Determine starting offset
                start_offset = 0
                if resume:
                    existing_count = db.get_record_count()
                    if existing_count > 0:
                        start_offset = existing_count
                        self.logger.info(f"Resuming download from offset {start_offset}")
                        self.total_downloaded = existing_count
                
                # Download in batches
                offset = start_offset
                consecutive_empty_batches = 0
                
                while not self.interrupted:
                    # Fetch batch
                    awards = self.fetch_batch(offset, BATCH_SIZE)
                    
                    if awards is None:
                        self.logger.error("Failed to fetch batch, aborting download")
                        return False
                    
                    if len(awards) == 0:
                        consecutive_empty_batches += 1
                        if consecutive_empty_batches >= 3:
                            self.logger.info("Received multiple empty batches, download complete")
                            break
                        else:
                            self.logger.warning(f"Empty batch at offset {offset}, trying next batch")
                            offset += BATCH_SIZE
                            continue
                    else:
                        consecutive_empty_batches = 0
                    
                    # Validate awards
                    valid_awards = self.validate_batch(awards)
                    if not valid_awards:
                        self.logger.warning(f"No valid awards in batch at offset {offset}")
                        offset += len(awards)
                        continue
                    
                    # Insert into database
                    try:
                        inserted = db.insert_awards(valid_awards)
                        self.total_downloaded += inserted
                        offset += len(awards)
                        
                        # Progress reporting
                        if offset % (PROGRESS_UPDATE_INTERVAL * BATCH_SIZE) == 0:
                            self.log_progress(offset)
                        
                        # Checkpoint
                        if offset % (CHECKPOINT_INTERVAL * BATCH_SIZE) == 0:
                            db.set_metadata("last_download_offset", str(offset))
                            db.set_metadata("last_download_time", datetime.now().isoformat())
                            self.logger.info(f"Checkpoint saved at offset {offset}")
                        
                        # Rate limiting
                        time.sleep(API_DELAY)
                        
                    except Exception as e:
                        self.logger.error(f"Database error at offset {offset}: {e}")
                        return False
                
                # Save final metadata
                db.set_metadata("initial_download_completed", datetime.now().isoformat())
                db.set_metadata("total_records_downloaded", str(self.total_downloaded))
                
                if self.interrupted:
                    self.logger.info("Download interrupted by user")
                    db.set_metadata("download_interrupted", "true")
                    return False
                else:
                    self.logger.info("Download completed successfully")
                    db.set_metadata("download_interrupted", "false")
                    return True
                
        except Exception as e:
            self.logger.error(f"Fatal error during download: {e}")
            return False
    
    def log_progress(self, current_offset: int):
        """Log download progress"""
        if not self.start_time:
            return
        
        elapsed = datetime.now() - self.start_time
        elapsed_seconds = elapsed.total_seconds()
        
        if elapsed_seconds > 0:
            rate = self.total_downloaded / elapsed_seconds
            estimated_total = ESTIMATED_TOTAL_RECORDS
            
            if estimated_total > 0:
                progress_pct = (self.total_downloaded / estimated_total) * 100
                remaining = estimated_total - self.total_downloaded
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                self.logger.info(
                    f"Progress: {self.total_downloaded:,}/{estimated_total:,} "
                    f"({progress_pct:.1f}%) - "
                    f"Rate: {rate:.1f} records/sec - "
                    f"ETA: {eta_minutes:.1f} minutes"
                )
            else:
                self.logger.info(
                    f"Downloaded: {self.total_downloaded:,} records - "
                    f"Rate: {rate:.1f} records/sec"
                )
    
    def create_exports(self):
        """Create CSV and JSON exports after download"""
        self.logger.info("Creating export files...")
        
        try:
            with SBIRDatabase() as db:
                # CSV export
                self.logger.info("Exporting to CSV...")
                db.export_to_csv(CSV_EXPORT_PATH)
                
                # Create summary statistics
                count = db.get_record_count()
                latest_date = db.get_latest_date()
                
                summary = {
                    "export_date": datetime.now().isoformat(),
                    "total_records": count,
                    "latest_award_date": latest_date,
                    "database_path": str(DATABASE_PATH),
                    "csv_path": str(CSV_EXPORT_PATH)
                }
                
                summary_path = DATA_DIR / "export_summary.json"
                with open(summary_path, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                self.logger.info(f"Export complete: {count:,} records")
                self.logger.info(f"CSV file: {CSV_EXPORT_PATH}")
                self.logger.info(f"Summary: {summary_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to create exports: {e}")

def main():
    """Main function"""
    print("SBIR Initial Data Download")
    print("=" * 50)
    
    downloader = SBIRInitialDownloader()
    
    # Check if this is a resume operation
    try:
        with SBIRDatabase() as db:
            existing_count = db.get_record_count()
            if existing_count > 0:
                print(f"Found existing database with {existing_count:,} records")
                resume = input("Resume download? (y/n): ").lower().startswith('y')
            else:
                resume = False
    except:
        resume = False
    
    print(f"Starting download (resume={resume})...")
    print("Press Ctrl+C to interrupt and save progress")
    print()
    
    # Start download
    success = downloader.download_all_awards(resume=resume)
    
    if success:
        print("\nDownload completed successfully!")
        print("Creating export files...")
        downloader.create_exports()
    else:
        print("\nDownload was interrupted or failed.")
        print("You can resume later by running this script again.")
    
    # Final statistics
    try:
        with SBIRDatabase() as db:
            final_count = db.get_record_count()
            print(f"\nFinal database contains {final_count:,} records")
            
            if db.get_metadata("download_interrupted") == "true":
                print("Note: Download was interrupted and can be resumed")
            
    except Exception as e:
        print(f"Could not get final statistics: {e}")

if __name__ == "__main__":
    main()