# Historic England Complete Scraper

A comprehensive scraper for the Historic England National Heritage List for England (NHLE).

Combines both **API data** and **web scraping** to extract the most complete dataset possible.

## Features

- ✅ **API Data**: Fast, structured data from NHLE ArcGIS API
- ✅ **Web Scraping**: Detailed architectural descriptions and metadata
- ✅ **Complete Coverage**: All available data about listed buildings
- ✅ **Production Ready**: Handles cookies, timeouts, errors gracefully
- ✅ **Clean Output**: Structured JSON format

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Requirements
- Python 3.7+
- `playwright==1.48.0` - Web scraping framework
- `requests==2.31.0` - HTTP library for API calls

## Usage

### Command Line

```bash
# Scrape a single building
python3 complete_scraper.py 1380908

# Output: complete_1380908.json
```

### As a Module

```python
from complete_scraper import scrape_complete

# Scrape a building
result = await scrape_complete('1380908', headless=True)

print(result['api_data']['name'])
print(result['web_data']['description'])
```

## Data Structure

```json
{
  "list_entry_number": "1380908",
  "scraped_at": "2025-10-16T17:08:19.446100",
  "urls": {
    "official_list_entry": "https://...",
    "comments_and_photos": "https://..."
  },
  "api_data": { ... },
  "web_data": {
    "major_amendment_date": "05-Nov-1987",
    "minor_amendment_date": "17 April 2024",
    ...
  },
  "success": true
}
```

## What's Included

### API Data
- Building name, grade, list date
- National Grid Reference (NGR)
- Easting/Northing coordinates
- Direct hyperlink

### Web Data
- Full title and address
- **Complete architectural description** (1000+ characters)
- **Major amendment date** (from "Date of most recent amendment" field)
- **Minor amendment date** (from description text when entry was recently updated)
- District, Parish, Grid Reference
- Legacy system information
- Legal information
- Downloadable map PDF URL

## Performance

- **Speed**: ~3-4 seconds per building
- **Success Rate**: Very high (>99%)
- **Headless**: Runs without visible browser

## Limitations

- **Comments & Photos**: Not included due to Cloudflare protection
- **Rate Limiting**: Add 2+ second delays between requests
- **Official Entries Only**: Scrapes official list entry page

## License

For educational and research purposes. Please respect Historic England's terms of service.
