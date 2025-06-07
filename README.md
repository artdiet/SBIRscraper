# SBIR Award Data Scraper

A Python-based tool to automatically collect Small Business Innovation Research (SBIR) and Small Business Technology Transfer (STTR) program award data from the official SBIR.gov API. This tool provides comprehensive data extraction, local storage, and analysis capabilities for SBIR/STTR research and proposal development.

## Features

- **Complete Data Collection**: Downloads all available SBIR/STTR awards (~213,000 records)
- **Robust Storage**: SQLite database with full-text search capabilities
- **Incremental Updates**: Periodic checking for new awards
- **Multiple Export Formats**: CSV export for analysis tools
- **Production Ready**: Comprehensive error handling, logging, and resume capability
- **Research Tools**: Foundation for trend analysis and proposal development

## Quick Start

### Prerequisites

- Python 3.7+
- Internet connection for API access
- ~1GB free disk space

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dtriq/sbir-scraper.git
cd sbir-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run initial data download:
```bash
python src/initial_download.py
```

This will download all available SBIR awards (estimated 35-40 minutes) and create a SQLite database in the `data/` directory.

### Basic Usage

**Check for new awards:**
```bash
python src/update_checker.py
```

**Force update check:**
```bash
python src/update_checker.py --force
```

**Setup automated weekly updates:**
```bash
python src/update_checker.py --setup-cron
```

## Project Structure

```
sbir-scraper/
├── src/                    # Source code
│   ├── initial_download.py # Initial data download
│   ├── update_checker.py   # Periodic updates
│   ├── database.py         # Database management
│   └── api_test.py         # API testing utilities
├── config/                 # Configuration
│   └── config.py          # Settings and parameters
├── data/                   # Data storage (not in repo)
│   ├── sbir_awards.db     # SQLite database
│   └── sbir_awards.csv    # CSV export
├── logs/                   # Application logs
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

## Data Schema

Each award record contains 41 fields including:

- **Company Information**: Firm name, address, contact details
- **Award Details**: Title, abstract, amount, dates, phase
- **Government Data**: Agency, contract numbers, tracking IDs
- **Demographics**: Women-owned, HUBZone status, employee count
- **Technical**: Topic codes, research keywords

See `docs/API_FINDINGS.md` for complete field documentation.

## Database Information

- **Total Records**: ~213,000 SBIR/STTR awards
- **Database Size**: ~355MB (SQLite)
- **CSV Export Size**: ~405MB
- **Time Range**: Historical data spanning 10+ years
- **Update Frequency**: New awards added regularly

## Configuration

Key settings in `config/config.py`:

- `API_DELAY`: Time between requests (default: 1 second)
- `BATCH_SIZE`: Records per request (max: 1000)
- `UPDATE_CHECK_DAYS`: Days between update checks (default: 7)
- `DATABASE_PATH`: SQLite database location

## Advanced Usage

### Custom Queries

Access the SQLite database directly for custom analysis:

```python
from src.database import SBIRDatabase

with SBIRDatabase() as db:
    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT agency, COUNT(*) as count, AVG(award_amount) as avg_amount
        FROM awards 
        WHERE award_year = 2024
        GROUP BY agency
        ORDER BY count DESC
    """)
    results = cursor.fetchall()
```

### Export Specific Data

```python
from src.database import SBIRDatabase

with SBIRDatabase() as db:
    # Export specific agency data
    db.export_to_csv("nsf_awards.csv", 
                     where_clause="WHERE agency = 'NSF'")
```

## Research Applications

This dataset enables analysis of:

- **Funding Trends**: Agency priorities and funding patterns
- **Success Factors**: Phase I to Phase II progression rates
- **Market Intelligence**: Company capabilities and competitive landscape
- **Geographic Analysis**: Regional innovation clusters
- **Topic Analysis**: Research area trends and opportunities

## API Rate Limiting

The tool implements responsible API usage:

- 1-second delays between requests
- Automatic retry logic for failed requests
- Graceful handling of network issues
- Progress checkpointing for large downloads

## Troubleshooting

**Database locked error:**
- Close any applications accessing the database
- Check for multiple running instances

**Network timeout:**
- Check internet connection
- Increase `API_TIMEOUT` in config

**Incomplete download:**
- Run `initial_download.py` again to resume

**Missing new records:**
- Use `--force` flag with update checker
- Check `UPDATE_LOOKBACK_DAYS` setting

## Development

### Running Tests

```bash
python -m pytest tests/
```

### API Testing

```bash
python src/api_test.py
```

### Database Validation

```bash
python src/database.py
```

## Data Quality

The scraper implements several data quality measures:

- **Validation**: Required field checking
- **Deduplication**: Contract number-based uniqueness
- **Normalization**: Consistent data formatting
- **Backup**: Automatic database backups
- **Logging**: Comprehensive operation tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is proprietary software owned by DTRIQ LLC. See `LICENSE` for details.

## Support

For questions or issues:

- Check the documentation in `docs/`
- Review logs in `logs/sbir_scraper.log`
- Open an issue on GitHub
- Contact: Art Dietrich <art.dietrich@dtriq.com>

## Author

**Art Dietrich**  
DTRIQ LLC  
Email: art.dietrich@dtriq.com  
Website: https://www.dtriq.com

## Acknowledgments

- Data source: [SBIR.gov](https://www.sbir.gov/) - official U.S. government SBIR/STTR database
- Built for research and proposal development purposes
- Designed for responsible API usage and data stewardship

---

**Note**: The database files (`data/` directory) are not included in the repository due to size. Run the initial download to create your local database.