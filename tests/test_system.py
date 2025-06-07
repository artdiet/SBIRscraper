#!/usr/bin/env python3
"""
Basic system tests for SBIR Scraper
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from config.config import API_BASE_URL, DATABASE_PATH
        from src.database import SBIRDatabase
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration settings"""
    try:
        from config.config import validate_config
        errors = validate_config()
        if errors:
            print(f"❌ Configuration errors: {errors}")
            return False
        else:
            print("✅ Configuration validation passed")
            return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    try:
        from src.database import SBIRDatabase
        
        # Test database creation
        with SBIRDatabase() as db:
            db.create_tables()
            print("✅ Database tables created successfully")
            
            # Test sample data with all required fields
            sample_award = {
                "firm": "Test Company",
                "award_title": "Test Award",
                "agency": "NSF",
                "branch": None,
                "phase": "Phase I",
                "program": "SBIR",
                "agency_tracking_number": "TEST123",
                "contract": "TEST123",
                "proposal_award_date": "2025-01-01",
                "contract_end_date": "2026-01-01",
                "solicitation_number": "TEST-2025",
                "solicitation_year": 2025,
                "topic_code": "T",
                "award_year": 2025,
                "award_amount": "100000.00",
                "duns": "123456789",
                "uei": "TESTCOMPANY123",
                "hubzone_owned": "N",
                "socially_economically_disadvantaged": "N",
                "women_owned": "N",
                "number_employees": 10,
                "company_url": "https://test.com",
                "address1": "123 Test St",
                "address2": "",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "poc_name": "Test Person",
                "poc_title": "CEO",
                "poc_phone": "555-1234",
                "poc_email": "test@test.com",
                "pi_name": "Test PI",
                "pi_title": "Principal Investigator",
                "pi_phone": "555-1234",
                "pi_email": "pi@test.com",
                "ri_name": None,
                "ri_poc_name": "",
                "ri_poc_phone": None,
                "research_area_keywords": None,
                "abstract": "This is a test award for system validation.",
                "award_link": 12345
            }
            
            db.insert_awards([sample_award])
            count = db.get_record_count()
            print(f"✅ Database test successful - {count} records")
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity"""
    try:
        import requests
        from config.config import API_BASE_URL, get_user_agent
        
        response = requests.get(
            API_BASE_URL,
            params={'start': 0, 'rows': 1},
            headers={'User-Agent': get_user_agent()},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            print("✅ API connectivity test passed")
            return True
        else:
            print("❌ API returned unexpected data format")
            return False
            
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("SBIR Scraper System Tests")
    print("=" * 30)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("API Connectivity", test_api_connectivity)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"Test {test_name} failed!")
    
    print(f"\n" + "=" * 30)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)