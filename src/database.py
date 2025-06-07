#!/usr/bin/env python3
"""
Database management for SBIR Awards
"""

import sqlite3
import logging
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config.config import DATABASE_PATH, BACKUP_DATABASE_PATH

logger = logging.getLogger(__name__)

class SBIRDatabase:
    """Manages SQLite database for SBIR awards"""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from database")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        create_awards_sql = """
        CREATE TABLE IF NOT EXISTS awards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm TEXT,
            award_title TEXT,
            agency TEXT,
            branch TEXT,
            phase TEXT,
            program TEXT,
            agency_tracking_number TEXT,
            contract TEXT,
            proposal_award_date TEXT,
            contract_end_date TEXT,
            solicitation_number TEXT,
            solicitation_year INTEGER,
            topic_code TEXT,
            award_year INTEGER,
            award_amount REAL,
            duns TEXT,
            uei TEXT,
            hubzone_owned TEXT,
            socially_economically_disadvantaged TEXT,
            women_owned TEXT,
            number_employees INTEGER,
            company_url TEXT,
            address1 TEXT,
            address2 TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            poc_name TEXT,
            poc_title TEXT,
            poc_phone TEXT,
            poc_email TEXT,
            pi_name TEXT,
            pi_title TEXT,
            pi_phone TEXT,
            pi_email TEXT,
            ri_name TEXT,
            ri_poc_name TEXT,
            ri_poc_phone TEXT,
            research_area_keywords TEXT,
            abstract TEXT,
            award_link INTEGER,
            raw_data TEXT,  -- JSON string of original API response
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(contract, agency, agency_tracking_number)
        );
        """
        
        create_metadata_sql = """
        CREATE TABLE IF NOT EXISTS scraper_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_agency ON awards(agency);",
            "CREATE INDEX IF NOT EXISTS idx_firm ON awards(firm);",
            "CREATE INDEX IF NOT EXISTS idx_phase ON awards(phase);",
            "CREATE INDEX IF NOT EXISTS idx_award_year ON awards(award_year);",
            "CREATE INDEX IF NOT EXISTS idx_proposal_date ON awards(proposal_award_date);",
            "CREATE INDEX IF NOT EXISTS idx_contract ON awards(contract);",
            "CREATE INDEX IF NOT EXISTS idx_created_at ON awards(created_at);",
        ]
        
        try:
            cursor = self.connection.cursor()
            
            # Create tables
            cursor.execute(create_awards_sql)
            cursor.execute(create_metadata_sql)
            
            # Create indexes
            for index_sql in create_indexes_sql:
                cursor.execute(index_sql)
            
            self.connection.commit()
            logger.info("Database tables and indexes created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def insert_awards(self, awards: List[Dict[str, Any]]) -> int:
        """Insert multiple awards into database"""
        if not awards:
            return 0
        
        insert_sql = """
        INSERT OR REPLACE INTO awards (
            firm, award_title, agency, branch, phase, program,
            agency_tracking_number, contract, proposal_award_date, contract_end_date,
            solicitation_number, solicitation_year, topic_code, award_year,
            award_amount, duns, uei, hubzone_owned, socially_economically_disadvantaged,
            women_owned, number_employees, company_url, address1, address2,
            city, state, zip, poc_name, poc_title, poc_phone, poc_email,
            pi_name, pi_title, pi_phone, pi_email, ri_name, ri_poc_name,
            ri_poc_phone, research_area_keywords, abstract, award_link, raw_data,
            updated_at
        ) VALUES (
            :firm, :award_title, :agency, :branch, :phase, :program,
            :agency_tracking_number, :contract, :proposal_award_date, :contract_end_date,
            :solicitation_number, :solicitation_year, :topic_code, :award_year,
            :award_amount, :duns, :uei, :hubzone_owned, :socially_economically_disadvantaged,
            :women_owned, :number_employees, :company_url, :address1, :address2,
            :city, :state, :zip, :poc_name, :poc_title, :poc_phone, :poc_email,
            :pi_name, :pi_title, :pi_phone, :pi_email, :ri_name, :ri_poc_name,
            :ri_poc_phone, :research_area_keywords, :abstract, :award_link, :raw_data,
            CURRENT_TIMESTAMP
        );
        """
        
        try:
            processed_awards = []
            for award in awards:
                processed_award = self._process_award_for_db(award)
                processed_awards.append(processed_award)
            
            cursor = self.connection.cursor()
            cursor.executemany(insert_sql, processed_awards)
            self.connection.commit()
            
            inserted_count = cursor.rowcount
            logger.info(f"Inserted {inserted_count} awards into database")
            return inserted_count
            
        except sqlite3.Error as e:
            logger.error(f"Failed to insert awards: {e}")
            raise
    
    def _process_award_for_db(self, award: Dict[str, Any]) -> Dict[str, Any]:
        """Process award data for database insertion"""
        processed = award.copy()
        
        # Convert award_amount to float
        if 'award_amount' in processed and processed['award_amount']:
            try:
                processed['award_amount'] = float(str(processed['award_amount']).replace(',', ''))
            except (ValueError, TypeError):
                processed['award_amount'] = None
        
        # Store raw JSON data
        processed['raw_data'] = json.dumps(award)
        
        # Handle None values for integer fields
        int_fields = ['solicitation_year', 'award_year', 'number_employees', 'award_link']
        for field in int_fields:
            if field in processed and processed[field] is not None:
                try:
                    processed[field] = int(processed[field])
                except (ValueError, TypeError):
                    processed[field] = None
        
        return processed
    
    def get_record_count(self) -> int:
        """Get total number of records in database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM awards")
            count = cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(f"Failed to get record count: {e}")
            return 0
    
    def get_latest_date(self) -> Optional[str]:
        """Get the latest proposal_award_date in the database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT MAX(proposal_award_date) 
                FROM awards 
                WHERE proposal_award_date IS NOT NULL
            """)
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get latest date: {e}")
            return None
    
    def set_metadata(self, key: str, value: str):
        """Set a metadata value"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO scraper_metadata (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            self.connection.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to set metadata {key}: {e}")
            raise
    
    def get_metadata(self, key: str) -> Optional[str]:
        """Get a metadata value"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT value FROM scraper_metadata WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get metadata {key}: {e}")
            return None
    
    def backup_database(self) -> bool:
        """Create a backup of the database"""
        try:
            if self.db_path.exists():
                shutil.copy2(self.db_path, BACKUP_DATABASE_PATH)
                logger.info(f"Database backed up to {BACKUP_DATABASE_PATH}")
                return True
            else:
                logger.warning("No database file found to backup")
                return False
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def export_to_csv(self, output_path: Path, limit: Optional[int] = None):
        """Export awards to CSV file"""
        import csv
        
        try:
            cursor = self.connection.cursor()
            
            # Get column names (excluding raw_data)
            cursor.execute("PRAGMA table_info(awards)")
            columns = [col[1] for col in cursor.fetchall() if col[1] not in ['raw_data', 'id']]
            
            # Build query
            query = f"SELECT {', '.join(columns)} FROM awards ORDER BY proposal_award_date DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                
                for row in cursor.fetchall():
                    writer.writerow(dict(row))
            
            logger.info(f"Exported awards to CSV: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise

def test_database():
    """Test database functionality"""
    print("Testing database functionality...")
    
    with SBIRDatabase() as db:
        db.create_tables()
        
        # Test sample data
        sample_award = {
            "firm": "Test Company",
            "award_title": "Test Award",
            "agency": "NSF",
            "phase": "Phase I",
            "program": "SBIR",
            "contract": "TEST123",
            "award_amount": "100000.00",
            "proposal_award_date": "2025-01-01"
        }
        
        db.insert_awards([sample_award])
        count = db.get_record_count()
        print(f"Records in database: {count}")
        
        # Test metadata
        db.set_metadata("test_key", "test_value")
        value = db.get_metadata("test_key")
        print(f"Metadata test: {value}")

if __name__ == "__main__":
    test_database()