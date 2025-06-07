#!/usr/bin/env python3
"""
SBIR Update Checker
Periodically checks for new awards and updates the database.
"""

import requests
import time
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config.config import *
from src.database import SBIRDatabase

class SBIRUpdateChecker:
    """Checks for and downloads new SBIR awards"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': get_user_agent()
        })
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.new_records_found = 0
        self.updated_records = 0
    
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
    
    def get_last_update_date(self) -> Optional[datetime]:
        """Get the last update check date from database"""
        try:
            with SBIRDatabase() as db:
                last_update_str = db.get_metadata("last_update_check")
                if last_update_str:
                    return datetime.fromisoformat(last_update_str)
        except Exception as e:
            self.logger.error(f"Failed to get last update date: {e}")
        
        return None
    
    def should_check_for_updates(self) -> bool:
        """Determine if we should check for updates"""
        last_update = self.get_last_update_date()
        
        if not last_update:
            self.logger.info("No previous update check found")
            return True
        
        days_since_update = (datetime.now() - last_update).days
        
        if days_since_update >= UPDATE_CHECK_DAYS:
            self.logger.info(f"Last update was {days_since_update} days ago, checking for updates")
            return True
        else:
            self.logger.info(f"Last update was {days_since_update} days ago, no check needed")
            return False
    
    def get_existing_contracts(self) -> Set[str]:
        """Get set of existing contract numbers from database"""
        contracts = set()
        
        try:
            with SBIRDatabase() as db:
                cursor = db.connection.cursor()
                cursor.execute("SELECT DISTINCT contract FROM awards WHERE contract IS NOT NULL")
                contracts = {row[0] for row in cursor.fetchall()}
                
            self.logger.info(f"Found {len(contracts)} existing contracts in database")
            
        except Exception as e:
            self.logger.error(f"Failed to get existing contracts: {e}")
        
        return contracts
    
    def fetch_recent_awards(self, days_back: int = UPDATE_LOOKBACK_DAYS) -> List[Dict[str, Any]]:
        """Fetch awards from recent period to check for updates"""
        self.logger.info(f"Fetching awards from last {days_back} days...")
        
        all_recent_awards = []
        offset = 0
        
        # Calculate date threshold
        threshold_date = datetime.now() - timedelta(days=days_back)
        threshold_str = threshold_date.strftime("%Y-%m-%d")
        
        while True:
            try:
                params = {
                    'start': offset,
                    'rows': BATCH_SIZE
                }
                
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
                    break
                
                if not awards:
                    self.logger.info("No more awards found, stopping search")
                    break
                
                # Filter for recent awards
                recent_awards = []
                for award in awards:
                    award_date = award.get('proposal_award_date', '')
                    if award_date and award_date >= threshold_str:
                        recent_awards.append(award)
                
                all_recent_awards.extend(recent_awards)
                
                # If no recent awards in this batch, check if we've gone too far back
                if not recent_awards:
                    # Check if all awards in batch are older than threshold
                    latest_in_batch = max([a.get('proposal_award_date', '') for a in awards if a.get('proposal_award_date')])
                    if latest_in_batch < threshold_str:
                        self.logger.info(f"Reached awards older than {threshold_str}, stopping search")
                        break
                
                offset += len(awards)
                self.logger.debug(f"Processed {offset} total awards, found {len(all_recent_awards)} recent")
                
                # Rate limiting
                time.sleep(API_DELAY)
                
                # Safety limit
                if offset >= 10000:  # Don't search more than 10k records
                    self.logger.warning("Reached safety limit of 10,000 records searched")
                    break
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed while fetching recent awards: {e}")
                break
            
            except Exception as e:
                self.logger.error(f"Unexpected error while fetching recent awards: {e}")
                break
        
        self.logger.info(f"Found {len(all_recent_awards)} awards from last {days_back} days")
        return all_recent_awards
    
    def identify_new_awards(self, recent_awards: List[Dict[str, Any]], existing_contracts: Set[str]) -> List[Dict[str, Any]]:
        """Identify awards that are new (not in existing database)"""
        new_awards = []
        
        for award in recent_awards:
            contract = award.get('contract')
            if contract and contract not in existing_contracts:
                new_awards.append(award)
        
        self.logger.info(f"Identified {len(new_awards)} new awards")
        return new_awards
    
    def check_for_updates(self, force: bool = False) -> bool:
        """Check for and download new awards"""
        self.logger.info("Starting update check...")
        
        if not force and not self.should_check_for_updates():
            return True
        
        try:
            # Get existing contracts for duplicate detection
            existing_contracts = self.get_existing_contracts()
            
            # Fetch recent awards
            recent_awards = self.fetch_recent_awards(UPDATE_LOOKBACK_DAYS)
            
            if not recent_awards:
                self.logger.info("No recent awards found")
                self.update_metadata()
                return True
            
            # Identify new awards
            new_awards = self.identify_new_awards(recent_awards, existing_contracts)
            
            if not new_awards:
                self.logger.info("No new awards found")
                self.update_metadata()
                return True
            
            # Insert new awards
            with SBIRDatabase() as db:
                inserted = db.insert_awards(new_awards)
                self.new_records_found = inserted
                
                self.logger.info(f"Successfully added {inserted} new awards to database")
                
                # Update exports if new records were added
                if inserted > 0:
                    self.logger.info("Updating CSV export...")
                    db.export_to_csv(CSV_EXPORT_PATH)
            
            self.update_metadata()
            return True
            
        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            return False
    
    def update_metadata(self):
        """Update metadata with latest check information"""
        try:
            with SBIRDatabase() as db:
                db.set_metadata("last_update_check", datetime.now().isoformat())
                db.set_metadata("last_update_new_records", str(self.new_records_found))
                
        except Exception as e:
            self.logger.error(f"Failed to update metadata: {e}")
    
    def get_update_summary(self) -> Dict[str, Any]:
        """Get summary of update check results"""
        try:
            with SBIRDatabase() as db:
                total_records = db.get_record_count()
                last_check = db.get_metadata("last_update_check")
                last_new_records = db.get_metadata("last_update_new_records")
                
                return {
                    "total_records": total_records,
                    "last_check_date": last_check,
                    "new_records_last_check": int(last_new_records or 0),
                    "new_records_this_check": self.new_records_found
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get update summary: {e}")
            return {}

def run_update_check(force: bool = False):
    """Run the update check process"""
    print("SBIR Update Checker")
    print("=" * 30)
    
    checker = SBIRUpdateChecker()
    
    # Check if initial download is complete
    try:
        with SBIRDatabase() as db:
            initial_complete = db.get_metadata("initial_download_completed")
            if not initial_complete:
                print("Initial download has not been completed.")
                print("Please run initial_download.py first.")
                return False
    except Exception:
        print("Database not found. Please run initial_download.py first.")
        return False
    
    # Run update check
    success = checker.check_for_updates(force=force)
    
    if success:
        summary = checker.get_update_summary()
        print("\nUpdate Check Complete!")
        print(f"Total records in database: {summary.get('total_records', 'Unknown'):,}")
        print(f"New records found: {summary.get('new_records_this_check', 0)}")
        
        if summary.get('last_check_date'):
            print(f"Last check: {summary.get('last_check_date')}")
    else:
        print("\nUpdate check failed. Check logs for details.")
    
    return success

def setup_cron_job():
    """Provide instructions for setting up automated updates"""
    script_path = Path(__file__).absolute()
    
    print("\nTo setup automated weekly updates, add this to your crontab:")
    print(f"0 2 * * 0 cd {script_path.parent.parent} && python3 {script_path}")
    print("\nThis will run the update checker every Sunday at 2 AM.")
    print("To edit crontab: crontab -e")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SBIR Update Checker")
    parser.add_argument("--force", action="store_true", 
                       help="Force update check even if recently checked")
    parser.add_argument("--setup-cron", action="store_true",
                       help="Show instructions for setting up automated updates")
    
    args = parser.parse_args()
    
    if args.setup_cron:
        setup_cron_job()
        return
    
    success = run_update_check(force=args.force)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()