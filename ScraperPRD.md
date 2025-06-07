Product Requirements Document: SBIR Award Data Scraper and Analyzer
Version: 1.0
Date: June 7, 2025
Author: Art Dietrich, DTRIQ LLC
Contact: art.dietrich@dtriq.com

1. Introduction

This document outlines the requirements for the "SBIR Award Data Scraper and Analyzer" project. The primary goal is to develop a Python-based tool to automatically collect Small Business Innovation Research (SBIR) and Small Business Technology Transfer (STTR) program award data from the official SBIR.gov API. This tool will initially focus on comprehensive data extraction and local storage, laying the groundwork for future advanced analysis, including the identification of Phase II progression, LLM-powered award categorization, and trend discovery to support the development of strong proposal ideas and abstracts. The project will be developed for local deployment and will eventually be hosted on a public GitHub repository.   

2. Goals

Automate Data Collection: To create a script that automatically fetches all available SBIR/STTR award data from the SBIR.gov API.
Provide Structured Data: To store the collected data in a clean, structured, and accessible format (initially CSV) for local use and analysis.
Enable Future Analysis: To build a foundational dataset and toolset that can be extended for more sophisticated analyses, such as:
Tracking award progression from Phase I to Phase II.   
Utilizing Large Language Models (LLMs) for categorizing awards and identifying research trends.   
Support Proposal Development: Ultimately, to leverage the collected data and analyses to help the user develop more competitive and informed grant proposal ideas and abstracts.
Open Source: To prepare the codebase for eventual hosting on a public GitHub repository, emphasizing clarity and good documentation.
3. Target User & Audience

Primary User: The individual initiating this project, who will run the scraper, use the collected data, and guide future analytical developments.
LLM Coding Assistant: An AI assistant that will use this PRD to generate the initial Python code for the scraper.
4. Project Scope

4.1. Phase 1: MVP (Minimum Viable Product - Current PRD Focus)
This phase focuses on creating the core data scraping and storage tool.

A Python script that connects to the SBIR.gov Award API.   
Functionality to retrieve all available SBIR/STTR award data.
Robust handling of API pagination to ensure complete data collection.   
Parsing of JSON responses from the API.   
Storage of retrieved data into a local CSV file.
Basic error handling for network issues and API errors.
Informative logging of script operations and errors.
Easily configurable parameters (e.g., API endpoint, output file name).
Well-commented and organized Python code suitable for a public GitHub repository.
4.2. Future Phases (Out of Scope for Initial LLM Coding Task)
These are potential future enhancements to build upon the MVP:

Vector Database Integration: Storing award abstracts and other key textual data in a vector database for semantic search and advanced querying.
Phase II Progression Analysis: Developing logic to identify Phase I awards and track their progression to Phase II.
LLM-Powered Categorization & Trend Analysis:
Implementing topic modeling (e.g., LDA ) or using LLMs to categorize awards based on their abstracts.   
Analyzing categorized data to identify research trends, funding patterns, and agency priorities.
AFWERX-Specific Filtering: Enhancing the script to specifically filter for AFWERX-managed awards by searching for relevant keywords (e.g., "AFWERX", "SpaceWERX", "STRATFI", "TACFI" ) within Air Force awards.   
Data Deduplication & Update Strategy: Implementing a strategy for periodic runs to update the dataset with new awards and avoid duplicates.
User Interface (Optional): Potentially developing a simple web interface (e.g., using Streamlit  or Dash ) for easier data exploration and visualization.   
Advanced Scheduling: Setting up automated periodic execution using tools like cron , Windows Task Scheduler , or GitHub Actions.   
5. Functional Requirements (FR)

FR1: API Endpoint Configuration
The script shall use https://api.www.sbir.gov/public/api/awards as the default base URL for fetching award data. This should be a configurable parameter.   
FR2: Comprehensive Data Retrieval
The script must be capable of fetching all publicly available SBIR/STTR awards through the API.
The script shall retrieve all fields returned by the Award API for each award (e.g., firm, award_title, agency, branch, phase, program, abstract, award_amount, proposal_award_date, etc. ).   
FR3: API Interaction Mechanics
FR3.1: Pagination: The script must correctly implement pagination using the start (offset) and rows (records per page) parameters as documented by the SBIR.gov API. The default rows per request is 100, but the API may allow more (e.g., up to 400 mentioned for awards , though other API endpoints have different limits ). The script should use a configurable rows value.   
FR3.2: Data Format: The script shall request and parse data in JSON format, which is the API's default.   
FR4: Local Data Storage
The script shall save all retrieved award data into a single CSV file on the local file system.
The name and path of the output CSV file shall be configurable.
The CSV file should include a header row with column names corresponding to the fields retrieved from the API.
FR5: Logging
The script shall implement logging to record its operational status.
Logged information should include:
Script start and end times.
Number of records fetched per API call/page.
Total number of records fetched.
Any errors encountered during API requests or data processing.
Path to the output file upon successful completion.
FR6: Configuration Management
Essential parameters such as the API base URL, output CSV file name, and rows per API request should be defined as easily modifiable variables or constants at the beginning of the script or in a separate configuration file.
FR7: Basic Error Handling
The script must gracefully handle common errors, including:
Network connection issues (e.g., timeouts).
HTTP error responses from the API (e.g., 4xx client errors, 5xx server errors).
Errors during JSON parsing.
In case of an error, the script should log the error details and, where appropriate, attempt a limited number of retries for transient issues or skip a problematic page and continue, rather than crashing.
6. Non-Functional Requirements (NFR)

