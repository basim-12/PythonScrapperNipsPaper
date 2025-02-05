import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup
import aiofiles
from urllib.parse import urljoin

# Constants
BASE_URL = "https://papers.nips.cc/"
TIMEOUT = 60  # Increased timeout to 60 seconds
MAX_RETRIES = 5  # Increased retries
MAX_CONCURRENT_YEARS = 4  # Limit to 4 concurrent years
CSV_FILE_PATH = "papers_metadata.csv"
REQUEST_DELAY = 1  # Delay between requests in seconds

# Semaphore for limiting concurrent years
years_semaphore = asyncio.Semaphore(MAX_CONCURRENT_YEARS)

# Initialize CSV file
async def initialize_csv():
    async with aiofiles.open(CSV_FILE_PATH, mode="w") as file:
        await file.write("Title,Year,Authors,PDF Link\n")
    print("Initialized CSV file with headers.")

# Extract year from URL
def extract_year_from_url(url):
    parts = url.split("/")
    for part in parts:
        if part.isdigit() and len(part) == 4:  # Check if it's a 4-digit year
            return part
    return None

# Scrape main page
async def scrape_main_page(session):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Scraping main page: {BASE_URL} (Attempt {attempt})")
            async with session.get(BASE_URL) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract year links
                    year_links = soup.select("body > div.container-fluid > div.col-sm > ul > li > a")
                    if not year_links:
                        print("No year links found.")
                        return

                    # Process each year concurrently with a limit of 4
                    tasks = []
                    for year_link in year_links:
                        year_url = year_link.get("href")
                        full_year_url = urljoin(BASE_URL, year_url)
                        year = extract_year_from_url(year_url)
                        if year:
                            print(f"Adding year to queue: {year}")
                            task = asyncio.create_task(process_year(session, full_year_url, year))
                            tasks.append(task)

                    # Wait for all tasks to complete
                    await asyncio.gather(*tasks)
                    return  # Exit retry loop if successful
                else:
                    print(f"Failed to fetch main page: {BASE_URL} (Status: {response.status})")
                    await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff
        except asyncio.TimeoutError:
            print(f"Timeout occurred while fetching main page: {BASE_URL} (Attempt {attempt})")
            if attempt == MAX_RETRIES:
                print(f"Max retries reached for: {BASE_URL}")
            await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff
        except Exception as e:
            print(f"Failed to scrape main page: {BASE_URL} (Attempt {attempt}) - {e}")
            if attempt == MAX_RETRIES:
                print(f"Max retries reached for: {BASE_URL}")
            await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff

# Process a single year
async def process_year(session, year_url, year):
    async with years_semaphore:  # Acquire semaphore for concurrent year processing
        print(f"Processing year: {year}")
        await scrape_yearly_page(session, year_url, year)
        print(f"Completed processing year: {year}")

# Scrape yearly page
async def scrape_yearly_page(session, year_url, year):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Scraping yearly page: {year_url} (Attempt {attempt})")
            async with session.get(year_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract paper links
                    paper_links = soup.select("a[href*='/paper/']")
                    if not paper_links:
                        print(f"No paper links found for: {year_url}")
                        return

                    # Create a folder for the year
                    if not os.path.exists(year):
                        os.makedirs(year)
                        print(f"Created folder for year: {year}")

                    # Process each paper sequentially
                    for paper_link in paper_links:
                        paper_url = paper_link.get("href")
                        full_paper_url = urljoin(BASE_URL, paper_url)
                        await scrape_paper_page(session, full_paper_url, year)
                    return  # Exit retry loop if successful
                else:
                    print(f"Failed to fetch yearly page: {year_url} (Status: {response.status})")
                    await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff
        except Exception as e:
            print(f"Failed to scrape yearly page: {year_url} (Attempt {attempt}) - {e}")
            if attempt == MAX_RETRIES:
                print(f"Max retries reached for: {year_url}")
            await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff

# Scrape paper page
async def scrape_paper_page(session, paper_url, year):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Scraping paper page: {paper_url} (Attempt {attempt})")
            async with session.get(paper_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract title
                    title = soup.select_one("h4").text.strip()

                    # Extract authors
                    authors = "N/A"
                    author_header = soup.select_one("h4:-soup-contains(Authors)")  # Updated selector
                    if author_header:
                        author_element = author_header.find_next_sibling()
                        if author_element:
                            authors = author_element.text.strip()

                    # Extract PDF link
                    pdf_link = soup.select_one("a:-soup-contains(Paper)")  # Updated selector
                    if not pdf_link:
                        print(f"No PDF link found for: {paper_url}")
                        return

                    pdf_url = pdf_link.get("href")
                    full_pdf_url = urljoin(BASE_URL, pdf_url)

                    # Download PDF
                    await download_pdf(session, full_pdf_url, year)

                    # Write metadata to CSV
                    await write_metadata_to_csv(title, year, authors, full_pdf_url)
                    return  # Exit retry loop if successful
                else:
                    print(f"Failed to fetch paper page: {paper_url} (Status: {response.status})")
                    await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff
        except Exception as e:
            print(f"Failed to scrape paper page: {paper_url} (Attempt {attempt}) - {e}")
            if attempt == MAX_RETRIES:
                print(f"Max retries reached for: {paper_url}")
            await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff

# Download PDF
async def download_pdf(session, pdf_url, year):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(pdf_url) as response:
                if response.status == 200:
                    file_name = pdf_url.split("/")[-1]
                    file_path = os.path.join(year, file_name)
                    async with aiofiles.open(file_path, mode="wb") as file:
                        await file.write(await response.read())
                    print(f"Downloaded PDF: {file_path}")
                    return  # Exit retry loop if successful
                else:
                    print(f"Failed to download PDF: {pdf_url} (Status: {response.status})")
                    await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff
        except Exception as e:
            print(f"Failed to download PDF: {pdf_url} (Attempt {attempt}) - {e}")
            if attempt == MAX_RETRIES:
                print(f"Max retries reached for: {pdf_url}")
            await asyncio.sleep(REQUEST_DELAY * attempt)  # Exponential backoff

# Write metadata to CSV
async def write_metadata_to_csv(title, year, authors, pdf_link):
    async with aiofiles.open(CSV_FILE_PATH, mode="a") as file:
        await file.write(f'"{title}",{year},"{authors}",{pdf_link}\n')
    print(f"Metadata written to CSV for: {title}")

# Main function
async def main():
    await initialize_csv()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        await scrape_main_page(session)

# Run the scraper
if __name__ == "__main__":
    asyncio.run(main())