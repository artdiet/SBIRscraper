#!/usr/bin/env python3
"""
SBIR API Total Count Investigation
Tests different strategies to determine total record count in the database.
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.www.sbir.gov/public/api/awards"

def test_large_offset_strategy():
    """Test using large offset to find total records"""
    logger.info("Testing large offset strategy...")
    
    # Binary search approach to find total count
    low, high = 0, 1000000  # Start with assumption of max 1M records
    total_found = 0
    
    while low <= high:
        mid = (low + high) // 2
        
        try:
            params = {'start': mid, 'rows': 1}
            response = requests.get(API_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            records_returned = len(data) if isinstance(data, list) else len(data.get('docs', []))
            
            logger.info(f"  Offset {mid}: {records_returned} records returned")
            
            if records_returned > 0:
                total_found = mid + 1
                low = mid + 1
            else:
                high = mid - 1
                
            time.sleep(0.5)  # Be respectful to API
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request failed at offset {mid}: {e}")
            high = mid - 1
            
        # Safety break for very large searches
        if high - low > 100000:
            logger.info("  Breaking early to avoid excessive requests")
            break
    
    logger.info(f"Estimated total records: {total_found}")
    return total_found

def test_progressive_sampling():
    """Test progressive sampling to estimate total size"""
    logger.info("Testing progressive sampling strategy...")
    
    sample_points = [0, 1000, 5000, 10000, 25000, 50000, 100000]
    valid_offsets = []
    
    for offset in sample_points:
        try:
            params = {'start': offset, 'rows': 1}
            response = requests.get(API_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            records_returned = len(data) if isinstance(data, list) else len(data.get('docs', []))
            
            logger.info(f"  Offset {offset}: {records_returned} records")
            
            if records_returned > 0:
                valid_offsets.append(offset)
            else:
                logger.info(f"  No records at offset {offset} - likely near end")
                break
                
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  Failed at offset {offset}: {e}")
            break
    
    if valid_offsets:
        estimated_total = max(valid_offsets) + 1000  # Add buffer
        logger.info(f"Progressive sampling suggests at least {max(valid_offsets)} records")
        return estimated_total
    
    return 0

def test_api_metadata():
    """Check if API provides metadata about total count"""
    logger.info("Checking API response for total count metadata...")
    
    try:
        # Try different parameter combinations that might return metadata
        test_params = [
            {'start': 0, 'rows': 1},
            {'start': 0, 'rows': 0},  # Sometimes returns just metadata
            {'rows': 1},  # Without start parameter
            {}  # No parameters
        ]
        
        for i, params in enumerate(test_params, 1):
            logger.info(f"  Test {i}: {params}")
            
            response = requests.get(API_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict):
                logger.info(f"    Response keys: {list(data.keys())}")
                
                # Look for common total count fields
                total_fields = ['total', 'totalCount', 'numFound', 'count', 'totalRecords']
                for field in total_fields:
                    if field in data:
                        logger.info(f"    Found {field}: {data[field]}")
                        
                # Check if there's a different structure with Solr-style response
                if 'response' in data:
                    resp = data['response']
                    logger.info(f"    Response object keys: {list(resp.keys())}")
                    if 'numFound' in resp:
                        logger.info(f"    numFound in response: {resp['numFound']}")
                        
            elif isinstance(data, list):
                logger.info(f"    Got list with {len(data)} items")
                
            time.sleep(0.5)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Metadata test failed: {e}")

def analyze_sample_size():
    """Analyze a larger sample to estimate record characteristics"""
    logger.info("Analyzing larger sample for size estimation...")
    
    try:
        params = {'start': 0, 'rows': 100}
        response = requests.get(API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        records = data if isinstance(data, list) else data.get('docs', [])
        
        if records:
            # Calculate average record size
            total_size = 0
            for record in records:
                record_json = json.dumps(record)
                total_size += len(record_json.encode('utf-8'))
            
            avg_size_bytes = total_size / len(records)
            avg_size_kb = avg_size_bytes / 1024
            
            logger.info(f"Sample of {len(records)} records:")
            logger.info(f"  Average record size: {avg_size_bytes:.0f} bytes ({avg_size_kb:.2f} KB)")
            logger.info(f"  Total sample size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
            
            # Look at date ranges to estimate time span
            dates = []
            for record in records:
                if 'proposal_award_date' in record and record['proposal_award_date']:
                    dates.append(record['proposal_award_date'])
                    
            if dates:
                dates.sort()
                logger.info(f"  Date range in sample: {dates[0]} to {dates[-1]}")
                
            return avg_size_bytes
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Sample analysis failed: {e}")
        
    return 0

def main():
    """Run all count estimation tests"""
    logger.info("Starting SBIR API total count investigation...")
    
    # Test for metadata
    test_api_metadata()
    time.sleep(1)
    
    # Analyze sample characteristics
    avg_record_size = analyze_sample_size()
    time.sleep(1)
    
    # Progressive sampling
    progressive_estimate = test_progressive_sampling()
    time.sleep(1)
    
    # Binary search for exact count (commented out to avoid too many requests)
    # exact_count = test_large_offset_strategy()
    
    logger.info("\n" + "="*60)
    logger.info("TOTAL COUNT INVESTIGATION SUMMARY")
    logger.info("="*60)
    
    if avg_record_size > 0:
        logger.info(f"Average record size: {avg_record_size:.0f} bytes ({avg_record_size/1024:.2f} KB)")
        
        # Size estimates for different total counts
        for total_records in [10000, 50000, 100000, 250000, 500000, 1000000]:
            total_size_mb = (total_records * avg_record_size) / (1024 * 1024)
            logger.info(f"  {total_records:,} records = {total_size_mb:.1f} MB")
    
    if progressive_estimate > 0:
        logger.info(f"Progressive sampling estimate: At least {progressive_estimate:,} records")
        
    logger.info("\nRecommendations:")
    logger.info("- Use progressive downloading with checkpoints")
    logger.info("- Monitor actual count during full download")
    logger.info("- Plan for 100MB-1GB+ storage depending on total size")

if __name__ == "__main__":
    main()