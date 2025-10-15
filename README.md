# Historic England API Explorer

A comprehensive tool for exploring the National Heritage List for England (NHLE) API and scraping detailed building information from Historic England pages.

## Overview

This project provides two main capabilities:

1. **API Explorer** - Explore the NHLE API to understand available data and search capabilities
2. **Detailed Scraper** - Scrape comprehensive building details from Historic England listing pages

## Features

### API Explorer (`api_explorer.py`)
- Get API information and available data layers
- Count total listed buildings (379,604+ buildings)
- Search buildings by name, grade, or other criteria
- Get sample building data
- Explore different heritage types (buildings, monuments, parks, etc.)

### Detailed Scraper (`detailed_scraper.py`)
- Scrape detailed building information from Historic England pages
- Navigate through different tabs (Overview, Official List Entry, Comments/Photos)
- Extract architectural descriptions and historical details
- Get coordinates, grades, and official listing information
- Handle cookie consent and anti-bot protection

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd historic-england
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install ChromeDriver (for detailed scraping):
   - Download from https://chromedriver.chromium.org/
   - Place in your PATH or specify the path in the code

## Usage

### API Explorer
```bash
python api_explorer.py
```

This will:
- Show API information and available layers
- Count total listed buildings by grade
- Display sample buildings
- Search for specific building types

### Detailed Scraper
```bash
python detailed_scraper.py
```

This will:
- Get a random building from the API
- Scrape detailed information from all tabs
- Extract architectural descriptions
- Save results to `detailed_scraping_results.json`

## Data Available

### API Data
- **379,604+ listed buildings** across England
- **11 data layers** including:
  - Listed Building points/polygons
  - Scheduled Monuments
  - Parks and Gardens
  - Battlefields
  - Protected Wreck Sites
  - World Heritage Sites
- **Building grades**: I (exceptional), II* (important), II (special)
- **Coordinates**: British National Grid references
- **Direct links** to detailed Historic England pages

### Scraped Data
- **Complete architectural descriptions**
- **Historical information**
- **Construction details and materials**
- **Reasons for listing**
- **Images and media**
- **Location details**
- **Official listing text**

## Example Output

### API Explorer
```
🏛️  National Heritage List for England (NHLE) API Explorer
============================================================
📋 API Information:
Service Name: National Heritage List for England
Max Record Count: 1000
Supported Query Formats: JSON
Supported Export Formats: csv, shapefile, sqlite, geoPackage, filegdb, featureCollection, geojson, kml, excel

🗂️  Available Layers (11):
  0. ID: 0 - Listed Building points
  1. ID: 1 - Building Preservation Notice points
  2. ID: 2 - Certificate of Immunity points
  ...

✅ Total listed buildings: 379,604
  Grade I: 9,344 (2.5%)
  Grade II*: 22,106 (5.8%)
  Grade II: 348,154 (91.7%)
```

### Detailed Scraper
```
🏛️  Detailed Historic England Building Scraper
============================================================
🎲 Getting random building from API...
✅ Selected: 20 and 20A Whitbourne Springs

🏛️  Building: 20 and 20A Whitbourne Springs
   Grade: II, Entry: 1021466
   URL: https://historicengland.org.uk/listing/the-list/list-entry/1021466

✅ SUCCESS! Detailed scraping completed
   Tabs found: 2
   Tabs clicked: 2
   Tabs processed: 2

📋 Tab: Overview
   Headings: 17
   Paragraphs: 40
   Images: 9
   Links: 272

📋 Tab: Official List Entry
   Headings: 17
   Paragraphs: 40
   Images: 9
   Links: 273
   Specific data: ['grade', 'list_entry', 'coordinates', 'architectural_details']
   Architectural details: Pair of semi-detached cottages. Mid C17, Painted coursed rubble stone, tiled, pair of diagonally-set brick stacks...
```

## Technical Details

### API Endpoint
- **Base URL**: `https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer`
- **Format**: ArcGIS REST Service (JSON)
- **Max Records**: 1000 per query
- **Export Formats**: CSV, Shapefile, GeoJSON, KML, Excel

### Scraping Approach
- **Selenium WebDriver** with Chrome for bypassing anti-bot protection
- **Tab navigation** to access different content sections
- **Cookie consent handling** for compliance
- **Comprehensive content extraction** from all page elements

## Legal Considerations

- ✅ **robots.txt compliance** - Historic England allows scraping
- ✅ **Open Government Licence** - Data is freely available
- ✅ **Respectful scraping** - Built-in delays and proper headers
- ⚠️ **Rate limiting** - Be respectful of server resources
- ⚠️ **Terms of service** - Check Historic England's terms for commercial use

## Troubleshooting

### Common Issues
1. **ChromeDriver not found** - Install ChromeDriver and ensure it's in PATH
2. **403 Forbidden errors** - The scraper handles this automatically with Selenium
3. **No content extracted** - Check if the page structure has changed
4. **Timeout errors** - Increase wait times in the code

### Debugging
- Check the generated JSON files for detailed results
- Enable non-headless mode in Chrome options for visual debugging
- Check browser console for JavaScript errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Historic England for providing the NHLE API and data
- The Open Government Licence for making heritage data freely available
- The Python community for excellent libraries (requests, selenium, beautifulsoup4)