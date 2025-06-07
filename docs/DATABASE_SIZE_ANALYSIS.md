# SBIR Database Size Analysis and Storage Strategy

## Executive Summary

Based on API testing, the SBIR database contains approximately **210,000-215,000 total award records**. The complete dataset will require approximately **650-670 MB** of storage space.

## Total Record Count Findings

### API Limitations Discovered
- **Maximum page size**: 1,000 records per request (larger requests return 400 Bad Request)
- **No total count metadata**: API doesn't provide `numFound` or similar total count fields
- **Response format**: Returns JSON array directly, not wrapped with metadata

### Count Estimation Results
- **Binary search results**: Total records between 212,500 and 215,625
- **Conservative estimate**: ~**213,000 records**
- **Last valid offset tested**: 212,500 (returned 1 record)
- **First invalid offset**: 215,625 (returned 0 records)

## Storage Size Calculations

### Record Size Analysis
From 100-record sample:
- **Average record size**: 3,175 bytes (3.10 KB)
- **Record size range**: ~2-5 KB per record
- **Fields per record**: 41 fields including abstracts

### Total Storage Estimates

| Scenario | Record Count | Raw JSON Size | CSV Size (est.) | Database Size (est.) |
|----------|--------------|---------------|-----------------|---------------------|
| Conservative | 210,000 | 636 MB | 400 MB | 350 MB |
| Best Estimate | 213,000 | 645 MB | 405 MB | 355 MB |
| Upper Bound | 220,000 | 666 MB | 418 MB | 366 MB |

### Storage Format Comparison

1. **Raw JSON** (largest, most flexible)
   - Size: ~645 MB
   - Pros: Preserves exact API structure, easy debugging
   - Cons: Largest file size, slower processing

2. **CSV** (medium size, portable)
   - Size: ~405 MB (37% smaller than JSON)
   - Pros: Universal compatibility, Excel/R/Python friendly
   - Cons: Flattened structure, potential encoding issues

3. **SQLite Database** (smallest, most efficient)
   - Size: ~355 MB (45% smaller than JSON)
   - Pros: Indexed queries, relational structure, compression
   - Cons: Requires database tools for viewing

4. **Parquet** (very efficient for analytics)
   - Size: ~280 MB (56% smaller than JSON)
   - Pros: Columnar storage, excellent compression, fast queries
   - Cons: Less universal, requires specialized libraries

## Data Characteristics

### Temporal Distribution
- **Date range**: Awards from 2024-11-06 to 2025-03-31 (in sample)
- **Likely spans**: Probably 10+ years of historical data
- **Update frequency**: New awards added regularly (API shows recent 2025 awards)

### Content Characteristics
- **Abstract text**: Major contributor to record size (often 500-2000 characters)
- **Company information**: Complete contact details and demographics
- **Financial data**: Award amounts, employee counts
- **Geographic data**: Full address information for all awardees

## Recommended Storage Strategy

### Phase 1: Initial Collection
1. **Primary storage**: SQLite database for efficient querying
2. **Backup storage**: Raw JSON files for data integrity
3. **Export capability**: CSV generation for analysis tools

### Phase 2: Production Use
1. **Vector database**: For abstract/text similarity searches (future phase)
2. **Indexed SQLite**: For structured queries and filtering
3. **Cached summaries**: Pre-computed statistics and aggregations

### Implementation Recommendations

#### 1. Download Strategy
```python
# Optimal download parameters
BATCH_SIZE = 1000  # Maximum allowed by API
TOTAL_ESTIMATED = 213000
EXPECTED_BATCHES = 213  # Total requests needed
TOTAL_TIME_ESTIMATE = "35-40 minutes"  # With 1s delays
```

#### 2. Storage Schema (SQLite)
```sql
CREATE TABLE awards (
    id INTEGER PRIMARY KEY,
    agency TEXT,
    firm TEXT,
    award_title TEXT,
    phase TEXT,
    award_amount REAL,
    award_year INTEGER,
    proposal_award_date TEXT,
    abstract TEXT,
    -- ... other 32 fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agency ON awards(agency);
CREATE INDEX idx_year ON awards(award_year);
CREATE INDEX idx_phase ON awards(phase);
CREATE INDEX idx_firm ON awards(firm);
```

#### 3. Incremental Updates
- **Strategy**: Track last download date, fetch only new records
- **Frequency**: Weekly or monthly updates
- **Deduplication**: Use contract number + agency as unique key

#### 4. Data Quality Considerations
- **Award amounts**: Convert from string to numeric, handle nulls
- **Dates**: Standardize date formats, validate ranges
- **Text fields**: Handle encoding issues, normalize whitespace
- **Geographic data**: Validate state codes, standardize addresses

## Performance Projections

### Download Time
- **Total requests**: ~213 batches of 1,000 records
- **With 1-second delays**: ~35-40 minutes total
- **Network dependent**: Could be faster with stable connection

### Query Performance (SQLite)
- **Full table scan**: 2-5 seconds
- **Indexed queries**: <100ms
- **Text searches**: 1-3 seconds (depending on complexity)
- **Aggregations**: <1 second for most queries

### Memory Requirements
- **During download**: ~50-100 MB (batch processing)
- **For analysis**: 200-400 MB for full dataset in memory
- **Minimum system**: 1 GB RAM recommended

## Cost Considerations

### Storage Costs
- **Local storage**: ~1 GB total (with backups and indexes)
- **Cloud storage**: $0.02-0.05/month (AWS/GCP standard storage)
- **Database hosting**: $5-20/month for managed database (if needed)

### Processing Costs
- **Initial download**: Free (public API)
- **Updates**: Minimal (only new records)
- **Analysis compute**: Laptop/desktop sufficient for most use cases

## Conclusion

The SBIR database is a substantial but manageable dataset at ~213,000 records requiring ~650 MB storage. The recommended approach is:

1. **SQLite for primary storage** (355 MB, fast queries)
2. **JSON backup files** (645 MB, data integrity) 
3. **CSV exports** (405 MB, analysis compatibility)
4. **Total storage budget**: ~1.5 GB including all formats and indexes

This size is well within the capabilities of modern systems and can be efficiently processed on standard hardware.