NFR1: Code Quality & Maintainability:
The Python code must be well-structured, clean, and include clear comments and docstrings.
Code should follow PEP 8 Python style guidelines.
The project structure should be organized logically, suitable for a public GitHub repository.
NFR2: Modularity:
The script should be broken down into logical functions or classes to promote code reuse, readability, and testability.
NFR3: Reliability:
The scraper should be designed to run reliably for potentially long durations, especially when fetching a large historical dataset.
NFR4: API Politeness:
The script must include a configurable delay (e.g., 1-2 seconds) between consecutive API requests to avoid overwhelming the SBIR.gov server and ensure responsible API usage.
NFR5: Performance:
While not the primary focus for the MVP, the script should be reasonably efficient in terms of processing time and memory usage. Using pandas for data handling should aid this.
7. Technology Stack (MVP)

Language: Python 3.x
Libraries:
requests: For making HTTP calls to the SBIR.gov API.
pandas: For data manipulation (creating DataFrames) and exporting to CSV.
logging (standard Python module): For application logging.
time (standard Python module): For implementing delays between API calls.
8. Testing and Acceptance Criteria

The following test cases should be used to verify the functionality of the scraper:

Test Case 1: Successful API Connection and Initial Data Fetch
Description: Verify the script can connect to the SBIR.gov Award API and retrieve the first page of awards.
Acceptance Criteria:
Script executes without connection errors.
A list of award records is successfully retrieved and parsed.
Key fields such as firm, award_title, agency, and abstract are present in the fetched data.   
Log message indicates successful connection and data fetch.
Test Case 2: Pagination Logic
Description: Verify the script correctly handles API pagination to fetch multiple pages of results.
Acceptance Criteria:
If the total number of awards exceeds rows per request, the script makes multiple API calls.
The start parameter in API requests is correctly incremented for each subsequent page.
The script successfully aggregates data from all pages.
Log messages indicate fetching of multiple pages.
Test Case 3: Data Storage to CSV
Description: Verify the script correctly saves all fetched award data to a CSV file.
Acceptance Criteria:
A CSV file is created at the configured output path.
The CSV file contains a header row matching the API field names.
The number of data rows in the CSV (excluding header) matches the total number of awards logged as fetched.
Data integrity is maintained (e.g., special characters handled correctly, data appears in correct columns).
Test Case 4: API Error Handling
Description: Simulate an API error (e.g., by temporarily modifying the API URL to be invalid or by simulating a 500 server error if possible) and verify script behavior.
Acceptance Criteria:
The script does not crash.
An error message is logged detailing the API error.
The script either terminates gracefully or, if retry logic is implemented, attempts retries as configured.
Test Case 5: Logging Functionality
Description: Review the log output for completeness and clarity.
Acceptance Criteria:
Logs include script start/end times, total records fetched, records per page, output file location, and any errors.
Test Case 6: Configuration Parameter Usage
Description: Change configurable parameters (e.g., output CSV filename, rows per request) and verify the script uses the new values.
Acceptance Criteria:
The output file is created with the new name.
API requests reflect the changed rows parameter.
Test Case 7: Full Data Download (Spot Check for a Subset)
Description: Configure the script to download all awards for a smaller agency (e.g., "ED" - Department of Education ) or for a specific year to test end-to-end functionality without excessive runtime.   
Acceptance Criteria:
The script completes successfully.
The resulting CSV file contains a plausible number of records for the selected subset.
A spot check of the data shows diverse awards (different firms, titles, dates) as expected.
This PRD should provide a solid foundation for your LLM coding assistant to start developing the SBIR award scraper. Let me know if you'd like any adjustments or further details!

---

## IMPLEMENTATION STATUS UPDATE (June 7, 2025)

### ✅ Phase 1 MVP - COMPLETED

The SBIR Award Data Scraper has been successfully implemented and is production-ready:

**Core System Delivered:**
- **Database**: SQLite with 41-field schema storing ~213,000 SBIR/STTR awards
- **Initial Download**: `src/initial_download.py` - Complete data acquisition with resume capability
- **Update System**: `src/update_checker.py` - Automated periodic checking for new awards
- **Configuration**: Centralized config management in `config/config.py`
- **Error Handling**: Comprehensive logging, retry logic, and graceful failure recovery
- **Exports**: CSV generation and multiple output formats

**System Performance:**
- **Total Records**: 213,000 awards identified via API testing
- **Download Time**: 35-40 minutes for complete dataset
- **Storage Efficiency**: SQLite (355MB), CSV (405MB), Raw JSON (645MB)
- **Update Strategy**: Weekly checks for new awards with 30-day lookback

**Production Features:**
- **Resume Capability**: Interrupted downloads can be resumed
- **Progress Tracking**: Real-time progress reporting and ETAs
- **Data Validation**: Required field checking and data quality assurance
- **Rate Limiting**: Respectful API usage with configurable delays
- **Backup System**: Automatic database backups and recovery

**Repository Structure:**
```
sbir-scraper/
├── src/                    # Source code
├── config/                 # Configuration management
├── data/                   # Database storage (excluded from repo)
├── logs/                   # Application logs
├── docs/                   # API findings and analysis
├── README.md              # Public documentation
├── LICENSE                # DTRIQ LLC proprietary license
├── requirements.txt       # Python dependencies
└── .gitignore            # Repository exclusions
```

**Testing & Validation:**
- ✅ API connectivity and schema extraction
- ✅ Database creation and data integrity
- ✅ Error handling for network failures
- ✅ Large dataset processing (1000+ record batches)
- ✅ Update detection and deduplication

**Next Phase Readiness:**
The system is architected to support Phase 2 enhancements:
- Vector database integration for semantic search
- LLM-powered analysis and categorization
- Phase I → Phase II progression tracking
- Advanced filtering (AFWERX, agency-specific)
- Web interface development

The project has successfully met all Phase 1 MVP requirements and is ready for public GitHub release with DTRIQ LLC licensing.
