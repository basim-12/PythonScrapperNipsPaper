# NIPS Papers Scraper

This project is a web scraper designed to extract metadata and download PDFs of papers from the NeurIPS (Conference on Neural Information Processing Systems) website. The scraper is built using Python and leverages asynchronous programming with `aiohttp` and `asyncio` for efficient data retrieval.

## Features

- **Metadata Extraction**: Extracts paper titles, authors, and publication years.
- **PDF Download**: Downloads the PDFs of the papers.
- **CSV Export**: Saves the extracted metadata into a CSV file.
- **Concurrency**: Processes multiple years concurrently to speed up the scraping process.
- **Retry Mechanism**: Implements a retry mechanism with exponential backoff to handle failed requests.

## Requirements

- Python 3.7 or higher
- `aiohttp`
- `beautifulsoup4`
- `aiofiles`

## Configuration

You can modify the following constants in the scraper.py file to customize the scraper's behavior:

BASE_URL: The base URL of the NeurIPS papers website.
TIMEOUT: The timeout for HTTP requests.
MAX_RETRIES: The maximum number of retries for failed requests.
MAX_CONCURRENT_YEARS: The maximum number of years to process concurrently.
CSV_FILE_PATH: The path to the CSV file where metadata will be saved.
REQUEST_DELAY: The delay between requests to avoid overwhelming the server.

## Acknowledgments

Thanks to NeurIPS for making their papers publicly available.
This project uses aiohttp, beautifulsoup4, and aiofiles libraries.


published by baism-12
