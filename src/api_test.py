#!/usr/bin/env python3
"""
SBIR API Test Program
Tests the SBIR.gov API, extracts data schema, and samples awards.
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "https://api.www.sbir.gov/public/api/awards"
SAMPLE_SIZE = 10
REQUEST_DELAY = 1  # seconds between requests

class SBIRAPITester:
    """Test the SBIR API and extract data schema"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SBIR-Scraper-Test/1.0'
        })
    
    def test_api_connection(self) -> Dict[str, Any]:
        """Test basic API connection and get initial response"""
        logger.info("Testing API connection...")
        
        try:
            # Make initial request with small page size
            params = {
                'start': 0,
                'rows': 1
            }
            
            response = self.session.get(API_BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"API connection successful. Status: {response.status_code}")
            
            # Handle different response formats
            if isinstance(data, list):
                logger.info(f"API returned list with {len(data)} items")
                formatted_data = {
                    'docs': data,
                    'numFound': len(data),
                    'start': 0
                }
            elif isinstance(data, dict):
                logger.info(f"Total awards available: {data.get('numFound', 'Unknown')}")
                formatted_data = data
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                formatted_data = {'docs': [], 'numFound': 0, 'start': 0}
            
            return formatted_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API connection failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise
    
    def extract_schema(self, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and analyze the data schema from API response"""
        logger.info("Extracting data schema...")
        
        schema = {
            'response_structure': {},
            'award_fields': {},
            'sample_award': None
        }
        
        # Analyze response structure
        schema['response_structure'] = {
            'top_level_keys': list(sample_data.keys()),
            'total_records': sample_data.get('numFound'),
            'records_returned': len(sample_data.get('docs', [])),
            'start_offset': sample_data.get('start')
        }
        
        # Analyze award fields if we have docs
        docs = sample_data.get('docs', [])
        if docs:
            first_award = docs[0]
            schema['sample_award'] = first_award
            
            # Get field types and sample values
            for field, value in first_award.items():
                schema['award_fields'][field] = {
                    'type': type(value).__name__,
                    'sample_value': str(value)[:100] + '...' if len(str(value)) > 100 else value,
                    'is_null': value is None
                }
        
        return schema
    
    def sample_awards(self, num_samples: int = SAMPLE_SIZE) -> List[Dict[str, Any]]:
        """Sample multiple awards from the API"""
        logger.info(f"Sampling {num_samples} awards...")
        
        try:
            params = {
                'start': 0,
                'rows': num_samples
            }
            
            response = self.session.get(API_BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                awards = data
            elif isinstance(data, dict):
                awards = data.get('docs', [])
            else:
                awards = []
            
            logger.info(f"Successfully retrieved {len(awards)} sample awards")
            return awards
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to sample awards: {e}")
            raise
    
    def test_pagination(self) -> Dict[str, Any]:
        """Test API pagination functionality"""
        logger.info("Testing pagination...")
        
        try:
            # Get first page
            page1_params = {'start': 0, 'rows': 5}
            response1 = self.session.get(API_BASE_URL, params=page1_params, timeout=30)
            response1.raise_for_status()
            data1 = response1.json()
            
            time.sleep(REQUEST_DELAY)
            
            # Get second page
            page2_params = {'start': 5, 'rows': 5}
            response2 = self.session.get(API_BASE_URL, params=page2_params, timeout=30)
            response2.raise_for_status()
            data2 = response2.json()
            
            # Handle different response formats
            if isinstance(data1, list):
                docs1, total1 = data1, len(data1)
            else:
                docs1, total1 = data1.get('docs', []), data1.get('numFound', 0)
                
            if isinstance(data2, list):
                docs2, total2 = data2, len(data2)
            else:
                docs2, total2 = data2.get('docs', []), data2.get('numFound', 0)
            
            pagination_info = {
                'page1_count': len(docs1),
                'page2_count': len(docs2),
                'total_available': max(total1, total2),
                'pagination_working': len(docs1) > 0 and len(docs2) > 0
            }
            
            logger.info(f"Pagination test results: {pagination_info}")
            return pagination_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Pagination test failed: {e}")
            raise
    
    def print_schema_report(self, schema: Dict[str, Any]):
        """Print formatted schema report"""
        print("\n" + "="*60)
        print("SBIR API DATA SCHEMA REPORT")
        print("="*60)
        
        print(f"\nAPI Response Structure:")
        print(f"  Total Records Available: {schema['response_structure']['total_records']:,}")
        print(f"  Top-level Keys: {', '.join(schema['response_structure']['top_level_keys'])}")
        
        print(f"\nAward Fields ({len(schema['award_fields'])} total):")
        for field, info in schema['award_fields'].items():
            print(f"  {field:25} | {info['type']:10} | {str(info['sample_value'])[:50]}")
        
        print("\n" + "="*60)
    
    def print_sample_awards(self, awards: List[Dict[str, Any]]):
        """Print formatted sample awards"""
        print(f"\nSAMPLE AWARDS ({len(awards)} awards):")
        print("="*60)
        
        for i, award in enumerate(awards, 1):
            print(f"\nAward #{i}:")
            print(f"  Title: {award.get('award_title', 'N/A')}")
            print(f"  Company: {award.get('firm', 'N/A')}")
            print(f"  Agency: {award.get('agency', 'N/A')}")
            print(f"  Phase: {award.get('phase', 'N/A')}")
            print(f"  Amount: ${award.get('award_amount', 'N/A')}")
            print(f"  Date: {award.get('proposal_award_date', 'N/A')}")
            
            # Show first 200 chars of abstract
            abstract = award.get('abstract', 'N/A')
            if abstract and len(abstract) > 200:
                abstract = abstract[:200] + "..."
            print(f"  Abstract: {abstract}")
            print("-" * 40)

def main():
    """Main test function"""
    logger.info("Starting SBIR API test program...")
    
    tester = SBIRAPITester()
    
    try:
        # Test API connection and get initial data
        initial_data = tester.test_api_connection()
        
        # Extract schema
        schema = tester.extract_schema(initial_data)
        
        # Print schema report
        tester.print_schema_report(schema)
        
        # Sample awards
        sample_awards = tester.sample_awards(SAMPLE_SIZE)
        
        # Print sample awards
        tester.print_sample_awards(sample_awards)
        
        # Test pagination
        pagination_info = tester.test_pagination()
        print(f"\nPagination Test: {'PASSED' if pagination_info['pagination_working'] else 'FAILED'}")
        
        logger.info("API test completed successfully!")
        
        return {
            'schema': schema,
            'sample_awards': sample_awards,
            'pagination_info': pagination_info
        }
        
    except Exception as e:
        logger.error(f"API test failed: {e}")
        raise

if __name__ == "__main__":
    main()