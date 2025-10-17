# Historic England Database Scraper

This project provides tools to fetch Historic England data from the NHLE API and save it to a SQLite database.

## Scripts Overview

### 1. `sample_database_scraper.py` - Sample Data Fetcher
Fetches a small sample of Historic England buildings for testing and demonstration.

**Usage:**
```bash
# Fetch 100 buildings (default)
python sample_database_scraper.py

# Fetch 50 buildings to a specific database
python sample_database_scraper.py --count 50 --database my_sample.db

# Show statistics
python sample_database_scraper.py --stats --database my_sample.db
```

### 2. `database_scraper.py` - Full Data Fetcher
Fetches ALL available Historic England buildings (379,604+ records). Use with caution!

**Usage:**
```bash
# Full scrape with default settings
python database_scraper.py

# Custom batch size and database
python database_scraper.py --batch-size 500 --database full_historic_england.db

# Resume interrupted download
python database_scraper.py --resume

# Show statistics
python database_scraper.py --stats
```


## Database Schema

The database contains a `buildings` table with the following fields:

- `id` - Primary key
- `name` - Building name
- `grade` - Listing grade (I, II*, II)
- `list_entry` - Unique list entry number
- `list_date` - Date first listed
- `amend_date` - Date of last amendment
- `category` - Building category
- `ngr` - National Grid Reference
- `easting` - Easting coordinate
- `northing` - Northing coordinate
- `capture_scale` - Map capture scale
- `longitude` - Longitude (if available)
- `latitude` - Latitude (if available)
- `hyperlink` - URL to Historic England page
- `scraped_at` - When this record was scraped
- `created_at` - When this record was created

## Quick Start

1. **Install dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Test with sample data:**
   ```bash
   python sample_database_scraper.py --count 20
   python sample_database_scraper.py --stats --database sample_historic_england.db
   ```

3. **Run full scrape (if needed):**
   ```bash
   python database_scraper.py --batch-size 1000
   ```

## Performance Notes

- **Sample scraper**: Very fast, good for testing (seconds)
- **Full scraper**: Takes several hours for complete dataset
- **Batch size**: Larger batches are faster but use more memory
- **Resume**: Full scraper supports resuming interrupted downloads

## Data Statistics

The Historic England NHLE API contains:
- **Total buildings**: ~379,604 listed buildings
- **Grade distribution**: 
  - Grade II: ~85% (most common)
  - Grade II*: ~10%
  - Grade I: ~5% (most important)

## Examples

### Get a sample of buildings:
```bash
python sample_database_scraper.py --count 1000
python sample_database_scraper.py --stats --database sample_historic_england.db
```

### Monitor full scrape progress:
```bash
# In one terminal
python database_scraper.py --batch-size 1000

# In another terminal (check progress)
python database_scraper.py --stats --database historic_england.db
```

## Troubleshooting

- **API errors**: The API has rate limits, smaller batch sizes help
- **Database locked**: Make sure no other process is using the database
- **Memory issues**: Use smaller batch sizes
- **Interrupted downloads**: Use `--resume` flag to continue

## File Structure

```
historic-england/
├── sample_database_scraper.py    # Sample data fetcher
├── database_scraper.py           # Full data fetcher  
├── shared/
│   ├── api_client.py            # API client utilities
│   └── scraper.py               # Web scraping utilities
├── requirements.txt              # Python dependencies
└── *.db                         # SQLite database files
```
