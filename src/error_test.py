#!/usr/bin/env python3
"""
SBIR API Error Handling Test
Tests various error conditions and API edge cases.
"""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_invalid_url():
    """Test handling of invalid API URL"""
    logger.info("Testing invalid URL handling...")
    
    invalid_url = "https://api.www.sbir.gov/public/api/invalid_endpoint"
    
    try:
        response = requests.get(invalid_url, timeout=10)
        response.raise_for_status()
        logger.info("Unexpected success with invalid URL")
    except requests.exceptions.HTTPError as e:
        logger.info(f"Correctly handled HTTP error: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.info(f"Correctly handled request error: {e}")

def test_network_timeout():
    """Test network timeout handling"""
    logger.info("Testing timeout handling...")
    
    try:
        response = requests.get("https://api.www.sbir.gov/public/api/awards", timeout=0.001)
        logger.warning("Request completed faster than expected")
    except requests.exceptions.Timeout:
        logger.info("Correctly handled timeout")
    except requests.exceptions.RequestException as e:
        logger.info(f"Request failed with: {e}")

def test_large_request():
    """Test requesting large number of records"""
    logger.info("Testing large request...")
    
    try:
        params = {'start': 0, 'rows': 1000}  # Try to get 1000 records
        response = requests.get("https://api.www.sbir.gov/public/api/awards", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list):
            records = len(data)
        else:
            records = len(data.get('docs', []))
            
        logger.info(f"Successfully retrieved {records} records from large request")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Large request failed: {e}")

def test_malformed_params():
    """Test API with malformed parameters"""
    logger.info("Testing malformed parameters...")
    
    test_cases = [
        {'start': -1, 'rows': 10},  # Negative start
        {'start': 0, 'rows': -1},   # Negative rows  
        {'start': 'invalid', 'rows': 10},  # Non-numeric start
        {'start': 0, 'rows': 0},    # Zero rows
    ]
    
    for i, params in enumerate(test_cases, 1):
        try:
            logger.info(f"Test case {i}: {params}")
            response = requests.get("https://api.www.sbir.gov/public/api/awards", params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"  Unexpected success - got {len(data) if isinstance(data, list) else 'dict'}")
            
        except requests.exceptions.RequestException as e:
            logger.info(f"  Correctly handled error: {type(e).__name__}")

def main():
    """Run all error tests"""
    logger.info("Starting SBIR API error handling tests...")
    
    test_invalid_url()
    time.sleep(1)
    
    test_network_timeout() 
    time.sleep(1)
    
    test_large_request()
    time.sleep(1)
    
    test_malformed_params()
    
    logger.info("Error handling tests completed!")

if __name__ == "__main__":
    main()