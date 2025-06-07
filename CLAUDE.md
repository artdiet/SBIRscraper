# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready SBIR Award Data Scraper and Analyzer that collects Small Business Innovation Research (SBIR) and Small Business Technology Transfer (STTR) program award data from the official SBIR.gov API. The system downloads ~213,000 awards and stores them in SQLite for analysis and research.

## Project Structure

```
sbir-scraper/
├── src/                    # Source code
│   ├── initial_download.py # Main download program
│   ├── update_checker.py   # Periodic update checker
│   ├── database.py         # Database management
│   └── api_test.py         # API testing utilities
├── config/
│   └── config.py          # Configuration management
├── data/                   # Database and exports (not in repo)
├── logs/                   # Application logs
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

## Common Development Tasks

### Initial Setup
```bash
pip install -r requirements.txt
python src/initial_download.py  # Downloads all awards (~35-40 min)
```

### Testing
```bash
python src/api_test.py          # Test API connectivity and schema
python src/database.py          # Test database functionality
python -m pytest tests/        # Run unit tests
```

### Updates
```bash
python src/update_checker.py           # Check for new awards
python src/update_checker.py --force   # Force update check
```

### Data Analysis
```bash
python -c "from src.database import SBIRDatabase; 
with SBIRDatabase() as db: 
    print(f'Records: {db.get_record_count():,}')"
```

## Technology Stack

- **Language**: Python 3.7+
- **Database**: SQLite with 41-field schema
- **HTTP**: requests library with rate limiting
- **Data**: pandas for processing, CSV export
- **Config**: Centralized in `config/config.py`

## API Details

- **Endpoint**: https://api.www.sbir.gov/public/api/awards
- **Total Records**: ~213,000 awards
- **Max Page Size**: 1,000 records (API limitation)
- **Rate Limiting**: 1-second delays between requests
- **Response Format**: JSON array of award objects

## Database Schema

41 fields per award including:
- Company details (firm, address, contacts)
- Award information (title, amount, dates, phase)
- Government data (agency, contract numbers)
- Demographics (women-owned, HUBZone status)
- Research data (abstract, keywords, topics)

## Configuration Management

All settings in `config/config.py`:
- `API_DELAY`: Request intervals (default: 1.0s)
- `BATCH_SIZE`: Records per request (max: 1000)
- `DATABASE_PATH`: SQLite file location
- `UPDATE_CHECK_DAYS`: Update frequency (default: 7 days)

## Error Handling & Logging

- Comprehensive logging to `logs/sbir_scraper.log`
- Automatic retry logic for failed API requests
- Graceful shutdown with progress checkpointing
- Resume capability for interrupted downloads
- Database backup and recovery

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Comprehensive docstrings for all functions
- Modular design with clear separation of concerns

### Testing
- Unit tests in `tests/` directory
- API integration tests in `src/api_test.py`
- Database validation tests
- Error condition testing

### Performance Considerations
- Batch processing for large datasets
- Memory-efficient streaming for exports
- Progress tracking and checkpointing
- Configurable rate limiting

## Future Enhancement Areas

1. **Vector Database Integration**: Store abstracts for semantic search
2. **Phase II Progression**: Track Phase I → Phase II success rates
3. **LLM Analysis**: Topic modeling and trend identification
4. **Web Interface**: Streamlit/Dash dashboard for data exploration
5. **Advanced Filtering**: Agency-specific exports (e.g., AFWERX)

## Troubleshooting

### Common Issues
- **Database locked**: Close applications accessing the DB
- **Network timeouts**: Increase `API_TIMEOUT` in config
- **Incomplete downloads**: Run initial_download.py to resume
- **Missing updates**: Use `--force` flag with update checker

### Debugging
- Check `logs/sbir_scraper.log` for detailed error information
- Use `src/api_test.py` to verify API connectivity
- Validate database with `python src/database.py`

## License & Distribution

- Proprietary license owned by DTRIQ LLC
- Public repository ready (data/ directory excluded)
- Commercial licensing available for enterprise use