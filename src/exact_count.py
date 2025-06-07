#!/usr/bin/env python3
"""
Find exact total count using binary search approach
"""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.www.sbir.gov/public/api/awards"

def find_exact_count():
    """Use binary search to find exact total count"""
    logger.info("Finding exact total count using binary search...")
    
    # Start with a reasonable upper bound
    low, high = 100000, 500000
    last_valid_offset = 0
    
    # First, find a reasonable upper bound
    logger.info("Finding upper bound...")
    test_offsets = [200000, 300000, 400000, 500000, 750000, 1000000]
    
    for offset in test_offsets:
        try:
            params = {'start': offset, 'rows': 1}
            response = requests.get(API_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            records_returned = len(data) if isinstance(data, list) else len(data.get('docs', []))
            
            logger.info(f"  Testing offset {offset:,}: {records_returned} records")
            
            if records_returned > 0:
                last_valid_offset = offset
                low = offset
            else:
                high = offset
                logger.info(f"  Found upper bound at {offset:,}")
                break
                
            time.sleep(0.3)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request failed at offset {offset:,}: {e}")
            high = offset
            break
    
    # Now binary search between low and high
    logger.info(f"Binary searching between {low:,} and {high:,}...")
    
    iteration = 0
    while low < high and iteration < 20:  # Safety limit
        iteration += 1
        mid = (low + high) // 2
        
        try:
            params = {'start': mid, 'rows': 1}
            response = requests.get(API_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            records_returned = len(data) if isinstance(data, list) else len(data.get('docs', []))
            
            logger.info(f"  Iteration {iteration}: offset {mid:,} -> {records_returned} records")
            
            if records_returned > 0:
                last_valid_offset = mid
                low = mid + 1
            else:
                high = mid
                
            time.sleep(0.3)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request failed at offset {mid:,}: {e}")
            high = mid
    
    # Refine the exact boundary
    logger.info(f"Refining exact count around {last_valid_offset:,}...")
    
    # Check a few offsets around the last valid one
    for offset in range(last_valid_offset, last_valid_offset + 100):
        try:
            params = {'start': offset, 'rows': 1}
            response = requests.get(API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            records_returned = len(data) if isinstance(data, list) else len(data.get('docs', []))
            
            if records_returned == 0:
                logger.info(f"  Exact total count: {offset:,}")
                return offset
            
            time.sleep(0.2)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request failed at offset {offset:,}: {e}")
            break
    
    logger.info(f"  Estimated total count: {last_valid_offset + 1:,}")
    return last_valid_offset + 1

def test_large_page_size():
    """Test what happens with very large page sizes"""
    logger.info("Testing large page sizes...")
    
    page_sizes = [1000, 2000, 5000, 10000]
    
    for page_size in page_sizes:
        try:
            params = {'start': 0, 'rows': page_size}
            response = requests.get(API_BASE_URL, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            records_returned = len(data) if isinstance(data, list) else len(data.get('docs', []))
            
            logger.info(f"  Page size {page_size}: got {records_returned} records")
            
            if records_returned < page_size:
                logger.info(f"  -> This suggests total records ≤ {records_returned}")
                return records_returned
                
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Failed with page size {page_size}: {e}")
            
    return None

def main():
    """Run exact count determination"""
    logger.info("Starting exact count determination...")
    
    # Try large page size first (fastest method)
    large_page_result = test_large_page_size()
    
    if large_page_result:
        logger.info(f"\nExact count from large page test: {large_page_result:,}")
    else:
        # Fall back to binary search
        exact_count = find_exact_count()
        logger.info(f"\nExact count from binary search: {exact_count:,}")

if __name__ == "__main__":
    main()